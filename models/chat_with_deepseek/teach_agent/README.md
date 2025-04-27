# HeraCorps Educational Team Agent

## 🚀 Visão Geral  
Este protótipo demonstra um **pipeline multi‑agent** de geração de conteúdo educacional, usando Python e LLMs locais. Quatro sub‑agentes especializados (Professor, Academic Advisor, Research Librarian e Teaching Assistant) colaboram para criar:

- Base de conhecimento aprofundada  
- Roteiro de aprendizagem estruturado  
- Curadoria de recursos de estudo  
- Materiais práticos e exercícios  

A interface é construída com **Streamlit**, orquestrando chamadas ao LLM **Ollama/deepseek‑r1:14b** via **LangChain**.

## 🏗 Arquitetura & Fluxo de Dados  
1. **Front‑end (Streamlit)**  
   - Input de tópico de estudo  
   - Exibição de seções individuais para cada sub‑agente  
   - Exportação de resultados em Markdown  
2. **Sub‑agentes (TeachingAgent)**  
   - Cada instância recebe `role` e utiliza `ChatPromptTemplate` para construir prompts customizados  
   - Pipeline: `(prompt | llm | StrOutputParser()).invoke()`  
3. **Processamento**  
   - Extração de “pensamentos” internos (`<think>…</think>`) via regex  
   - Armazenamento em `st.session_state.documents` para contexto incremental  
4. **Exportação**  
   - Geração de arquivos `.md` com carimbo de data/hora para cada agente

```
User Input ─► TeachingAgent(role) ─► LangChain Prompt ─► Ollama LLM ─► Parsed Response ─► Streamlit UI + Export
```

## 🔍 Componentes Principais  
- `teachers_team.py`  
  • Classe `TeachingAgent(role)`  
    - Métodos: `generate_content(topic, context="")`  
    - Prompt templates específicos por papel  
  • Interface Streamlit  
    - Input de tópico  
    - Loop de agentes com expanders  
    - Botões de exportação  
  • Armazenamento em sessão para contexto e histórico  

## 📦 Tecnologias & Bibliotecas  
- Python 3.8+  
- Streamlit — UI interativa  
- Ollama (`deepseek-r1:14b`) — LLM on‑premise  
- LangChain — `ChatPromptTemplate`, `StrOutputParser`  
- Regex — extração de blocos de raciocínio  
- datetime/os — gerenciamento de arquivos de exportação  

## ⚡️ Como Executar  
```bash
# 1. Clone o repositório
git clone https://github.com/manthysbr/llm_apps.git

# 2. Instale dependências
cd llm_apps/models/chat_with_deepseek/teach_agent
pip install -r requirements.txt

# 3. Execute a aplicação
streamlit run teachers_team.py
```

## 🔭 Extensões Futuras  
- Persistência de conteúdo em banco (FAISS/Qdrant) para versionamento de tópicos  
- Multi‑agent feedback loop: agentes revisando conteúdo uns dos outros  
- Avaliação automática de qualidade (métricas de coerência e completude)  
- Integração com plataformas de e‑learning (Moodle, Canvas)  

---
*Repositório de pesquisa em Agentes de IA e Python — HeraCorps AI Division*  