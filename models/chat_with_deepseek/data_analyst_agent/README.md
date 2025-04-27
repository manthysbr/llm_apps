# HeraCorps Data Analyst Agent

## 🚀 Visão Geral  
Este agente de análise de dados interativo combina Python, Streamlit e LLMs locais para permitir que usuários não‑técnicos gerem consultas SQL a partir de descrições em linguagem natural, executem as consultas em memória (DuckDB) e explorem resultados em tempo real. Foi idealizado como um protótipo de pesquisa para demonstrar como agentes de IA podem acelerar a análise de dados exploratória.


## 🛠 Componentes Principais  

1. **Interface Streamlit**  
   - Upload de datasets CSV/XLSX  
   - Preview interativo de amostras e metadados  
   - Input de perguntas em linguagem natural  

2. **Módulo de IA**  
   - **Ollama (deepseek‑r1:14b)** como LLM on‑premise  
   - **LangChain**  
     - `ChatPromptTemplate` para estruturar system + user prompt  
     - `StrOutputParser` para extrair saída textual  
   - Regex para identificar e exibir blocos de “pensamento” (`<think>…</think>`)

3. **Pipelines de Dados**  
   - **Pandas** para carregamento e pré‑processamento básico (conversão de datas)  
   - **DuckDB** para execução em memória de queries SQL geradas  
   - Exibição dos resultados em tabelas no front‑end Streamlit  

## 🔍 Fluxo de Funcionamento  

1. Usuário faz upload de um arquivo `.csv` ou `.xlsx`.  
2. O agente pré‑processa colunas de data e registra o DataFrame em DuckDB.  
3. Usuário descreve o que deseja analisar (ex.: “Top 5 vendas por categoria”).  
4. O LLM recebe:
   - Informações da tabela (nome, colunas, amostra)
   - Pergunta em linguagem natural  
5. O modelo:
   - Raciocina em etapas (pensamentos internos exibidos opcionalmente)  
   - Gera um bloco SQL encapsulado em markdown  
6. A API executa o SQL em DuckDB e retorna o DataFrame resultante.  
7. Resultados são exibidos em tempo real no Streamlit.

## 📦 Tecnologias & Bibliotecas  
- Python 3.8+  
- Streamlit – UI de chat/insights  
- Ollama / deepseek‑r1:14b – LLM local  
- LangChain – orquestração de prompts e parsing  
- Pandas – manipulação de dados  
- DuckDB – engine SQL in‑memory  
- Regex – extração de blocos de pensamento  

## 🚀 Como Executar  

```shell
pip install -r requirements.txt
streamlit run data_analyst.py
```

## 📈 Possíveis Extensões  
- Suporte a múltiplos formatos (Parquet, JSON, SQL Server)  
- Cache de prompts e resultados para consultas recorrentes  
- Integração com embeddings para recomendações de colunas  
- Orquestração de pipelines ETL diretamente pelo LLM  
- Adição de teste A/B para avaliar precisão das queries geradas  

---
Feito com ❤️ pela HeraCorps AI Division  
