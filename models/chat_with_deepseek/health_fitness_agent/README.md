# HeraCorps Health & Fitness Planner Agent

## 🚀 Visão Geral  
Este protótipo implementa um **agente de IA** para criação automática de planos personalizados de treino e nutrição. Desenvolvido em Python, integra um LLM local (Ollama/deepseek-r1:14b) a uma interface Streamlit, gerando:

- Rotinas de exercícios detalhadas  
- Sugestões de refeições e macronutrientes  
- Métricas de acompanhamento (IMC, calorias, dias de treino)  
- Raciocínio científico explícito (blocos de “pensamento”)

## 🛠 Arquitetura & Fluxo de Dados  
1. **Front‑end (Streamlit)**  
   - Captura dados do usuário (idade, peso, altura, nível de atividade, objetivos, preferências alimentares).  
   - Renderiza métricas e plano final em tempo real.  
2. **Motor de IA (Ollama + deepseek‑r1:14b)**  
   - **LangChain**: `ChatPromptTemplate` para compor system+user prompt; `StrOutputParser` para extrair texto puro.  
   - **Function Pipeline**: `(prompt | llm | parser).invoke()` retornando JSON/texto com “pensamentos” opcionais.  
3. **Pós‑processamento & Métricas**  
   - Regex identifica blocos `<think>…</think>` e exibe raciocínio científico.  
   - Cálculo de IMC e sugestões de dias de treino/calorias via Python.

```
User Input → Streamlit UI → LangChain Prompt → LLM (Ollama) → Parsed Response → Display Plan & Metrics
```

## 📦 Tecnologias & Bibliotecas  
- Python 3.8+  
- Streamlit — UI interativa  
- Ollama (`deepseek-r1:14b`) — LLM on‑premise  
- LangChain — orquestração de prompts e parsing de saída  
- Regex — extração de raciocínio interno  
- Built‑in Python — cálculos de IMC e métricas

## ⚡️ Como Executar  
```bash
# 1. Clone o repositório
git clone https://github.com/manthysbr/llm_apps.git

# 2. Instale dependências
cd llm_apps/models/chat_with_deepseek/health_fitness_agent
pip install -r requirements.txt

# 3. Execute a aplicação
streamlit run health_and_fitness_agent.py
```

## 🔭 Possíveis Extensões  
- Armazenar histórico e progresso do usuário (memória persistente via FAISS/Qdrant)  
- Integração com wearables (Fitbit/Apple Health) e APIs de nutrição  
- Módulo de ajustes automáticos baseado em feedback (auto‑tuning de metas)  
- Multi‑agent: separar sub‑agentes para treino, nutrição e recuperação  

---
Feito com ❤️ pela HeraCorps AI Division  