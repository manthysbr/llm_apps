# HeraCorps Financial Agent Team

## 🚀 Visão Geral  
Este repositório reúne dois protótipos de agentes de IA voltados para análise e gestão financeira, implementados em Python com integração a LLMs locais (Ollama/deepseek-r1:14b).  
1. **Financial Analyst** (`finance_team.py`): fornece análise de ações com dados de mercado e web scraping.  
2. **Financial Tracker** (`finance_tracker.py`): permite registrar despesas, armazenar embeddings em Qdrant e gerar insights de gastos.

## 🏗 Arquitetura  
```
┌────────────────────────┐      ┌──────────────┐      ┌─────────────┐
│  Streamlit Front‑end   │◄─────│ FinanceAgent │◄─────│ Ollama LLM  │
│ (UI interativa / chat) │      │  (Python)    │─────►│ deepseek-r1 │
└────────────────────────┘      └──────────────┘      └─────────────┘
                                       │
                ┌──────────────────┬───┴───┬──────────────────┐
                │                  │       │                  │
         yfinance / WebScraping   │  DuckDB/│ Qdrant (VDB)  │
        (cotação, histórico, news)│  Pandas │(embeddings +  │
                                   │         │  payloads)    │
                │                  │       │                  │
         PDF parsing (fitz)        └───────┴────────         │
                                          JSON files         │
```

## 🔍 Componentes Principais  

### 1. Financial Analyst (`finance_team.py`)  
- **Input**  
  - `stock_symbol` (yfinance)  
  - `analysis_query` (texto livre)  
- **Fluxo**  
  1. Coleta de dados de mercado via yfinance (`info`, `history`, `news`).  
  2. Web scraping (DuckDuckGo + BeautifulSoup) para notícias.  
  3. Prompting com **LangChain** (`ChatPromptTemplate`, `StrOutputParser`).  
  4. Exibição de “pensamentos” (`<think>…</think>`) e relatório em Markdown.  

### 2. Financial Tracker (`finance_tracker.py`)  
- **Entrada de Despesas**  
  - Upload de PDF (PyMuPDF/fitz) ou formulário manual.  
- **Armazenamento**  
  - **Qdrant** como vector store (embeddings `all-MiniLM-L6-v2`).  
  - JSON mensal em disco (`~finance_history/YYYY_MM.json`).  
- **Consultas & Insights**  
  - Busca semântica por NLP (`query_expenses`).  
  - Análise de padrão de gastos (`get_spending_insights`).  
  - Estatísticas e visualizações com Plotly & Streamlit.  

## 🛠 Técnicas e Tecnologias  
- **LLM Local**: Ollama + modelo `deepseek-r1:14b`  
- **LangChain**: orquestração de prompts e parsing de saída  
- **Embeddings**: HuggingFace `all-MiniLM-L6-v2`  
- **Vector Store**: Qdrant (busca vetorial semântica)  
- **DataFrame & SQL**: Pandas, DuckDB (execução in‑memory)  
- **Web Scraping**: Requests + BeautifulSoup  
- **PDF Parsing**: PyMuPDF (fitz)  
- **Front‑end**: Streamlit (UI interativa)  
- **Visualização**: Plotly Express & Graph Objects  

## ⚡️ Como Executar  
```bash
# Clone e acesse o diretório
git clone https://github.com/manthysbr/llm_apps.git
cd llm_apps/models/chat_with_deepseek/finance_agent_team

# Instale dependências
pip install -r requirements.txt

# Inicie Qdrant (tracker)
docker run -d -p 6333:6333 qdrant/qdrant

# Execute cada app em janelas separadas
streamlit run finance_team.py
streamlit run finance_tracker/finance_tracker.py
```

## 🔭 Extensões Futuras  
- Adotar function‑calling para ações automáticas (e.g., ordens de compra/venda)  
- Integração com bancos de dados remotos (PostgreSQL, Pinecone)  
- Fine‑tuning do LLM para domínios financeiros específicos  
- Autenticação multi‑tenant e controle de acesso  

---
Feito com ❤️ pela HeraCorps AI Division  