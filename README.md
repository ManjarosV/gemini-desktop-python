
``` Bash
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



