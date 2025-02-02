import streamlit as st
import time
import json
import random
from datetime import datetime
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
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
    .story-block {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #00FF00;
        background-color: #0A2A0A;
    }
    .character-sheet {
        padding: 1rem;
        border: 2px solid #00FF00;
        border-radius: 0.5rem;
        background-color: #0A2A0A;
    }
    .dice-roll {
        font-size: 1.5rem;
        font-weight: bold;
        color: #00FF00;
    }
    </style>
""", unsafe_allow_html=True)

class RPGAgent:
    def __init__(self):
        self.llm = Ollama(model="deepseek-r1:14b")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        # Initialize memory store
        self.memory = FAISS.from_texts(
            ["Campaign begins."],
            self.embeddings
        )
        
    def roll_dice(self, dice_type: str) -> int:
        """Simulate dice rolls (d4, d6, d8, d10, d12, d20, d100)"""
        sides = int(dice_type.replace('d', ''))
        return random.randint(1, sides)
    
    def generate_character(self, name: str, race: str, class_type: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a character creation expert for fantasy RPGs.
            Create a detailed character profile including:
            1. Background story
            2. Personality traits
            3. Basic statistics (HP, MP, etc.)
            4. Special abilities
            5. Starting equipment
            
            CHARACTER DETAILS:
            Name: {name}
            Race: {race}
            Class: {class_type}
            
            Provide the profile in a well-formatted markdown structure."""),
            ("human", "Generate character profile")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        return chain.invoke({
            "name": name,
            "race": race,
            "class_type": class_type
        })
    
    def generate_lore(self, context: str, player_action: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a master storyteller and game master.
            Using the context and player action, continue the story in an engaging way.
            
            PREVIOUS CONTEXT:
            {context}
            
            PLAYER ACTION:
            {action}
            
            Create a rich narrative response that:
            1. Acknowledges the player's action
            2. Advances the story
            3. Provides new choices or challenges
            4. Maintains consistency with previous events
            
            End with 2-3 possible action choices for the player."""),
            ("human", "Continue the story")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        response = chain.invoke({
            "context": context,
            "action": player_action
        })
        
        # Store in memory
        self.memory.add_texts([player_action, response])
        
        return response

# Initialize session state
if 'rpg_agent' not in st.session_state:
    st.session_state.rpg_agent = RPGAgent()
if 'character' not in st.session_state:
    st.session_state.character = None
if 'story_log' not in st.session_state:
    st.session_state.story_log = []

st.title("🎲 AI RPG Lore Generator")
st.caption("Interactive Storytelling & Character Management")

# Sidebar for character creation
with st.sidebar:
    st.header("⚔️ Character Creation")
    char_name = st.text_input("Character Name", key="char_name")
    char_race = st.selectbox("Race", ["Human", "Elf", "Dwarf", "Halfling", "Orc"])
    char_class = st.selectbox("Class", ["Warrior", "Mage", "Rogue", "Cleric", "Ranger"])
    
    if st.button("🎭 Generate Character"):
        with st.spinner("Creating character..."):
            profile = st.session_state.rpg_agent.generate_character(
                char_name, char_race, char_class
            )
            st.session_state.character = {
                "name": char_name,
                "race": char_race,
                "class": char_class,
                "profile": profile
            }

# Main game interface
if st.session_state.character:
    # Display character sheet
    with st.expander("📜 Character Sheet", expanded=False):
        st.markdown(f"### {st.session_state.character['name']}")
        st.markdown(f"**Race:** {st.session_state.character['race']}")
        st.markdown(f"**Class:** {st.session_state.character['class']}")
        st.markdown("---")
        st.markdown(st.session_state.character['profile'])
    
    # Dice roller
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("🎲 Dice Roller")
        dice_type = st.selectbox("Select dice", ["d4", "d6", "d8", "d10", "d12", "d20", "d100"])
    with col2:
        if st.button("Roll"):
            result = st.session_state.rpg_agent.roll_dice(dice_type)
            st.markdown(f"<div class='dice-roll'>{result}</div>", unsafe_allow_html=True)
    
    # Story interaction
    st.header("📖 Story Progression")
    
    # Display story log
    for entry in st.session_state.story_log:
        st.markdown(f"<div class='story-block'>{entry}</div>", unsafe_allow_html=True)
    
    # Player input
    player_action = st.text_area("What do you do?", height=100)
    
    if st.button("⚡ Take Action"):
        if player_action.strip():
            with st.spinner("The story unfolds..."):
                # Get recent context
                recent_docs = st.session_state.rpg_agent.memory.similarity_search(
                    player_action, k=3
                )
                context = "\n".join([doc.page_content for doc in recent_docs])
                
                # Generate response
                response = st.session_state.rpg_agent.generate_lore(
                    context, player_action
                )
                
                # Update story log
                st.session_state.story_log.append(f"**You:** {player_action}")
                st.session_state.story_log.append(f"**Story:** {response}")
                
                # Rerun to update display
                st.rerun()

else:
    st.info("👈 Create your character to begin the adventure!")

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered RPG board game made by @manthysbr")