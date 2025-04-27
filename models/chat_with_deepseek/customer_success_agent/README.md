# HeraCorps Customer Support Agent

## 🚀 Visão Geral  
Este repositório contém um protótipo de **agente de suporte ao cliente** desenvolvido em Python, integrado a um LLM local (via Ollama) e a técnicas de embeddings e recuperação vetorial. O objetivo é demonstrar uma abordagem de **chat personalizado** com memória de contexto e geração de perfis sintéticos, visando fluxos de atendimento automatizado em cenários de pesquisa.

## 🛠 Problema Abordado  
- Alto volume de tickets de atendimento manual  
- Falta de contexto histórico e personalização por cliente  
- Dificuldade em simular perfis de usuários para testes  

## ⚙️ Arquitetura & Fluxo de Dados  
1. **Interface Streamlit**  
   - Entrada de `customer_id` e geração de perfil sintético (`generate_synthetic_data()`).  
   - Chat interativo com bolhas de conversa (`st.chat_message` / `st.chat_input`).  
2. **Módulo de IA**  
   - `CustomerSupportAgent` encapsula:  
     - **LLM**: [`Ollama`](https://ollama.ai) apontado para o modelo `deepseek-r1:14b`.  
     - **Prompting**: `ChatPromptTemplate` do LangChain para geração de instruções ao LLM.  
     - **Output Parser**: `StrOutputParser` para extrair texto bruto da resposta.  
3. **Memória Vetorial**  
   - `HuggingFaceEmbeddings` + FAISS para armazenar e recuperar histórico de perguntas e respostas por `user_id`.  
4. **Pós‑processamento**  
   - Extração de blocos internos de “pensamento” (`<think>…</think>`) via regex para exibição opcional.  
   - Persistência no [`st.session_state`](https://docs.streamlit.io/) para manter histórico de mensagens.

## 📦 Tecnologias Utilizadas  
- Python 3.8+  
- Streamlit (UI de chat)  
- Ollama & deepseek-r1:14b (LLM on‑premise)  
- LangChain (`ChatPromptTemplate`, `StrOutputParser`)  
- HuggingFace Embeddings (`all-MiniLM-L6-v2`)  
- FAISS (vetorial store)  
- Regex (extração de pensamento)  

## 🔧 Instalação & Execução  
```bash
git clone https://github.com/manthysbr/llm_apps.git
cd llm_apps/models/chat_with_deepseek/customer_success_agent
pip install -r ../../../../requirements.txt
streamlit run customer_success.py
```  

## 📑 Estrutura de Código  
- `customer_success.py`  
  - **Classe** `CustomerSupportAgent`  
    - `handle_query(query, user_id, context)`: gera resposta LLM + atualiza FAISS  
    - `generate_synthetic_data(user_id)`: cria perfil JSON simulado  
  - **Fluxo Streamlit**: sidebar para configurações, chat loop, exibição de pensamentos e perfil.

## 🔭 Possíveis Extensões  
- Persistir memória em banco (ex: Redis, Pinecone)  
- Multi‑tenant e autenticação de usuários  
- Customização de prompts por domínio  
- Pipeline de fine‑tuning para personalização de respostas  

---

Made with ❤️ by HeraCorps AI Division  