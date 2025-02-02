import streamlit as st
import time
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re

# Dark theme styling
st.markdown("""
    <style>
    .stApp {
        background-color: #1E1E1E;
        color: #00FF00;
    }
    [data-testid="stHeader"] {
        background-color: #000000;
    }
    .stButton>button {
        background-color: #004400;
        color: #00FF00;
        border: 1px solid #00FF00;
    }
    .sql-block {
        background-color: #002200;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #00FF00;
        font-family: monospace;
    }
    .result-block {
        background-color: #001100;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("HeraCorps Game Design Team")

# Info about the team
st.info("""
**HeraCorps developed your AI Game Design Team:**
🎭 Story Agent - Narrative & World Building
🎮 Gameplay Agent - Mechanics & Systems
🎨 Visuals Agent - Art & Sound
⚙️ Tech Agent - Technical Architecture
""")

# Game inputs
st.subheader("Game Details")
col1, col2 = st.columns(2)

with col1:
    background = st.text_input("Background/Setting", "A bastard prince and a magical sword")
    game_type = st.selectbox("Game Type", ["RPG", "Action", "Strategy", "Horror"])
    target_audience = st.selectbox("Target Audience", ["Kids", "Teens", "Adults", "All Ages"])

with col2:
    art_style = st.selectbox("Art Style", ["Realistic", "Cartoon", "Pixel Art", "Stylized"])
    platforms = st.multiselect("Platforms", ["PC", "Mobile", "Console", "Web"])
    multiplayer = st.checkbox("Multiplatform/Multiplayer Support")

# Configure LLM
llm = Ollama(model="deepseek-r1:14b")

if st.button("🎯 Game Concept"):
    # Prepare game data
    game_data = {
        "background": background,
        "type": game_type,
        "audience": target_audience,
        "art_style": art_style,
        "platforms": platforms,
        "multiplayer": multiplayer
    }

    # Agent prompts
    agents = {
        "story": """You are a narrative designer creating a game story.
        Based on the game data: {game_data}
        
        Provide:
        1. Main storyline, with detailed plot points
        2. Character profiles, relationships and arcs
        3. World building elements and lore
        4. Narrative progression, twists and endings
        
        IMPORTANT: Use gaming industry terminology and creative writing expertise.""",
        
        "gameplay": """You are a expert gameplay designer creating game mechanics.
        Based on the game data: {game_data}
        
        Design:
        1. Core gameplay loops, objectives and challenges
        2. Player progression systems
        3. Game systems and mechanics
        4. Combat/interaction mechanics/controls
        
        Use technical game design terminology.""",
        
        "visuals": """You are an art director designing the game's look.
        Based on the game data: {game_data}
        
        Define:
        1. Visual style guide, color palette and mood
        2. Character aesthetics and animations
        3. Environment design and level aesthetics
        4. UI/UX approach and sound design
        
        IMPORTANT: Use visual design terminology.""",
        
        "tech": """You are a technical director planning implementation.
        Based on the game data: {game_data}
        
        Specify:
        1. Engine recommendations and tools
        2. Technical requirements and constraints
        3. Development roadmap and milestones
        4. Performance considerations and optimization
        
        IMPORTANT: Use game development terminology."""
    }

    # Process each agent
    for role, prompt_template in agents.items():
        with st.spinner(f"🤖 {role.title()} Agent is working..."):
            prompt = ChatPromptTemplate.from_messages([
                ("system", prompt_template),
                ("human", "Generate your specialized analysis for this game concept.")
            ])
            
            chain = (prompt | llm | StrOutputParser())
            response = chain.invoke({"game_data": str(game_data)})
            
            # Extract thinking process
            thinking = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
            if thinking:
                with st.expander(f"🧠 {role.title()} Thought Process", expanded=True):
                    st.markdown(thinking.group(1).strip())
                main_response = response.replace(f'<think>{thinking.group(1)}</think>', '').strip()
            else:
                main_response = response
            
            # Display results
            with st.expander(f"📋 {role.title()} Design Document", expanded=True):
                st.markdown(main_response)

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered gdd team simulation made by @manthysbr")