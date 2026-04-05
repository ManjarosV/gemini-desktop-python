# 🌌 Nebula Gemini Desktop

Uma interface desktop moderna e minimalista para interagir com o Google Gemini AI, construída com Python e PyQt6. Inspirada na estética **Catppuccin Mocha**.

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.11+-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📥 Download (Windows x64)

Para utilizar o Nebula Gemini sem precisar instalar o Python, baixe o executável abaixo:

> ### 🚀 [**Baixar Nebula Gemini v1.0**](https://github.com/ManjarosV/gemini-desktop-python/raw/main/dist/NebulaGemini.exe)
> *Versão compilada para Windows 10/11 x64.*

---

## 🛠️ Como Configurar

Ao abrir o aplicativo pela primeira vez, você precisará configurar sua API Key:

| Passo | Ação | Link |
| :--- | :--- | :--- |
| **1** | Obtenha uma chave de API gratuita | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| **2** | Cole a chave na tela de Setup do App | - |
| **3** | Escolha seu modelo (ex: `gemini-2.0-flash`) | - |

---

## ✨ Funcionalidades

* **🎨 Interface Catppuccin:** Visual moderno, escuro e minimalista.
* **💾 Histórico Local**: Salva suas conversas em arquivos JSON de forma local na pasta do usuário.
* **⚙️ Zero Config:** Configuração inicial rápida através da interface, sem necessidade de editar o código.
* **🗑️ Gerenciamento de Chats**: Botão para deletar conversas individuais diretamente na barra lateral.

---

## 💻 Como Rodar (Desenvolvedores)

Se preferir rodar o código fonte no seu **Arch Linux** ou Windows:


1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/ManjarosV/gemini-desktop-python.git](https://github.com/ManjarosV/gemini-desktop-python.git)
   cd gemini-desktop-python

2. **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
   # Ou manualmente: pip install PyQt6 google-genai

3. **Execute o script:**
     ```bash
     python nebula_gemini.py

**🏗️ Notas Técnicas (Versão dos DEVS)**
```bash
Status atual do desenvolvimento e detalhes internos:

   - Auto-Rename: Renomeia sessões baseado no contexto da primeira pergunta. (Status: Experimental/Inoperante em certas condições).

   - Design Moderno: Janela arredondada, sem bordas e com animações de pulsação. (Status: Necessita de correções visuais básicas em alguns sistemas).

   - Performance: O desempenho de resposta depende inteiramente do modelo selecionado pelo usuário.

   - Gerenciamento de Chats: Sistema de deleção via sidebar. (Status: Testes de estabilidade pendentes).
`
