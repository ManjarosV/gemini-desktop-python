<div align="center">

# 🌌 Nebula Gemini Desktop

Uma interface desktop moderna e minimalista para o Google Gemini AI,
construída com Python e PyQt6. Inspirada na estética Catppuccin Mocha.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

<!-- Adicione um screenshot aqui -->
<!-- ![Screenshot](assets/screenshot.png) -->

</div>

---

## ✨ Funcionalidades

- 🎨 **Interface Catppuccin Mocha** — visual escuro, moderno e minimalista
- 💾 **Histórico local** — conversas salvas em JSON na máquina do usuário
- ⚙️ **Setup via interface** — sem necessidade de editar código ou arquivos de config
- 🗑️ **Gerenciamento de chats** — delete conversas individuais pela sidebar
- 🔄 **Auto-rename de sessões** — nomeia conversas com base no contexto inicial

---

## 📥 Download (Windows x64)

Sem precisar instalar Python:

**[🚀 Releases → Nebula Gemini v1.0](../../releases)**

> Compatível com Windows 10/11 x64.

---

## 🛠️ Configuração

1. Abra o app
2. Obtenha uma API Key gratuita em [Google AI Studio](https://aistudio.google.com)
3. Cole a chave na tela de Setup
4. Escolha seu modelo (ex: `gemini-2.0-flash`)

---

## 💻 Rodando pelo código-fonte
```bash
# Clone o repositório
git clone https://github.com/ManjarosV/gemini-desktop-python.git
cd gemini-desktop-python

# Instale as dependências
pip install PyQt6 google-genai
# ou
pip install -r requirements.txt

# Execute
python nebula_gemini.py
```

**Requisitos:** Python 3.10+ | PyQt6 | google-genai

---

## 🗂️ Estrutura do Projeto
