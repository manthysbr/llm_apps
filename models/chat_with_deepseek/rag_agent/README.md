# HeraCorps RAG (Retrieval-Augmented Generation) Agent

## 🚀 Visão Geral  
Este protótipo implementa um agente de **RAG (Retrieval‑Augmented Generation)** em Python, combinando:
- Streamlit como UI interativa de chat  
- FAISS para armazenamento vetorial e busca semântica  
- HuggingFace Embeddings (`all‑MiniLM‑L6‑v2`)  
- LLM local (Ollama/deepseek‑r1:14b) orquestrado via LangChain  

O objetivo é permitir que pesquisadores carreguem documentos (PDFs), indexem o conteúdo e façam consultas em linguagem natural, recebendo respostas fundamentadas no corpus carregado.

## 🎯 Problema Endereçado  
- Dificuldade de extrair informação de grandes volumes de documentos legais, técnicos ou de pesquisa.  
- Ferramentas tradicionais de busca não capturam semântica e contexto de forma robusta.  
- Necessidade de protótipos de pesquisa para avaliar integração LLM + vector store em pipelines RAG.

## 🏗 Arquitetura & Fluxo de Dados  
1. **Upload de Documentos**  
   - Usuário faz upload de múltiplos PDFs via Streamlit.  
   - Cada arquivo é salvo temporariamente e carregado com `PyPDFLoader`.  
2. **Pré‑processamento**  
   - Split de texto em chunks de 1000 tokens, overlap de 200 (via `RecursiveCharacterTextSplitter`).  
3. **Indexação Vetorial**  
   - Vetorização com `HuggingFaceEmbeddings` sobre cada chunk.  
   - Criação de índice FAISS on‑memory (`FAISS.from_documents`).  
4. **Chat Interativo**  
   - Histórico mantido em `st.session_state.chat_history`.  
   - No envio de uma pergunta:
     - Busca semântica (`similarity_search(k=3)`) retorna contextos relevantes.  
     - Construção de prompt LangChain (`ChatPromptTemplate`) com bloco SYSTEM + HUMAN.  
     - Geração de resposta via Ollama e parsing por `StrOutputParser`.  
     - Extração de raciocínio interno (`<think>…</think>`) por regex.  
     - Exibição da resposta, raciocínio e fontes usadas.

```
[User Query] ─► FAISS Retrieve ─► Context ► Prompt │
                                ↓                 ▼
                             Ollama LLM ─► Parsed Response ─► Streamlit UI
```

## 🔍 Componentes Principais  
- **rag.py**: aplicação Streamlit única para toda a pipeline.  
- **Streamlit**: interface de upload, chat e exibição de histórico.  
- **LangChain**  
  - `ChatPromptTemplate.from_messages()`  
  - `StrOutputParser()`  
  - `RecursiveCharacterTextSplitter`  
  - `PyPDFLoader`  
- **FAISS**: similaridade vetorial semântica.  
- **HuggingFaceEmbeddings**: geração de vetores de alta qualidade.  
- **Ollama (deepseek‑r1:14b)**: modelo on‑premise de geração de linguagem.

## 📦 Tecnologias & Bibliotecas  
- Python 3.8+  
- Streamlit  
- langchain‑community & langchain‑core  
- Ollama  
- FAISS  
- HuggingFace Embeddings  
- PyPDFLoader  
- Regex & built‑in Python I/O  

## ⚡️ Como Executar  
```bash
git clone https://github.com/manthysbr/llm_apps.git
cd llm_apps/models/chat_with_deepseek/rag_agent
pip install -r requirements.txt
streamlit run rag.py
```

Após inicializar, carregue arquivos PDF, aguarde o processamento e interaja via chat para obter respostas baseadas no conteúdo indexado.

## 🔭 Extensões Futuras  
- Persistência do índice FAISS em disco ou Qdrant  
- Suporte a outros formatos (Word, TXT, HTML)  
- Integração com autenticação e ACL  
- Monitoramento de latência e métricas de relevância  
- Adoção de function‑calling para executar ações a partir de respostas  

---
Feito com ❤️ pela HeraCorps AI Division  
