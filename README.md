

> [!TIP]
> 🤖 Uma coleção de agentes de IA potencializados por modelos open-source, com Ollama.

# Agentes e Prototipagem de IA

Esse repo é fruto de uma série de estudos e experimentos com **Agentes de IA**. Minha intenção é criar protótipos de agentes que utilizam llms e slms, como o `deepseek-r1:14b` (entre outros), para resolver problemas específicos em diferentes domínios.

Tudo isso roda localmente, utilizando o **Ollama** como backend para os LLMs. A ideia é explorar como esses agentes podem ser orquestrados para realizar tarefas complexas, utilizando diversos frameworks que facilitam a integração com LLMs de modo geral. 

### 🎮 Agente de apoio a equipe de desenvolvimento de jogos
Orquestra quatro sub-agentes especializados para criar um prototipo para um GDD (Game Design Document) inicial:
- **Agente de História**: Cria trama, personagens, arcos narrativos e lore.
- **Agente de Gameplay**: Descreve loops centrais, progressão e sistemas de interação.
- **Agente Visual**: Define guia de arte, paleta de cores, estilo de animação e som.
- **Agente Técnico**: Recomenda motores de jogo, arquitetura, marcos e otimizações.

### 📊 Agente Data Analysis
Interface interativa que permite gerar e executar consultas SQL em datasets (CSV/XLSX) usando linguagem natural:
- Faz upload e pré-processamento básico dos dados (ex: colunas de data).
- Utiliza LangChain e Ollama para entender a pergunta do usuário e gerar uma consulta SQL.
- Executa a consulta em memória usando DuckDB e exibe os resultados.
- Mostra o "processo de pensamento" do LLM para gerar o SQL.

### 🤝 Agente de CS
Simula um chatbot de suporte com memória e contexto por usuário:
- Gera perfis de clientes sintéticos em JSON para simulação.
- Utiliza FAISS (vector store) para armazenar e recuperar o histórico de interações do cliente, fornecendo contexto ao LLM.
- Mantém o histórico da conversa atual na sessão do Streamlit.

### 📚 Agente Jurídico de IA
Oferece dois protótipos para análise de documentos jurídicos:
1.  **Equipe Jurídica de IA**: Orquestra três sub-agentes (Pesquisa, Contratos, Estratégia) para analisar um documento PDF sob múltiplas perspectivas.
2.  **Assistente Jurídico Brasileiro**: Implementa um pipeline RAG completo: upload de PDF, OCR (fallback), divisão de texto, vetorização (FAISS), recuperação de contexto e resposta a perguntas sobre o documento.

### 💪 Agente `Planner` de Saúde e Fitness
Gera planos personalizados de treino e nutrição com base nas informações do usuário:
- Coleta dados como idade, peso, altura, nível de atividade, objetivos e preferências.
- Calcula IMC e sugere métricas de acompanhamento (calorias, dias de treino).
- Cria rotinas de exercícios detalhadas e sugestões de refeições.
- Exibe o raciocínio científico do LLM em blocos `<think>…</think>`.

### 📈 Agente de Equipe Financeira
Conjunto de dois agentes focados em finanças pessoais e de mercado:
1.  **Analista Financeiro**: Coleta dados de ações (usando `yfinance`), notícias (via web scraping com DuckDuckGo/BeautifulSoup) e fornece uma análise baseada em uma consulta do usuário.
2.  **Rastreador Financeiro**: Permite registrar despesas (manualmente ou via upload de PDF), vetoriza as descrições usando embeddings e armazena em Qdrant (vector store). Possibilita consultas em linguagem natural sobre os gastos e gera insights.

### 🤖 Agente RAG (Geração Aumentada por Recuperação)
Permite conversar sobre o conteúdo de documentos PDF carregados:
- Processa PDFs: carrega, divide em chunks, gera embeddings (vetores) e indexa no FAISS.
- Quando o usuário faz uma pergunta, busca os trechos mais relevantes (busca semântica) no FAISS.
- Envia a pergunta e os trechos relevantes como contexto para o LLM gerar uma resposta fundamentada.
- Exibe a resposta, as fontes (trechos dos documentos) e o raciocínio interno do LLM.

### 🎓 Agente de Equipe Educacional
Pipeline multi-agente para criar materiais de estudo sobre um tópico específico:
- **Professor**: Cria uma base de conhecimento abrangente sobre o tópico.
- **Orientador Acadêmico**: Desenha um roteiro de aprendizagem estruturado.
- **Bibliotecário de Pesquisa**: Faz a curadoria de recursos de estudo relevantes com webscrapping (artigos, vídeos, etc.).
- **Assistente de Ensino**: Cria materiais práticos, como exercícios e exemplos.
- Permite exportar o conteúdo gerado por cada agente para arquivos Markdown.

Alguns outros estudos que venho fazendo em `advanced_stuff`:

- ⛴️ Um agente que valida templates Helm, verificando sintaxe, segurança e boas práticas usando um esquema de multiagente. O sistema utiliza LLMs locais via Ollama e é orquestrado com a framework AutoGen (AG2). A validação vai além do `helm lint` e `kubeval`, abordando aspectos de segurança, otimização de recursos e boas práticas. A interface é construída com Streamlit, permitindo upload de templates e visualização de resultados.

- 🧠 Um sistema multiagente que simula um fluxo de apoio inicial à saúde mental, utilizando LLMs locais via Ollama e a framework AutoGen (AG2). O sistema orquestra três agentes especializados (Avaliação, Ação, Acompanhamento) para gerar um plano de apoio preliminar baseado nas informações do usuário. A interface é construída com Streamlit, permitindo a coleta de dados e a visualização dos resultados.


