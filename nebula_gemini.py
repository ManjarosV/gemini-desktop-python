#!/usr/bin/env python3
"""
NebulaAI Desktop â€” v3.0
Catppuccin Mocha â€¢ PyQt6 â€¢ Google Gemini + OpenRouter
"""
import sys, os, json, re, requests
from datetime import datetime
from google import genai
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QFrame, QLabel, QComboBox, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize,
    QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import QFont, QTextCursor

# â”€â”€ Catppuccin Mocha â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
C_ACCENT   = "#cba6f7"
C_ACCENT2  = "#89b4fa"
C_BG_SIDE  = "#11111b"
C_BG_MAIN  = "#1e1e2e"
C_BG_SURF  = "#181825"
C_BG_INPUT = "#313244"
C_BUBBLE_U = "#45475a"
C_TEXT     = "#cdd6f4"
C_SUBTEXT  = "#6c7086"
C_RED      = "#f38ba8"
C_GREEN    = "#a6e3a1"
C_YELLOW   = "#f9e2af"
C_TEAL     = "#94e2d5"

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".gemini_nebula_config.json")
CHATS_DIR   = os.path.expanduser("~/.gemini_chats")
os.makedirs(CHATS_DIR, exist_ok=True)

PROVIDERS = ["OpenRouter", "Google Gemini"]

GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

OPENROUTER_MODELS = [
    "openrouter/qwen/qwen3.6-plus:free",
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "deepseek/deepseek-chat",
    "anthropic/claude-3.5-haiku",
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
]

OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"

# â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def save_config(data: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f)

def load_config() -> dict | None:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None

# â”€â”€ Markdown-lite â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def render_markdown(text: str) -> str:
    text = re.sub(
        r'```(?:\w+)?\n?(.*?)```',
        lambda m: (
            f'<pre style="background:#181825;color:{C_TEAL};padding:10px;'
            f'border-radius:8px;font-family:monospace;white-space:pre-wrap;">'
            f'{m.group(1).strip()}</pre>'
        ),
        text, flags=re.DOTALL
    )
    text = re.sub(
        r'`([^`]+)`',
        rf'<code style="background:#181825;color:{C_TEAL};padding:2px 5px;'
        rf'border-radius:4px;font-family:monospace;">\1</code>',
        text
    )
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = text.replace('\n', '<br>')
    return text

# â”€â”€ Worker â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class GeminiWorker(QThread):
    finished = pyqtSignal(str)
    errored  = pyqtSignal(str)

    def __init__(self, config: dict, history: list):
        super().__init__()
        self._config  = config
        self._history = history
        self._abort   = False

    def abort(self):
        self._abort = True
        self.terminate()

    def run(self):
        provider = self._config.get("provider", "Google Gemini")
        try:
            if provider == "Google Gemini":
                self._run_gemini()
            else:
                self._run_openrouter()
        except Exception as e:
            if not self._abort:
                self.errored.emit(str(e))

    def _run_gemini(self):
        client = genai.Client(api_key=self._config["api_key"])
        res = client.models.generate_content(
            model=self._config["model"],
            contents=self._history
        )
        if not self._abort:
            self.finished.emit(res.text)

    def _run_openrouter(self):
        messages = []
        for msg in self._history:
            role    = "user" if msg["role"] == "user" else "assistant"
            content = msg["parts"][0]["text"] if msg.get("parts") else ""
            messages.append({"role": role, "content": content})

        headers = {
            "Authorization": f"Bearer {self._config['api_key']}",
            "Content-Type":  "application/json",
            "HTTP-Referer":  "https://nebulaai.app",
            "X-Title":       "NebulaAI",
        }
        
        payload = {
            "model": self._config["model"],
            "messages": messages,
            "temperature": 0.7,
        }
        
        try:
            resp = requests.post(
                OPENROUTER_BASE,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            # Log para debug
            print(f"OpenRouter status: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
            
            if resp.status_code == 401:
                raise Exception("API Key invÃ¡lida ou expirada. Verifique em openrouter.ai/keys")
            elif resp.status_code == 402:
                raise Exception("CrÃ©ditos insuficientes. Adicione crÃ©ditos em openrouter.ai/credits")
            elif resp.status_code == 429:
                raise Exception("Rate limit atingido. Aguarde alguns segundos e tente novamente.")
            elif resp.status_code != 200:
                try:
                    error_data = resp.json()
                    error_msg = error_data.get("error", {}).get("message", resp.text)
                    raise Exception(f"Erro {resp.status_code}: {error_msg}")
                except:
                    raise Exception(f"Erro HTTP {resp.status_code}: {resp.text[:200]}")
            
            data = resp.json()
            
            if "error" in data:
                raise Exception(f"OpenRouter error: {data['error'].get('message', 'Unknown error')}")
            
            if "choices" not in data or not data["choices"]:
                raise Exception("Resposta vazia da API. Tente outro modelo.")
            
            text = data["choices"][0]["message"]["content"]
            if not self._abort:
                self.finished.emit(text)
                
        except requests.exceptions.Timeout:
            raise Exception("Timeout: OpenRouter demorou demais para responder. Tente novamente.")
        except requests.exceptions.ConnectionError:
            raise Exception("Erro de conexÃ£o: Verifique sua internet.")
        except Exception as e:
            if "API Key" in str(e) or "Erro" in str(e):
                raise
            raise Exception(f"Erro na requisiÃ§Ã£o: {str(e)}")

# â”€â”€ Pulsing dots â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class ThinkingDots(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dots = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setStyleSheet(
            f"color:{C_ACCENT}; font-weight:bold; font-size:13px; margin-left:22px;"
        )
        self.hide()

    def start(self):
        self._dots = 0
        self._timer.start(400)
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _tick(self):
        self._dots = (self._dots + 1) % 4
        self.setText("â— Pensando" + "." * self._dots)

# â”€â”€ Sidebar chat item â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class ChatItemWidget(QWidget):
    delete_requested = pyqtSignal(str)
    selected         = pyqtSignal(str)

    def __init__(self, chat_id: str, active: bool = False):
        super().__init__()
        self.chat_id = chat_id
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 6, 6)

        name = chat_id[:17] + "â€¦" if len(chat_id) > 17 else chat_id
        self.lbl = QLabel(name)
        self.lbl.setStyleSheet(
            f"color:{'white' if active else C_TEXT}; border:none; font-size:13px;"
        )
        btn_del = QPushButton("âœ•")
        btn_del.setFixedSize(22, 22)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{C_RED}; border-radius:11px; border:none; }}"
            f"QPushButton:hover {{ background:rgba(243,139,168,0.2); }}"
        )
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self.chat_id))
        lay.addWidget(self.lbl)
        lay.addStretch()
        lay.addWidget(btn_del)

        bg = "rgba(203,166,247,0.12)" if active else "transparent"
        self.setStyleSheet(f"ChatItemWidget {{ background:{bg}; border-radius:10px; }}")

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.chat_id)

# â”€â”€ Settings Overlay â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class SettingsOverlay(QWidget):
    """Overlay de configuraÃ§Ãµes que abre dentro da janela principal"""
    config_saved = pyqtSignal(dict)

    def __init__(self, parent, current: dict | None = None):
        super().__init__(parent)
        self._current = current or {}
        self._drag_pos = None
        self.setFixedSize(parent.size())
        # Translucent
        self.hide()
        self._build_ui()
        self._fade_in()

    def _fade_in(self):
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(350)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _combo_style(self):
        return (
            f"QComboBox {{ background:{C_BG_INPUT}; color:white; padding:10px 16px;"
            f" border-radius:12px; border:none; font-size:13px; }}"
            f"QComboBox::drop-down {{ border:none; }}"
            f"QComboBox QAbstractItemView {{ background:{C_BG_SURF}; color:white;"
            f" selection-background-color:{C_ACCENT}; selection-color:{C_BG_SIDE}; }}"
        )

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background:{C_BG_MAIN}; border-radius:26px; border:1px solid {C_ACCENT}; }}"
        )
        root.addWidget(card)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(36, 32, 36, 36)
        lay.setSpacing(13)

        title = QLabel("âœ¦  NebulaAI")
        title.setStyleSheet(f"color:{C_ACCENT}; font-size:22px; font-weight:800; border:none;")
        sub = QLabel("Configure o provedor e a API Key")
        sub.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px; border:none;")
        lay.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub,   alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addSpacing(4)

        lay.addWidget(QLabel("Provedor", styleSheet=f"color:{C_TEXT}; border:none; font-size:13px;"))
        self.provider_cb = QComboBox()
        self.provider_cb.addItems(PROVIDERS)
        self.provider_cb.setCurrentText(self._current.get("provider", "Google Gemini"))
        self.provider_cb.currentTextChanged.connect(self._on_provider_changed)
        self.provider_cb.setStyleSheet(self._combo_style())
        lay.addWidget(self.provider_cb)

        lay.addWidget(QLabel("API Key", styleSheet=f"color:{C_TEXT}; border:none; font-size:13px;"))
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_input.setText(self._current.get("api_key", ""))
        self.api_input.setStyleSheet(
            f"QLineEdit {{ background:{C_BG_INPUT}; color:white; padding:12px 16px;"
            f" border-radius:12px; border:1px solid transparent; font-size:13px; }}"
            f"QLineEdit:focus {{ border:1px solid {C_ACCENT}; }}"
        )
        lay.addWidget(self.api_input)

        self.hint_lbl = QLabel()
        self.hint_lbl.setOpenExternalLinks(True)
        self.hint_lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px; border:none;")
        lay.addWidget(self.hint_lbl)

        self.test_btn = QPushButton("ðŸ” Testar ConexÃ£o")
        self.test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_btn.setFixedHeight(38)
        self.test_btn.clicked.connect(self._test_connection)
        self.test_btn.setStyleSheet(
            f"QPushButton {{ background:{C_TEAL}; color:{C_BG_SIDE}; font-weight:700;"
            f" font-size:12px; border-radius:10px; border:none; }}"
            f"QPushButton:hover {{ background:#7dd3c0; }}"
            f"QPushButton:disabled {{ background:{C_BG_INPUT}; color:{C_SUBTEXT}; }}"
        )
        lay.addWidget(self.test_btn)

        lay.addWidget(QLabel("Modelo", styleSheet=f"color:{C_TEXT}; border:none; font-size:13px;"))
        self.model_cb = QComboBox()
        self.model_cb.setStyleSheet(self._combo_style())
        lay.addWidget(self.model_cb)

        self.err_lbl = QLabel("")
        self.err_lbl.setStyleSheet(f"color:{C_RED}; border:none; font-size:12px;")
        self.err_lbl.hide()
        lay.addWidget(self.err_lbl)

        btn = QPushButton("Salvar e Iniciar â†’")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(48)
        btn.clicked.connect(self._finish)
        btn.setStyleSheet(
            f"QPushButton {{ background:{C_ACCENT}; color:{C_BG_SIDE}; font-weight:800;"
            f" font-size:14px; border-radius:14px; border:none; }}"
            f"QPushButton:hover {{ background:#d4b4ff; }}"
            f"QPushButton:pressed {{ background:#b89ae6; }}"
        )
        lay.addWidget(btn)

        # Trigger initial state
        self._on_provider_changed(self.provider_cb.currentText())

    def _on_provider_changed(self, provider: str):
        self.model_cb.clear()
        if provider == "Google Gemini":
            self.model_cb.addItems(GEMINI_MODELS)
            self.api_input.setPlaceholderText("AIzaâ€¦")
            self.hint_lbl.setText(
                'Obtenha em: <a href="https://aistudio.google.com/apikey" '
                f'style="color:{C_ACCENT};">Google AI Studio</a><br>'
                f'<span style="color:{C_TEAL}; font-size:10px;">ðŸ’¡ Recomendado: use OpenRouter para mais modelos gratuitos</span>'
            )
        else:
            self.model_cb.addItems(OPENROUTER_MODELS)
            self.api_input.setPlaceholderText("sk-or-â€¦")
            self.hint_lbl.setText(
                'Obtenha em: <a href="https://openrouter.ai/keys" '
                f'style="color:{C_ACCENT};">openrouter.ai/keys</a><br>'
                f'<span style="color:{C_GREEN}; font-size:10px;">âœ“ Qwen 3.6, Llama 3.3, GPT-4o e mais â€” todos grÃ¡tis!</span>'
            )
        if self._current.get("provider") == provider:
            idx = self.model_cb.findText(self._current.get("model", ""))
            if idx >= 0:
                self.model_cb.setCurrentIndex(idx)

    def _test_connection(self):
        key = self.api_input.text().strip()
        if not key:
            self.err_lbl.setText("âš  Insira uma API Key antes de testar.")
            self.err_lbl.show()
            return
        
        self.test_btn.setEnabled(False)
        self.test_btn.setText("â³ Testando...")
        self.err_lbl.hide()
        
        provider = self.provider_cb.currentText()
        import threading
        
        def test():
            try:
                if provider == "OpenRouter":
                    resp = requests.get(
                        "https://openrouter.ai/api/v1/auth/key",
                        headers={"Authorization": f"Bearer {key}"},
                        timeout=10
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        credits = data.get("data", {}).get("credits", "N/A")
                        msg = f"âœ… ConexÃ£o OK! CrÃ©ditos: {credits}"
                        self._test_success(msg)
                    else:
                        self._test_fail(f"API Key invÃ¡lida (HTTP {resp.status_code})")
                else:
                    client = genai.Client(api_key=key)
                    res = client.models.list()
                    models = [str(m.id) for m in res.models if hasattr(m, 'id')]
                    msg = f"âœ… ConexÃ£o OK! {len(models)} modelos disponÃ­veis."
                    self._test_success(msg)
            except Exception as e:
                self._test_fail(str(e))
        
        threading.Thread(target=test, daemon=True).start()
    
    def _test_success(self, msg):
        self.err_lbl.setStyleSheet(f"color:{C_GREEN}; border:none; font-size:12px;")
        self.err_lbl.setText(msg)
        self.err_lbl.show()
        self.test_btn.setEnabled(True)
        self.test_btn.setText("ðŸ” Testar ConexÃ£o")
    
    def _test_fail(self, msg):
        self.err_lbl.setStyleSheet(f"color:{C_RED}; border:none; font-size:12px;")
        self.err_lbl.setText(f"âŒ Erro: {msg}")
        self.err_lbl.show()
        self.test_btn.setEnabled(True)
        self.test_btn.setText("ðŸ” Testar ConexÃ£o")

    def _finish(self):
        key = self.api_input.text().strip()
        if not key:
            self.err_lbl.setText("âš  Insira uma API Key vÃ¡lida.")
            self.err_lbl.show()
            return
        cfg = {
            "provider": self.provider_cb.currentText(),
            "api_key":  key,
            "model":    self.model_cb.currentText(),
        }
        save_config(cfg)
        self.config_saved.emit(cfg)
        self.close()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(self.pos() + e.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = e.globalPosition().toPoint()

# â”€â”€ Main window â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class GeminiWindow(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self._config = config
        self.all_chats: dict[str, list] = {}
        self.current_chat_id: str | None = None
        self._drag_pos  = None
        self._worker: GeminiWorker | None = None
        self._full_response = ""
        self._typing_idx    = 0
        self._type_timer    = QTimer(self)
        self._type_timer.timeout.connect(self._tick_typing)

        self._build_ui()
        self.load_chats_from_disk()
        self._fade_in()

    @property
    def _provider(self): return self._config.get("provider", "Google Gemini")
    @property
    def _model(self):    return self._config.get("model", "")

    def _ia_color(self):
        return C_YELLOW if self._provider == "OpenRouter" else C_GREEN

    def _provider_badge_html(self) -> str:
        if self._provider == "OpenRouter":
            return (
                f"<span style='background:rgba(249,226,175,0.15); color:{C_YELLOW};"
                f" padding:2px 10px; border-radius:8px; font-size:11px;'>OpenRouter</span>"
            )
        return (
            f"<span style='background:rgba(203,166,247,0.15); color:{C_ACCENT};"
            f" padding:2px 10px; border-radius:8px; font-size:11px;'>Google Gemini</span>"
        )

    # â”€â”€ UI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _build_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        # Translucent
        self.resize(1120, 760)

        self._root = QFrame(self)
        self._root.setObjectName("Root")
        self._root.setStyleSheet(
            f"QFrame#Root {{ background:{C_BG_MAIN}; border-radius:30px;"
            f" border:1px solid rgba(255,255,255,0.08); }}"
        )
        win_lay = QVBoxLayout(self)
        win_lay.setContentsMargins(0, 0, 0, 0)
        win_lay.addWidget(self._root)

        hbar = QHBoxLayout(self._root)
        hbar.setContentsMargins(0, 0, 0, 0)
        hbar.setSpacing(0)
        hbar.addWidget(self._build_sidebar())
        hbar.addWidget(self._build_content())

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setFixedWidth(265)
        sidebar.setStyleSheet(
            f"QFrame {{ background:{C_BG_SIDE}; border-top-left-radius:30px;"
            f" border-bottom-left-radius:30px; }}"
        )
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(12, 18, 12, 18)
        lay.setSpacing(10)

        brand = QLabel("âœ¦ NebulaAI")
        brand.setStyleSheet(
            f"color:{C_ACCENT}; font-size:17px; font-weight:800; border:none; padding-left:6px;"
        )
        lay.addWidget(brand)

        self.provider_lbl = QLabel()
        self.provider_lbl.setTextFormat(Qt.TextFormat.RichText)
        self.provider_lbl.setStyleSheet("border:none; padding-left:4px;")
        self.provider_lbl.setText(self._provider_badge_html())
        lay.addWidget(self.provider_lbl)

        btn_new = QPushButton("+ Novo Chat")
        btn_new.setFixedHeight(42)
        btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new.clicked.connect(self.new_chat)
        btn_new.setStyleSheet(
            f"QPushButton {{ background:{C_ACCENT}; color:{C_BG_SIDE}; font-weight:800;"
            f" border-radius:13px; border:none; font-size:13px; }}"
            f"QPushButton:hover {{ background:#d4b4ff; }}"
            f"QPushButton:pressed {{ background:#b89ae6; }}"
        )
        lay.addWidget(btn_new)

        sep = QLabel("HISTÃ“RICO")
        sep.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:10px; font-weight:800;"
            f" padding-left:6px; border:none; margin-top:4px;"
        )
        lay.addWidget(sep)

        self.list_w = QListWidget()
        self.list_w.setStyleSheet(
            "QListWidget { background:transparent; border:none; outline:none; }"
            "QListWidget::item { background:transparent; padding:2px; }"
        )
        self.list_w.setSpacing(2)
        lay.addWidget(self.list_w)

        lay.addWidget(QLabel(
            "Modelo",
            styleSheet=f"color:{C_SUBTEXT}; font-size:10px; font-weight:800; border:none;"
        ))
        self.model_cb = QComboBox()
        self._populate_model_cb()
        self.model_cb.currentTextChanged.connect(
            lambda t: self._config.update({"model": t})
        )
        self.model_cb.setStyleSheet(
            f"QComboBox {{ background:{C_BG_INPUT}; color:white; padding:8px 12px;"
            f" border-radius:10px; border:none; font-size:12px; }}"
            f"QComboBox::drop-down {{ border:none; }}"
            f"QComboBox QAbstractItemView {{ background:{C_BG_SURF}; color:white;"
            f" selection-background-color:{C_ACCENT}; selection-color:{C_BG_SIDE}; }}"
        )
        lay.addWidget(self.model_cb)
        return sidebar

    def _populate_model_cb(self):
        self.model_cb.blockSignals(True)
        self.model_cb.clear()
        models = OPENROUTER_MODELS if self._provider == "OpenRouter" else GEMINI_MODELS
        self.model_cb.addItems(models)
        idx = self.model_cb.findText(self._model)
        if idx >= 0:
            self.model_cb.setCurrentIndex(idx)
        self.model_cb.blockSignals(False)

    def _build_content(self) -> QFrame:
        content = QFrame()
        content.setStyleSheet("QFrame { background: transparent; }")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(20, 14, 18, 8)

        self.title_lbl = QLabel("Novo Chat")
        self.title_lbl.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:13px; font-weight:600; border:none;"
        )
        header.addWidget(self.title_lbl)
        header.addStretch()

        # Show API status
        self.api_status = QLabel("âŒ Sem API Key")
        self.api_status.setStyleSheet(f"color:{C_RED}; font-size:11px; border:none; padding-right:8px;")
        if self._config.get("api_key"):
            self.api_status.setText("âœ… Conectado")
            self.api_status.setStyleSheet(f"color:{C_GREEN}; font-size:11px; border:none; padding-right:8px;")
        header.addWidget(self.api_status)

        btn_close = QPushButton("âœ•")
        btn_close.setFixedSize(30, 30)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet(
            f"QPushButton {{ background:{C_BG_INPUT}; color:white; border-radius:15px; border:none; }}"
            f"QPushButton:hover {{ background:{C_RED}; }}"
        )
        header.addWidget(btn_close)
        lay.addLayout(header)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet(
            f"QTextEdit {{ background:transparent; border:none; color:{C_TEXT};"
            f" padding:10px 24px; font-size:14px; }}"
            f"QScrollBar:vertical {{ background:{C_BG_SURF}; width:5px; border-radius:3px; }}"
            f"QScrollBar::handle:vertical {{ background:{C_BG_INPUT}; border-radius:3px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}"
        )
        lay.addWidget(self.chat_area)

        self.thinking = ThinkingDots()
        lay.addWidget(self.thinking)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(20, 4, 20, 20)
        input_row.setSpacing(10)

        self.input_f = QLineEdit()
        self.input_f.setPlaceholderText("Escreva uma mensagemâ€¦")
        self.input_f.setFixedHeight(50)
        self.input_f.returnPressed.connect(self.send_msg)
        self.input_f.setStyleSheet(
            f"QLineEdit {{ background:{C_BG_INPUT}; color:white; border-radius:20px;"
            f" padding:0 20px; border:1px solid transparent; font-size:14px; }}"
            f"QLineEdit:focus {{ border:1px solid {C_ACCENT}; }}"
            f"QLineEdit:disabled {{ color:{C_SUBTEXT}; }}"
        )

        self.btn_send = QPushButton("âž¤")
        self.btn_send.setFixedSize(50, 50)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.clicked.connect(self.send_msg)
        self.btn_send.setStyleSheet(
            f"QPushButton {{ background:{C_ACCENT}; color:{C_BG_SIDE}; border-radius:25px;"
            f" border:none; font-size:16px; font-weight:800; }}"
            f"QPushButton:hover {{ background:#d4b4ff; }}"
            f"QPushButton:disabled {{ background:{C_BG_INPUT}; color:{C_SUBTEXT}; }}"
        )

        self.btn_stop = QPushButton("â– ")
        self.btn_stop.setFixedSize(50, 50)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.clicked.connect(self._stop_generation)
        self.btn_stop.setStyleSheet(
            f"QPushButton {{ background:{C_BG_INPUT}; color:{C_RED}; border-radius:25px;"
            f" border:none; font-size:16px; }}"
            f"QPushButton:hover {{ background:rgba(243,139,168,0.15); }}"
            f"QPushButton:disabled {{ color:{C_SUBTEXT}; }}"
        )

        input_row.addWidget(self.input_f)
        input_row.addWidget(self.btn_send)
        input_row.addWidget(self.btn_stop)
        lay.addLayout(input_row)
        return content

    def _fade_in(self):
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(400)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    # â”€â”€ Messaging â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def send_msg(self):
        txt = self.input_f.text().strip()
        if not txt:
            return

        # Handle /key command
        if txt.startswith('/key '):
            api_key = txt[5:].strip()
            if api_key:
                self._config['api_key'] = api_key
                self._config['provider'] = 'OpenRouter'
                save_config(self._config)
                self.api_status.setText("âœ… Conectado")
                self.api_status.setStyleSheet(f"color:{C_GREEN}; font-size:11px; border:none; padding-right:8px;")
                self.chat_area.append(
                    f"<div style='background:rgba(166,227,161,0.15); padding:12px;"
                    f" border-radius:10px; color:{C_GREEN}; margin:10px 0;'>"
                    f"<b>âœ… API Key salva!</b><br>"
                    f"Agora vocÃª pode conversar normalmente."
                    f"</div><br>"
                )
                self.input_f.clear()
            return
        elif txt == '/key':
            self.chat_area.append(
                f"<div style='background:rgba(249,226,175,0.15); padding:12px;"
                f" border-radius:10px; color:{C_YELLOW}; margin:10px 0;'>"
                f"<b>ðŸ”‘ Como configurar API Key:</b><br><br>"
                f"1. Acesse: <a href='https://openrouter.ai/keys' style='color:{C_ACCENT};'>openrouter.ai/keys</a><br>"
                f"2. Crie uma conta gratuita<br>"
                f"3. Clique em 'Create Key'<br>"
                f"4. Copie a chave (comeÃ§a com sk-or-...)<br><br>"
                f"<b>Use no chat:</b> <code style='background:{C_BG_INPUT}; padding:2px 6px; border-radius:4px;'>/key sk-or-sua-chave-aqui</code>"
                f"</div><br>"
            )
            self.input_f.clear()
            return

        # Check if API key is set
        if not self._config.get('api_key'):
            self.chat_area.append(
                f"<div style='background:rgba(243,139,168,0.15); padding:12px;"
                f" border-radius:10px; color:{C_RED}; margin:10px 0;'>"
                f"<b>âš  API Key nÃ£o configurada</b><br>"
                f"Use <code style='background:{C_BG_INPUT}; padding:2px 6px; border-radius:4px;'>/key</code> para ver instruÃ§Ãµes"
                f"</div><br>"
            )
            self.input_f.clear()
            return

        if not self.current_chat_id:
            self.new_chat()

        self._append_user_bubble(txt)
        self.all_chats[self.current_chat_id].append(
            {'role': 'user', 'parts': [{'text': txt}]}
        )
        self.input_f.clear()
        self._set_busy(True)

        self._worker = AIWorker(self._config, self.all_chats[self.current_chat_id])
        self._worker.finished.connect(self._on_finished)
        self._worker.errored.connect(self._on_error)
        self._worker.start()

    def _stop_generation(self):
        if self._worker and self._worker.isRunning():
            self._worker.abort()
        self._type_timer.stop()
        self.thinking.stop()
        self._set_busy(False)
        self.chat_area.append(
            f"<i style='color:{C_SUBTEXT};'>â€” geraÃ§Ã£o interrompida â€”</i><br>"
        )

    def _on_finished(self, text: str):
        self.thinking.stop()
        self._full_response = text
        self._typing_idx    = 0
        self.chat_area.append(
            f"<b style='color:{self._ia_color()};'>IA</b> "
            f"<span style='color:{C_SUBTEXT}; font-size:11px;'>({self._model})</span><br>"
        )
        self._type_timer.start(8)

    def _on_error(self, err: str):
        self.thinking.stop()
        self._set_busy(False)
        self.chat_area.append(
            f"<div style='background:rgba(243,139,168,0.15); padding:10px;"
            f" border-radius:10px; color:{C_RED};'><b>Erro:</b> {err}</div><br>"
        )

    def _tick_typing(self):
        if self._typing_idx < len(self._full_response):
            cursor = self.chat_area.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.chat_area.setTextCursor(cursor)
            self.chat_area.insertPlainText(self._full_response[self._typing_idx])
            self._typing_idx += 1
            self.chat_area.verticalScrollBar().setValue(
                self.chat_area.verticalScrollBar().maximum()
            )
        else:
            self._type_timer.stop()
            self.chat_area.append("<br>")
            history = self.all_chats.get(self.current_chat_id, [])
            history.append({'role': 'model', 'parts': [{'text': self._full_response}]})
            self.save_chat()
            self._set_busy(False)
            if len(history) == 2:
                self._auto_name(history[0]['parts'][0]['text'])

    # â”€â”€ Auto-rename â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _auto_name(self, first_msg: str):
        try:
            prompt = f"Resuma em 2-3 palavras (sem pontuaÃ§Ã£o): {first_msg}"
            if self._provider == "OpenRouter":
                headers = {
                    "Authorization": f"Bearer {self._config['api_key']}",
                    "Content-Type":  "application/json",
                }
                resp = requests.post(
                    OPENROUTER_BASE,
                    headers=headers,
                    json={
                        "model":    self._model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=10
                )
                new_name = resp.json()["choices"][0]["message"]["content"].strip()
            else:
                client   = genai.Client(api_key=self._config["api_key"])
                res      = client.models.generate_content(
                    model=self._model, contents=prompt
                )
                new_name = res.text.strip()

            new_name = new_name.replace('"', '').replace('.', '').strip()[:22]
            if not new_name or new_name == self.current_chat_id:
                return

            old_id   = self.current_chat_id
            old_path = os.path.join(CHATS_DIR, f"{old_id}.json")
            self.all_chats[new_name] = self.all_chats.pop(old_id)
            if os.path.exists(old_path):
                os.remove(old_path)
            self.current_chat_id = new_name
            self.save_chat()
            self.load_chats_from_disk()
            self.title_lbl.setText(new_name)
        except Exception:
            pass

    # â”€â”€ Chat management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def new_chat(self):
        cid = f"SessÃ£o {datetime.now().strftime('%H%M%S')}"
        self.all_chats[cid] = []
        self.current_chat_id = cid
        self.chat_area.clear()
        self.title_lbl.setText(cid)
        self.save_chat()
        self.load_chats_from_disk()

    def save_chat(self):
        if not self.current_chat_id:
            return
        with open(
            os.path.join(CHATS_DIR, f"{self.current_chat_id}.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(self.all_chats[self.current_chat_id], f, ensure_ascii=False)

    def load_chats_from_disk(self):
        self.list_w.clear()
        try:
            files = sorted(
                [f for f in os.listdir(CHATS_DIR) if f.endswith(".json")],
                key=lambda x: os.path.getmtime(os.path.join(CHATS_DIR, x)),
                reverse=True
            )
        except OSError:
            files = []

        for fname in files:
            cid   = fname.replace(".json", "")
            fpath = os.path.join(CHATS_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    self.all_chats[cid] = json.load(fh)
            except Exception:
                self.all_chats[cid] = []

            item = QListWidgetItem(self.list_w)
            item.setSizeHint(QSize(0, 46))
            widget = ChatItemWidget(cid, active=(cid == self.current_chat_id))
            widget.delete_requested.connect(self.del_chat)
            widget.selected.connect(self.switch_chat)
            self.list_w.addItem(item)
            self.list_w.setItemWidget(item, widget)

        if files and not self.current_chat_id:
            self.current_chat_id = files[0].replace(".json", "")

    def del_chat(self, cid: str):
        path = os.path.join(CHATS_DIR, f"{cid}.json")
        if os.path.exists(path):
            os.remove(path)
        self.all_chats.pop(cid, None)
        if self.current_chat_id == cid:
            self.current_chat_id = None
            self.chat_area.clear()
            self.title_lbl.setText("Novo Chat")
        self.load_chats_from_disk()

    def switch_chat(self, cid: str):
        self.current_chat_id = cid
        self.title_lbl.setText(cid)
        self.chat_area.clear()
        for msg in self.all_chats.get(cid, []):
            role = msg.get('role', '')
            text = msg['parts'][0]['text'] if msg.get('parts') else ''
            if role == 'user':
                self._append_user_bubble(text)
            else:
                self.chat_area.append(
                    f"<b style='color:{self._ia_color()};'>IA</b><br>"
                    f"{render_markdown(text)}<br>"
                )
        self.load_chats_from_disk()

    # â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _append_user_bubble(self, text: str):
        self.chat_area.append(
            f"<div style='background:{C_BUBBLE_U}; padding:12px 16px;"
            f" border-radius:14px; margin-bottom:6px;'>"
            f"<b style='color:{C_ACCENT2};'>VOCÃŠ</b><br>{text}</div><br>"
        )

    def _set_busy(self, busy: bool):
        self.input_f.setEnabled(not busy)
        self.btn_send.setEnabled(not busy)
        self.btn_stop.setEnabled(busy)
        if busy:
            self.thinking.start()
        else:
            self.thinking.stop()

        # Criar overlay dentro da janela principal
        self._overlay = SettingsOverlay(self, current=self._config)
        self._overlay.show()
    
        self._config = cfg
        save_config(cfg)
        self._populate_model_cb()
        self.provider_lbl.setText(self._provider_badge_html())
        self._overlay.hide()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(self.pos() + e.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = e.globalPosition().toPoint()

# â”€â”€ Entry point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    config = load_config()
    win: GeminiWindow | None = None

    def start_app(cfg: dict):
        global win
        win = GeminiWindow(cfg)
        win.show()
        # Se nÃ£o tem config, mostrar overlay automaticamente
        if not load_config():
            win._open_setup()

    # Sempre inicia o app, com ou sem config
    dummy_config = config or {"provider": "OpenRouter", "api_key": "", "model": OPENROUTER_MODELS[0]}
    start_app(dummy_config)

    sys.exit(app.exec())
