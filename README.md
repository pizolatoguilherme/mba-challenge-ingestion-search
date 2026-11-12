# Desafio MBA Engenharia de Software com IA - Full Cycle

Sistema de perguntas e respostas sobre um documento PDF usando **RAG (Retrieval-Augmented Generation)**. O PDF é dividido em chunks, convertido em embeddings e armazenado no PostgreSQL com **pgVector**. No chat via terminal, cada pergunta é vetorizada, os 10 trechos mais relevantes são buscados no banco e a LLM responde **somente** com base nesse conteúdo.

O projeto suporta **OpenAI** e **Google Gemini**, escolhidos pela variável `LLM_PROVIDER` no `.env`.

## 📋 Pré-requisitos

- Python 3.12+ (testado com 3.14)
- Docker e Docker Compose
- API Key da OpenAI **ou** da Google (Gemini)

## 🚀 Como executar o projeto

### 1. Clone o repositório

```bash
git clone https://github.com/pizolatoguilherme/mba-challenge-ingestion-search.git
cd mba-challenge-ingestion-search
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com a sua chave e o provedor escolhido:

```bash
# Provedor de embeddings + LLM: openai | gemini
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-5-nano

# Google Gemini
GOOGLE_API_KEY=
GOOGLE_EMBEDDING_MODEL=models/gemini-embedding-001
GOOGLE_LLM_MODEL=gemini-2.5-flash-lite

# Banco de dados (docker-compose)
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rag
# O nome final da collection recebe o sufixo do provedor (ex.: documents_openai)
PG_VECTOR_COLLECTION_NAME=documents

# Caminho do PDF (relativo à raiz do projeto)
PDF_PATH=document.pdf
```

> Os nomes de modelos mudam com frequência. Se algum estiver descontinuado, consulte a documentação oficial do provedor e ajuste no `.env`.

### 3. Suba o PostgreSQL com pgVector

```bash
docker compose up -d

# Verifique se o container está rodando (postgres_rag deve estar "healthy")
docker compose ps
```

### 4. Crie o ambiente virtual e instale as dependências

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Execute a ingestão do PDF

```bash
python src/ingest.py
```

Esse script:
- Carrega o `document.pdf`
- Divide o conteúdo em chunks de 1000 caracteres com overlap de 150
- Gera os embeddings com o provedor configurado
- Armazena os vetores no PostgreSQL com pgVector (a collection é recriada a cada execução, sem duplicar dados)

### 6. Execute o chat

```bash
python src/chat.py
```

## 💬 Como usar o chat

Ao iniciar, o chat exibe:

```
Faça sua pergunta (digite 'sair' para encerrar):
```

**Exemplo de uso:**

```
PERGUNTA: Qual o faturamento da empresa Alfa Energia S.A.?
RESPOSTA: R$ 722.875.391,46

---

PERGUNTA: Em que ano foi fundada a Alfa IA Indústria?
RESPOSTA: 2020

---

PERGUNTA: Qual é a capital da França?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.

---

PERGUNTA: Quantos clientes temos em 2024?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.

---
```

### Comandos disponíveis no chat:

- Digite sua pergunta e pressione **Enter**
- Para sair: `sair`, `exit` ou `quit`
- `Ctrl+C` também encerra o chat

## 📁 Estrutura do projeto

```
├── docker-compose.yml    # PostgreSQL + pgVector
├── requirements.txt      # Dependências
├── .env.example          # Template das variáveis de ambiente
├── src/
│   ├── ingest.py         # Script de ingestão do PDF
│   ├── search.py         # Provedores (OpenAI/Gemini) + busca vetorial (k=10) + prompt + LLM
│   ├── chat.py           # CLI para interação com usuário
├── document.pdf          # PDF para ingestão
└── README.md             # Instruções de execução
```

## 🔧 Comandos úteis

### Parar o banco de dados

```bash
docker compose down
```

### Ver os logs do banco

```bash
docker compose logs postgres
```

### Resetar o banco (apaga todos os dados)

```bash
docker compose down -v
docker compose up -d
python src/ingest.py
```

### Trocar de provedor (OpenAI ↔ Gemini)

```bash
# 1. Altere LLM_PROVIDER no .env
# 2. Refaça a ingestão (cada provedor usa sua própria collection)
python src/ingest.py
```

## 🛠️ Tecnologias utilizadas

- **Python**: linguagem do projeto
- **LangChain**: orquestração do pipeline de RAG (loader, splitter, prompt e chain)
- **OpenAI / Google Gemini**: modelos de embeddings e LLM
- **PostgreSQL + pgVector**: armazenamento e busca por similaridade dos vetores
- **PyPDF**: leitura do PDF
- **Docker / Docker Compose**: execução do banco de dados

## ❗ Solução de problemas

### Erro de conexão com o banco

- Verifique se o container está rodando: `docker ps`
- Reinicie o banco: `docker compose restart`
- Confira o `DATABASE_URL` no `.env` (usuário `postgres`, senha `postgres`, banco `rag`, porta `5432`)

### Erro `permission denied` ao rodar o Docker (Linux/WSL)

- Adicione seu usuário ao grupo docker: `sudo usermod -aG docker $USER`
- Abra um novo terminal (no WSL, rode `wsl --shutdown` no PowerShell e reabra)

### Erro na API da OpenAI / Gemini

- Verifique se a chave está correta no `.env` e se corresponde ao `LLM_PROVIDER`
- Erro `429 insufficient_quota`: a conta OpenAI está sem créditos. Adicione créditos em *Settings → Billing*
- Erro `429` no Gemini: limite do plano gratuito atingido. Aguarde e tente novamente

### Erro de dimensão do vetor

- Acontece ao trocar o modelo de embeddings sem refazer a ingestão
- Rode `python src/ingest.py` novamente (a collection é recriada); se persistir, resete o banco com `docker compose down -v`

### Erro de dependências

- Confirme que o ambiente virtual está ativo: `source venv/bin/activate`
- Reinstale: `pip install -r requirements.txt`

### Documento não encontrado

- Confirme que o `document.pdf` está na raiz do projeto (ou ajuste `PDF_PATH` no `.env`)
- Execute novamente: `python src/ingest.py`
