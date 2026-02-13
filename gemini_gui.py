#!/usr/bin/env python3
import sys, os, json
from datetime import datetime
from google import genai
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QListWidget, QListWidgetItem, QPushButton, QFrame, QLabel)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QColor

# --- CONFIGURAÇÃO DE ESTILO (Catppuccin Mocha) ---
C_ACCENT, C_BG_SIDE, C_BG_MAIN = "#cba6f7", "#11111b", "#1e1e2e"
C_BG_INPUT, C_BUBBLE_USER = "#313244", "#45475a"
C_TEXT, C_RED, C_GREEN = "#cdd6f4", "#f38ba8", "#a6e3a1"

# Carregamento da API via variável de ambiente para segurança no GitHub
API_KEY = os.getenv("GEMINI_API_KEY", "SUA_CHAVE_AQUI")
CHATS_DIR = os.path.expanduser("~/.gemini_chats")
os.makedirs(CHATS_DIR, exist_ok=True)
client = genai.Client(api_key=API_KEY)

class GeminiWorker(QThread):
    finished = pyqtSignal(str)
    def __init__(self, history):
        super().__init__()
        self.history = history
    def run(self):
        try:
            res = client.models.generate_content(model="gemini-2.0-flash", contents=self.history)
            self.finished.emit(res.text)
        except Exception as e: self.finished.emit(f"Erro na API: {str(e)}")

class ChatItemWidget(QWidget):
    delete_requested = pyqtSignal(str)
    def __init__(self, chat_id):
        super().__init__()
        self.chat_id = chat_id
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 5, 2)
        
        name = chat_id[:18] + ".." if len(chat_id) > 18 else chat_id
        self.label = QLabel(name)
        self.label.setStyleSheet("color: #cdd6f4; border: none; font-size: 13px;")
        
        self.btn_del = QPushButton("✕")
        self.btn_del.setFixedSize(22, 22)
        self.btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self.chat_id))
        self.btn_del.setStyleSheet(f"QPushButton {{ background: transparent; color: {C_RED}; border-radius: 11px; }} QPushButton:hover {{ background: rgba(243, 139, 168, 0.2); }}")
        
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.btn_del)

class GeminiWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.all_chats = {}
        self.current_chat_id = None
        self.is_interrupted = False
        self.initUI()
        self.load_chats_from_disk()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1000, 720)

        self.main_container = QFrame(self)
        self.main_container.setObjectName("Main")
        self.main_container.setStyleSheet(f"QFrame#Main {{ background: {C_BG_MAIN}; border-radius: 28px; border: 1px solid rgba(255,255,255,0.1); }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.main_container)
        
        hbar = QHBoxLayout(self.main_container)
        hbar.setSpacing(0)
        hbar.setContentsMargins(0,0,0,0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet(f"background: {C_BG_SIDE}; border-top-left-radius: 28px; border-bottom-left-radius: 28px;")
        side_lay = QVBoxLayout(self.sidebar)
        
        btn_new = QPushButton("+ Novo Chat")
        btn_new.setFixedHeight(45)
        btn_new.clicked.connect(self.new_chat)
        btn_new.setStyleSheet(f"background: {C_ACCENT}; color: {C_BG_SIDE}; font-weight: bold; border-radius: 14px;")
        
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("QListWidget { background: transparent; border: none; outline: none; } QListWidget::item { background: transparent; }")
        self.chat_list.itemClicked.connect(self.on_item_clicked)
        
        side_lay.addWidget(QLabel("HISTÓRICO", styleSheet="color:#585b70; font-weight:800; font-size:10px; margin: 10px;"))
        side_lay.addWidget(btn_new)
        side_lay.addWidget(self.chat_list)

        # Content
        self.content = QFrame()
        cont_lay = QVBoxLayout(self.content)

        header = QHBoxLayout()
        header.addStretch()
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet(f"QPushButton {{ background: {C_BG_INPUT}; color: white; border-radius: 15px; border: none; }} QPushButton:hover {{ background: {C_RED}; }}")
        header.addWidget(btn_close)
        header.setContentsMargins(0, 10, 15, 0)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background: transparent; border: none; color: white; padding: 20px; font-size: 14px;")
        self.chat_display.verticalScrollBar().setStyleSheet("QScrollBar { width: 0px; }")

        self.status_lbl = QLabel(" ● Gemini pensando...")
        self.status_lbl.setStyleSheet(f"color: {C_ACCENT}; font-weight: bold; margin-left: 25px;")
        self.status_lbl.hide()

        input_row = QHBoxLayout()
        input_row.setContentsMargins(20, 0, 20, 20)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Escreva para o Gemini...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setStyleSheet(f"background: {C_BG_INPUT}; color: white; border-radius: 18px; padding: 15px; border: none;")
        
        self.btn_stop = QPushButton("■")
        self.btn_stop.setFixedSize(48, 48)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_generation)
        self.btn_stop.setStyleSheet(f"QPushButton {{ background: {C_BG_INPUT}; color: {C_RED}; border-radius: 24px; border: none; }}")

        input_row.addWidget(self.input_field)
        input_row.addWidget(self.btn_stop)

        cont_lay.addLayout(header)
        cont_lay.addWidget(self.chat_display)
        cont_lay.addWidget(self.status_lbl)
        cont_lay.addLayout(input_row)

        hbar.addWidget(self.sidebar)
        hbar.addWidget(self.content)

        self.type_timer = QTimer()
        self.type_timer.timeout.connect(self.update_typing_effect)

    def stop_generation(self):
        if hasattr(self, 'worker') and self.worker.isRunning(): self.worker.terminate()
        self.status_lbl.hide()
        self.is_interrupted = True
        self.input_field.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def send_message(self):
        txt = self.input_field.text().strip()
        if not txt or not self.current_chat_id: return
        self.is_interrupted = False
        self.chat_display.append(f"<div style='background:{C_BUBBLE_USER}; padding:12px; border-radius:14px; margin-bottom:10px;'><b>VOCÊ:</b><br>{txt}</div>")
        self.all_chats[self.current_chat_id].append({'role': 'user', 'parts': [{'text': txt}]})
        self.input_field.clear(); self.input_field.setEnabled(False)
        self.btn_stop.setEnabled(True); self.status_lbl.show()
        self.worker = GeminiWorker(self.all_chats[self.current_chat_id])
        self.worker.finished.connect(self.on_gemini_finished)
        self.worker.start()

    def on_gemini_finished(self, text):
        self.status_lbl.hide()
        if not self.is_interrupted:
            self.full_response, self.typing_index = text, 0
            self.chat_display.append(f"<b style='color:{C_GREEN};'>GEMINI:</b><br>")
            self.type_timer.start(3)

    def update_typing_effect(self):
        if self.typing_index < len(self.full_response):
            cursor = self.chat_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.chat_display.setTextCursor(cursor)
            self.chat_display.insertPlainText(self.full_response[self.typing_index])
            self.typing_index += 1
            self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
        else:
            self.type_timer.stop()
            self.all_chats[self.current_chat_id].append({'role': 'model', 'parts': [{'text': self.full_response}]})
            self.save_chat()
            self.input_field.setEnabled(True); self.btn_stop.setEnabled(False)
            if len(self.all_chats[self.current_chat_id]) == 2: self.auto_rename()

    def auto_rename(self):
        try:
            txt = self.all_chats[self.current_chat_id][0]['parts'][0]['text']
            res = client.models.generate_content(model="gemini-2.0-flash", contents=f"Resuma em 2 palavras: {txt}")
            new_name = res.text.strip().replace('"', '')[:20]
            old_id = self.current_chat_id
            self.all_chats[new_name] = self.all_chats.pop(old_id)
            if os.path.exists(os.path.join(CHATS_DIR, f"{old_id}.json")): os.remove(os.path.join(CHATS_DIR, f"{old_id}.json"))
            self.current_chat_id = new_name
            self.save_chat(); self.load_chats_from_disk()
        except: pass

    def delete_chat(self, cid):
        path = os.path.join(CHATS_DIR, f"{cid}.json")
        if os.path.exists(path): os.remove(path)
        if cid in self.all_chats: del self.all_chats[cid]
        self.load_chats_from_disk()
        if self.current_chat_id == cid: self.chat_display.clear(); self.current_chat_id = None

    def load_chats_from_disk(self):
        self.chat_list.clear()
        files = sorted([f for f in os.listdir(CHATS_DIR) if f.endswith(".json")], key=lambda x: os.path.getmtime(os.path.join(CHATS_DIR, x)), reverse=True)
        for f in files:
            cid = f.replace(".json", "")
            with open(os.path.join(CHATS_DIR, f), "r") as file: self.all_chats[cid] = json.load(file)
            item = QListWidgetItem(self.chat_list)
            item.setSizeHint(QSize(0, 42))
            widget = ChatItemWidget(cid)
            widget.delete_requested.connect(self.delete_chat)
            self.chat_list.addItem(item)
            self.chat_list.setItemWidget(item, widget)
        if files and not self.current_chat_id: self.current_chat_id = files[0].replace(".json", "")

    def on_item_clicked(self, item):
        widget = self.chat_list.itemWidget(item)
        self.current_chat_id = widget.chat_id
        self.chat_display.clear()
        for msg in self.all_chats.get(self.current_chat_id, []):
            role = "VOCÊ" if msg['role'] == 'user' else "GEMINI"
            self.chat_display.append(f"<b>{role}:</b><br>{msg['parts'][0]['text']}<br>")

    def new_chat(self):
        cid = f"Chat {datetime.now().strftime('%H%M%S')}"
        self.all_chats[cid] = []; self.current_chat_id = cid
        self.save_chat(); self.load_chats_from_disk()

    def save_chat(self):
        if self.current_chat_id:
            with open(os.path.join(CHATS_DIR, f"{self.current_chat_id}.json"), "w") as f: json.dump(self.all_chats[self.current_chat_id], f)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self.drag_pos = e.globalPosition().toPoint()
    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + e.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = e.globalPosition().toPoint()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = GeminiWindow()
    win.show()
    sys.exit(app.exec())
