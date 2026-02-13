#!/usr/bin/env python3
import sys, os, json
from datetime import datetime
from google import genai
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QListWidget, QListWidgetItem, QPushButton, 
                             QFrame, QLabel, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QColor, QFont

# --- TEMA CATPPUCCIN MOCHA ---
C_ACCENT, C_BG_SIDE, C_BG_MAIN = "#cba6f7", "#11111b", "#1e1e2e"
C_BG_INPUT, C_BUBBLE_USER = "#313244", "#45475a"
C_TEXT, C_RED, C_GREEN = "#cdd6f4", "#f38ba8", "#a6e3a1"

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".gemini_nebula_config.json")
CHATS_DIR = os.path.expanduser("~/.gemini_chats")
os.makedirs(CHATS_DIR, exist_ok=True)

# --- GERENCIAMENTO DE CONFIGURAÇÃO ---
def save_config(api_key, model):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"api_key": api_key, "model": model}, f)

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f: return json.load(f)
        except: return None
    return None

# --- TELA DE SETUP (ARREDONDADA E MODERNA) ---
class SetupWindow(QWidget):
    config_ready = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 350)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        container = QFrame()
        container.setStyleSheet(f"background: {C_BG_MAIN}; border-radius: 25px; border: 1px solid {C_ACCENT};")
        layout.addWidget(container)

        inner_lay = QVBoxLayout(container)
        inner_lay.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Nebula Gemini Setup")
        title.setStyleSheet(f"color: {C_ACCENT}; font-size: 20px; font-weight: bold; border: none;")
        inner_lay.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        inner_lay.addSpacing(20)
        
        inner_lay.addWidget(QLabel("Google API Key:", styleSheet="color: white; border: none;"))
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Cole sua chave aqui...")
        self.api_input.setStyleSheet(f"background: {C_BG_INPUT}; color: white; padding: 12px; border-radius: 10px; border: none;")
        inner_lay.addWidget(self.api_input)

        inner_lay.addSpacing(15)

        inner_lay.addWidget(QLabel("Modelo Padrão:", styleSheet="color: white; border: none;"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"])
        self.model_combo.setStyleSheet(f"background: {C_BG_INPUT}; color: white; padding: 10px; border-radius: 10px; border: none;")
        inner_lay.addWidget(self.model_combo)

        inner_lay.addSpacing(30)

        btn_save = QPushButton("Salvar e Iniciar")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.finish_setup)
        btn_save.setStyleSheet(f"background: {C_ACCENT}; color: {C_BG_SIDE}; font-weight: bold; padding: 15px; border-radius: 12px; border: none;")
        inner_lay.addWidget(btn_save)

    def finish_setup(self):
        key = self.api_input.text().strip()
        model = self.model_combo.currentText()
        if key:
            save_config(key, model)
            self.config_ready.emit(key, model)
            self.close()

# --- WORKER ASSÍNCRONO ---
class GeminiWorker(QThread):
    finished = pyqtSignal(str)
    def __init__(self, client, model, history):
        super().__init__()
        self.client, self.model, self.history = client, model, history
    def run(self):
        try:
            res = self.client.models.generate_content(model=self.model, contents=self.history)
            self.finished.emit(res.text)
        except Exception as e: self.finished.emit(f"Erro: {str(e)}")

# --- WIDGET DA LISTA DE CHATS ---
class ChatItemWidget(QWidget):
    delete_requested = pyqtSignal(str)
    def __init__(self, chat_id):
        super().__init__()
        self.chat_id = chat_id
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 5, 5, 5)
        lbl = QLabel(chat_id[:15] + ".." if len(chat_id) > 15 else chat_id)
        lbl.setStyleSheet("color: white; border: none;")
        btn = QPushButton("✕")
        btn.setFixedSize(22, 22)
        btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {C_RED}; border-radius: 11px; }} QPushButton:hover {{ background: rgba(243,139,168,0.2); }}")
        btn.clicked.connect(lambda: self.delete_requested.emit(self.chat_id))
        lay.addWidget(lbl)
        lay.addStretch()
        lay.addWidget(btn)

# --- JANELA PRINCIPAL ---
class GeminiWindow(QWidget):
    def __init__(self, api_key, model):
        super().__init__()
        self.api_key, self.model_name = api_key, model
        self.client = genai.Client(api_key=self.api_key)
        self.all_chats, self.current_chat_id = {}, None
        self.initUI()
        self.load_chats_from_disk()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1100, 750)

        main_frame = QFrame(self)
        main_frame.setObjectName("Main")
        main_frame.setStyleSheet(f"QFrame#Main {{ background: {C_BG_MAIN}; border-radius: 30px; border: 1px solid rgba(255,255,255,0.1); }}")
        
        win_lay = QVBoxLayout(self)
        win_lay.setContentsMargins(0,0,0,0)
        win_lay.addWidget(main_frame)

        hbar = QHBoxLayout(main_frame)
        hbar.setContentsMargins(0,0,0,0)
        hbar.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet(f"background: {C_BG_SIDE}; border-top-left-radius: 30px; border-bottom-left-radius: 30px;")
        side_lay = QVBoxLayout(sidebar)
        
        btn_new = QPushButton("+ Novo Chat")
        btn_new.setFixedHeight(45)
        btn_new.clicked.connect(self.new_chat)
        btn_new.setStyleSheet(f"background: {C_ACCENT}; color: {C_BG_SIDE}; font-weight: bold; border-radius: 15px; margin: 10px;")
        
        self.list_w = QListWidget()
        self.list_w.setStyleSheet("QListWidget { background: transparent; border: none; outline: none; }")
        self.list_w.itemClicked.connect(self.switch_chat)
        
        side_lay.addWidget(btn_new)
        side_lay.addWidget(self.list_w)
        hbar.addWidget(sidebar)

        # Content
        content = QFrame()
        cont_lay = QVBoxLayout(content)
        
        header = QHBoxLayout()
        header.addStretch()
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet(f"QPushButton {{ background: {C_BG_INPUT}; color: white; border-radius: 15px; }} QPushButton:hover {{ background: {C_RED}; }}")
        header.addWidget(btn_close)
        
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("background: transparent; border: none; color: white; padding: 20px;")
        
        self.status = QLabel("● Gemini processando...")
        self.status.setStyleSheet(f"color: {C_ACCENT}; font-weight: bold; margin-left: 20px;")
        self.status.hide()

        input_lay = QHBoxLayout()
        self.input_f = QLineEdit()
        self.input_f.setPlaceholderText("Escreva algo...")
        self.input_f.returnPressed.connect(self.send_msg)
        self.input_f.setStyleSheet(f"background: {C_BG_INPUT}; color: white; border-radius: 20px; padding: 15px; border: none;")
        
        self.btn_stop = QPushButton("■")
        self.btn_stop.setFixedSize(50, 50)
        self.btn_stop.setStyleSheet(f"background: {C_BG_INPUT}; color: {C_RED}; border-radius: 25px;")
        
        input_lay.addWidget(self.input_f)
        input_lay.addWidget(self.btn_stop)
        input_lay.setContentsMargins(20, 0, 20, 20)

        cont_lay.addLayout(header)
        cont_lay.addWidget(self.chat_area)
        cont_lay.addWidget(self.status)
        cont_lay.addLayout(input_lay)
        hbar.addWidget(content)

    def send_msg(self):
        txt = self.input_f.text().strip()
        if not txt or not self.current_chat_id: return
        self.chat_area.append(f"<div style='background:{C_BUBBLE_USER}; padding:10px; border-radius:10px;'><b>VOCÊ:</b><br>{txt}</div>")
        self.all_chats[self.current_chat_id].append({'role': 'user', 'parts': [{'text': txt}]})
        self.input_f.clear()
        self.status.show()
        self.worker = GeminiWorker(self.client, self.model_name, self.all_chats[self.current_chat_id])
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, text):
        self.status.hide()
        self.chat_area.append(f"<b style='color:{C_GREEN};'>GEMINI:</b><br>{text}<br>")
        self.all_chats[self.current_chat_id].append({'role': 'model', 'parts': [{'text': text}]})
        self.save_chat()
        if len(self.all_chats[self.current_chat_id]) == 2: self.auto_name(self.all_chats[self.current_chat_id][0]['parts'][0]['text'])

    def auto_name(self, first_msg):
        try:
            res = self.client.models.generate_content(model=self.model_name, contents=f"Resuma em 2 palavras: {first_msg}")
            new_name = res.text.strip().replace('"', '')[:20]
            old_id = self.current_chat_id
            self.all_chats[new_name] = self.all_chats.pop(old_id)
            os.remove(os.path.join(CHATS_DIR, f"{old_id}.json"))
            self.current_chat_id = new_name
            self.save_chat()
            self.load_chats_from_disk()
        except: pass

    def load_chats_from_disk(self):
        self.list_w.clear()
        files = sorted([f for f in os.listdir(CHATS_DIR) if f.endswith(".json")], key=lambda x: os.path.getmtime(os.path.join(CHATS_DIR, x)), reverse=True)
        for f in files:
            cid = f.replace(".json", "")
            with open(os.path.join(CHATS_DIR, f), "r") as file: self.all_chats[cid] = json.load(file)
            item = QListWidgetItem(self.list_w)
            item.setSizeHint(QSize(0, 45))
            widget = ChatItemWidget(cid)
            widget.delete_requested.connect(self.del_chat)
            self.list_w.setItemWidget(item, widget)
        if files and not self.current_chat_id: self.current_chat_id = files[0].replace(".json", "")

    def del_chat(self, cid):
        path = os.path.join(CHATS_DIR, f"{cid}.json")
        if os.path.exists(path): os.remove(path)
        if cid in self.all_chats: del self.all_chats[cid]
        self.current_chat_id = None
        self.load_chats_from_disk()
        self.chat_area.clear()

    def new_chat(self):
        cid = f"Sessão {datetime.now().strftime('%H%M%S')}"
        self.all_chats[cid] = []
        self.current_chat_id = cid
        self.save_chat(); self.load_chats_from_disk()

    def save_chat(self):
        if self.current_chat_id:
            with open(os.path.join(CHATS_DIR, f"{self.current_chat_id}.json"), "w") as f: json.dump(self.all_chats[self.current_chat_id], f)

    def switch_chat(self, item):
        widget = self.list_w.itemWidget(item)
        self.current_chat_id = widget.chat_id
        self.chat_area.clear()
        for msg in self.all_chats[self.current_chat_id]:
            role = "VOCÊ" if msg['role'] == 'user' else "GEMINI"
            self.chat_area.append(f"<b>{role}:</b><br>{msg['parts'][0]['text']}<br>")

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self.drag_pos = e.globalPosition().toPoint()
    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + e.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = e.globalPosition().toPoint()

# --- EXECUÇÃO ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    config = load_config()

    def start_app(key, model):
        global win
        win = GeminiWindow(key, model)
        win.show()

    if not config:
        setup = SetupWindow()
        setup.config_ready.connect(start_app)
        setup.show()
    else:
        start_app(config['api_key'], config['model'])
    
    sys.exit(app.exec())
