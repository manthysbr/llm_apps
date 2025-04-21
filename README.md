> [!TIP]
> 🤖 A collection of AI agents powered by open-source models, with Ollama

HeraCorps is a mock enterprise created by me, in order to demonstrate the capabilities of llms in automating various business functions through specialized AI agents. Some of them are just for fun/experimentation but the idea is in the code.

This is just for study purposes, so be free to use the code elsewhere!

## 🌟 Features

Each agent is designed to handle specific business operations:

### 🎮 Game Development Division
- Story & narrative design
- Gameplay mechanics
- Visual aesthetics
- Technical architecture planning

### 📊 Data Analytics Department
- SQL query generation
- Data visualization
- Business intelligence
- Pattern analysis

### 🎲 RPG Lore Generator
- Character creation
- Story progression
- Interactive gameplay
- Dice rolling system

### 📚 Legal Department
- Document analysis
- Contract review
- Legal research
- Risk assessment

### 💪 Health & Fitness Division
- Personalized workout plans
- Nutrition guidance
- Progress tracking
- Health metrics analysis

### 📈 Financial Analysis Team
- Stock analysis
- Market research
- Investment strategies
- Financial reporting
- Finance Self Manager ( manage your bills )

### 🎓 Educational Division
- Course content creation
- Learning path design
- Resource curation
- Assessment generation

### 🤝 Customer Success Team
- Support ticket handling
- Customer profile management
- Query resolution
- Interaction history tracking

## 🚀 Getting Started

1. Clone the repository:
```bash
git clone https://github.com/manthysbr/llm_apps.git
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Ollama and pull Deepseek model:
```bash
curl https://ollama.ai/install.sh | sh
ollama pull deepseek-r1:14b
```

4. Run any agent:
```bash
streamlit run models/chat_with_deepseek/[agent_folder]/[agent_file].py
```

## 🛠️ Architecture

- **Frontend**: Streamlit
- **LLM Engine**: Deepseek R1 (via Ollama)
- **Embeddings**: HuggingFace sentence-transformers
- **Vector Store**: FAISS or QDRANT ( it will depend on the agent ) 
- **Framework**: LangChain

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
---
Made with ❤️ by HeraCorps AI Division
