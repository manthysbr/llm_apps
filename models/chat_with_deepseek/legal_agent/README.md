# HeraCorps AI Legal Agent

## 🚀 Visão Geral  
Este módulo oferece dois protótipos de agentes jurídicos baseados em LLMs locais (Ollama/deepseek‑r1:14b) e Streamlit, com foco em pesquisa e automação de análise de documentos legais:  
1. **AI Legal Team** (`legal_team.py`): orquestra três especialistas—Pesquisa, Contratos e Estratégia—para múltiplas perspectivas de análise.  
2. **Assistente Jurídico Brasileiro** (`legal_agent.py`): pipeline único para upload de PDF, OCR (fallback), vetorização e consulta jurídica contextualizada.

## 🏗 Arquitetura & Fluxo de Dados  
1. **Ingestão**  
   - Upload de PDF via Streamlit.  
   - `PyPDFLoader` ou OCR com `pytesseract`/`pdf2image` como fallback.  
2. **Processamento**  
   - `RecursiveCharacterTextSplitter` chunk‑size 512/overlap 64.  
   - Extração de metadados (área jurídica, fonte).  
3. **Vetorização & Armazenamento**  
   - Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (Legal Team) ou `paraphrase-multilingual-MiniLM-L12-v2` (Assistente).  
   - FAISS in‑memory para índice semântico.  
4. **Recuperação & Análise**  
   - Similarity search (k=3) para contexto relevante.  
   - LangChain `ChatPromptTemplate` + `StrOutputParser`  
   - Multi‑agent: `LegalTeam.analyze()` dispara três cadeias de análise.  
   - Pipeline único: parâmetros dinâmicos via `RunnablePassthrough`, retriever e prompt customizado.  
5. **Exibição**  
   - Blocos Streamlit: raciocínio (`<think>…</think>`), resposta principal, documentos fonte.

## 🔍 Componentes Principais  
- `legal_team.py`  
  • Classe `LegalTeam` com `LegalAgent` especializado em três papéis  
  • `process_document()`: cria FAISS a partir de PDF chunked  
  • `analyze(query, knowledge_base, type)`: retorna dicionário de respostas  
- `legal_agent.py`  
  • OCR fallback via `PDFPlumberLoader` / `pytesseract`  
  • Vector store + retriever para busca semântica  
  • Prompt dinâmico com variáveis de área e nível de detalhe  
  • Exibição de processo de pensamento e fontes

## 📦 Tecnologias & Bibliotecas  
- Python 3.8+  
- Streamlit — UI interativa  
- Ollama (deepseek‑r1:14b) — LLM on‑premise  
- LangChain — Prompts, parsing, loaders, text splitter  
- FAISS — Armazenamento vetorial  
- HuggingFaceEmbeddings — Vetorização multilíngue/legal  
- pytesseract, pdf2image — OCR  
- PyPDFLoader, UnstructuredPDFLoader — Extração de texto  
- Regex — Extração de blocos de raciocínio  

## ⚡️ Como Executar  
```bash
cd llm_apps/models/chat_with_deepseek/legal_agent
pip install -r requirements.txt

# Analista multi‑agent
streamlit run legal_team.py

# Assistente Jurídico Brasileiro
streamlit run legal_agent.py
```

## 🔭 Extensões Futuras  
- Persistência de memória de consulta (FAISS/Qdrant)  
- Integração com bases regulatórias e APIs de jurisprudência  
- Function calling para gerar pareceres estruturados (JSON)  
- Avaliação comparativa de sub‑agentes via métricas de coerência  
- Multi‑tenant e controle de acesso por área jurídica  

---
Feito com ❤️ pela HeraCorps AI Division  
