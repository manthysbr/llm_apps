# HeraCorps Game Design Team Agent

## 🚀 Visão Geral  
Este protótipo demonstra como orquestrar múltiplos **agentes de IA** especializados em um pipeline de design de jogos, usando Python e LLMs locais. Cada sub‑agente (Story, Gameplay, Visuals, Tech) recebe um mesmo contexto de jogo e retorna saídas focadas em diferentes disciplinas de desenvolvimento.

## 🏗 Arquitetura & Fluxo de Dados  
1. **Front‑end (Streamlit)**  
   - Captura parâmetros do jogo: ambientação, gênero, público, estilo visual, plataformas e suporte multiplayer.  
   - Apresenta saídas em expansores interativos para cada sub‑agente.  
2. **Motor de IA (Ollama + deepseek‑r1:14b)**  
   - Reutiliza um único LLM local via LangChain (`ChatPromptTemplate` + `StrOutputParser`).  
   - Quatro prompts de sistema distintos, um para cada disciplina de design.  
3. **Extração de “Pensamentos”**  
   - O conteúdo `<think>…</think>` é identificado por expressão regular e exibido opcionalmente para pesquisa de **interpretablidade**.

```
User Input ──► Streamlit UI ──► { story, gameplay, visuals, tech } Prompts ──► LLM ──► Responses + Thought Extract  
                                                                                     │  
                                                                                     └─► Display Markdown
```

## 🔍 Componentes Principais  
- **Story Agent**: cria trama, personagens, arcos e lore.  
- **Gameplay Agent**: descreve loops centrais, progressão e sistemas de interação.  
- **Visuals Agent**: define guia de arte, paleta de cores, animações e som.  
- **Tech Agent**: recomenda motores, arquitetura, milestones e otimizações.  

Cada agente:
1. Recebe o mesmo `game_data` em JSON  
2. Utiliza `ChatPromptTemplate.from_messages()` para estruturar o prompt  
3. Passa pelo pipeline `(prompt | llm | StrOutputParser())`  
4. Processa e exibe o output puro e o bloco de pensamento.

## 📦 Tecnologias & Bibliotecas  
- Python 3.8+  
- Streamlit — Interface interativa de pesquisa  
- Ollama (`deepseek‑r1:14b`) — LLM on‑premise  
- LangChain — Orquestração de prompts e parsing de saída  
- Regex — Extração de blocos de raciocínio (`<think>…</think>`)  

## ⚡️ Como Executar  
```bash
cd /home/gohan/llm_apps/models/chat_with_deepseek/game_development_agent
pip install -r requirements.txt
streamlit run game_development.py
```

## 🔭 Extensões Futuras  
- Experimentar **function calling** para gerar assets (e.g., comandos para motores Unity/Unreal).  
- Conectar pipelines de geração de storyboard, protótipos de mecânicas e assets via APIs de automação.  
- Avaliar métricas de coerência entre agentes e introduzir feedback loop multi‑agent.  
- Integrar embeddings para busca semântica de ideias e assets reutilizáveis.

---
Feito com ❤️ pela HeraCorps AI Division  