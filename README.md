############################################################

# 🌌 Nebula Gemini Desktop

Uma interface desktop moderna e minimalista para interagir com o Google Gemini AI, construída com Python e PyQt6.

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

* **Interface Catppuccin:** Visual moderno e escuro.
* **Auto-Rename:** Os chats são renomeados automaticamente com base no contexto.
* **Histórico Local:** Seus chats ficam salvos na sua pasta de usuário.
* **Zero Config:** Configuração inicial rápida e simples.

---

## 💻 Como rodar (Desenvolvedores)

Se preferir rodar o código fonte no seu Arch Linux ou Windows:

1. Instale as dependências:
   `pip install PyQt6 google-genai`
2. Execute o script:
   `python nebula_gemini.py`


############################### ** Versão dos DEVS ** ###############################

```
#Gemini Desktop UI 

Uma interface desktop minimalista para o Google Gemini, construída com Python e PyQt6. Inspirada no tema Catppuccin.

## Funcionalidades
- **Histórico Automático**: Salva suas conversas em JSON de forma local.
- **Auto-Rename**: Renomeia sessões baseado no contexto da primeira pergunta. (inoperante)
- **Design Moderno**: Janela arredondada, sem bordas e com animações de pulsação. (precisa de correções visuais básicas)
- **Performance**: Depende do modelo usado pelo usuário (você altera para o seu uso)
- **Gerenciamento de Chats**: Botão para deletar conversas individuais na barra lateral. (Não testado 100%)

## Instalação
```
1. Clone o repositório:
   ```bash
   git clone git clone [https://github.com/ManjarosV/gemini-desktop-python.git](https://github.com/ManjarosV/gemini-desktop-python.git)
```

2. Instale as dependências:


pip install -r requirements.txt
```

3. Configure sua API Key:
Exporte como variável de ambiente ou substitua diretamente no código:

```bash
export GEMINI_API_KEY="sua_chave_aqui"
```

4. Rode o script:

```bash
python gemini_gui.py
```


