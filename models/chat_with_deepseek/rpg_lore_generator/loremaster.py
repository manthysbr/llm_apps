import streamlit as st
import time
import json
import random
import re
import os
from pathlib import Path
from datetime import datetime
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


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
        self.memory = FAISS.from_texts(["Campaign begins."], self.embeddings)
        self.difficulty_levels = {
            "Very Easy": 5,
            "Easy": 10,
            "Medium": 15,
            "Hard": 20,
            "Very Hard": 25
        }
        self.history_path = Path.cwd() / "rpg_history"  # Changed to current working directory
        self.history_path.mkdir(exist_ok=True)
        self.progress = {
            "major_events": [],
            "current_quest": None,
            "completed_quests": [],
            "story_progress": 0,
            "last_location": "",
            "known_npcs": []
        }

    def save_history(self, character_name: str, story_log: list):
        filename = self.history_path / f"{character_name.lower().replace(' ', '_')}_history.json"
        history = {
            "character": character_name,
            "timestamp": datetime.now().isoformat(),
            "story_log": story_log,
            "progress": self.progress  # Include progress data
        }
        with open(filename, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_history(self, character_name: str) -> list:
        filename = self.history_path / f"{character_name.lower().replace(' ', '_')}_history.json"
        if filename.exists():
            with open(filename) as f:
                history = json.load(f)
                self.progress = history.get("progress", self.progress)
                return history.get("story_log", [])
        return []

    def filter_think_content(self, text: str) -> str:
        """Remove content between <think> tags"""
        return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    
    def generate_character(self, name: str, race: str, class_type: str) -> str:
        """Generate character profile and backstory"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Create a character profile for a fantasy RPG character.
            Include:
            - Brief backstory
            - Personality traits
            - Notable skills
            - Distinctive features
            
            CHARACTER INFO:
            Name: {name}
            Race: {race}
            Class: {class_type}
            
            Use <think> tags for your reasoning, which will be hidden.
            Format the response in Markdown.""")
        ])
        
        try:
            chain = (prompt | self.llm | StrOutputParser())
            response = chain.invoke({
                "name": name,
                "race": race,
                "class_type": class_type
            })
            
            # Filter out think content
            return self.filter_think_content(response)
            
        except Exception as e:
            return f"""
            **{name}**
            A mysterious {race} {class_type}.
            *Character details will be revealed as the story unfolds...*
            """

    def interpret_roll(self, roll: int, difficulty: str) -> dict:
        """Interpret d20 roll results based on difficulty"""
        dc = self.difficulty_levels[difficulty]
        success = roll >= dc
        
        if roll == 20:
            outcome = "Critical Success!"
        elif roll == 1:
            outcome = "Critical Failure!"
        elif success:
            outcome = "Success"
        else:
            outcome = "Failure"
        
        return {
            "roll": roll,
            "dc": dc,
            "difficulty": difficulty,
            "success": success,
            "outcome": outcome
        }

    def roll_dice(self, dice_type: str, difficulty: str = "Medium") -> dict:
        sides = int(dice_type.replace('d', ''))
        roll = random.randint(1, sides)
        
        if dice_type == "d20":
            return self.interpret_roll(roll, difficulty)
        return {"roll": roll, "type": dice_type}

    def generate_lore(self, context: str, player_action: str, roll_result: dict = None) -> str:
        roll_context = ""
        if roll_result:
            if "outcome" in roll_result:
                roll_context = f"""
                DICE CHECK RESULT:
                Roll: d20 - {roll_result['roll']}
                Difficulty: {roll_result['difficulty']} (DC {roll_result['dc']})
                Outcome: {roll_result['outcome']}
                """
            else:
                roll_context = f"DICE ROLL: {roll_result['type']} - {roll_result['roll']}"

        progress_context = f"""
        CURRENT PROGRESS:
        Quest: {self.progress['current_quest'] or 'No active quest'}
        Location: {self.progress['last_location'] or 'Unknown'}
        Recent Events: {', '.join(self.progress['major_events'][-3:]) if self.progress['major_events'] else 'None'}
        Known NPCs: {', '.join(self.progress['known_npcs'][-3:]) if self.progress['known_npcs'] else 'None'}
        Story Progress: {self.progress['story_progress']}%
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a master storyteller and game master.
            Using the context, progress, and player action, continue the story.
            
            PREVIOUS CONTEXT:
            {context}
            
            {progress_context}
            
            PLAYER ACTION:
            {action}
            
            {roll_context}
            
            Use <think> tags for progress updates:
            <think>
            PROGRESS UPDATE:
            - Quest: [current quest name or None]
            - Location: [current location]
            - Event: [major event if significant]
            - NPCs: [new NPCs encountered]
            - Progress: [0-100]
            </think>
            
            [Story continuation]""")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        response = chain.invoke({
            "context": context,
            "progress_context": progress_context,
            "action": player_action,
            "roll_context": roll_context
        })

        think_match = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
        if think_match:
            think_content = think_match.group(1)
            
            # Update quest
            quest_match = re.search(r'Quest: (.*?)(?:\n|$)', think_content)
            if quest_match and quest_match.group(1).strip() not in ['None', '[current quest name or None]']:
                if self.progress['current_quest']:
                    self.progress['completed_quests'].append(self.progress['current_quest'])
                self.progress['current_quest'] = quest_match.group(1).strip()
            
            # Update location
            loc_match = re.search(r'Location: (.*?)(?:\n|$)', think_content)
            if loc_match and loc_match.group(1).strip() not in ['[current location]']:
                self.progress['last_location'] = loc_match.group(1).strip()
            
            # Update events
            event_match = re.search(r'Event: (.*?)(?:\n|$)', think_content)
            if event_match and event_match.group(1).strip() not in ['[major event if significant]']:
                self.progress['major_events'].append(event_match.group(1).strip())
            
            # Update NPCs
            npc_match = re.search(r'NPCs: (.*?)(?:\n|$)', think_content)
            if npc_match and npc_match.group(1).strip() not in ['[new NPCs encountered]']:
                new_npcs = [npc.strip() for npc in npc_match.group(1).split(',')]
                self.progress['known_npcs'].extend(new_npcs)
            
            # Update progress percentage
            prog_match = re.search(r'Progress: (\d+)', think_content)
            if prog_match:
                self.progress['story_progress'] = min(100, int(prog_match.group(1)))
        
        # Filter out think content and store in memory
        filtered_response = self.filter_think_content(response)
        self.memory.add_texts([player_action, filtered_response])
        
        return filtered_response

# Initialize session state
if 'rpg_agent' not in st.session_state:
    st.session_state.rpg_agent = RPGAgent()
if 'character' not in st.session_state:
    st.session_state.character = None
if 'story_log' not in st.session_state:
    st.session_state.story_log = []
if 'last_roll' not in st.session_state:
    st.session_state.last_roll = None

st.title("🎲 Save the Kingdom - IA RPG")
st.caption("Interactive Storytelling & Character Management")

# Sidebar for character creation
with st.sidebar:
    st.header("⚔️ Character Creation")
    char_name = st.text_input("Character Name", key="char_name")
    char_race = st.selectbox("Race", ["Human", "Elf", "Dwarf", "Halfling", "Orc"])
    char_class = st.selectbox("Class", ["Warrior", "Mage", "Rogue", "Cleric", "Ranger"])
    
    if st.button("🎭 Generate Character"):
        if st.session_state.character:
            if st.sidebar.checkbox("⚠️ Creating a new character will reset current game. Continue?"):
                # Save current history
                if st.session_state.character["name"]:
                    st.session_state.rpg_agent.save_history(
                        st.session_state.character["name"],
                        st.session_state.story_log
                    )
                # Reset game state
                st.session_state.story_log = []
                st.session_state.last_roll = None
                st.session_state.rpg_agent.memory = FAISS.from_texts(
                    ["Campaign begins."], 
                    st.session_state.rpg_agent.embeddings
                )
        
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
            
            # Load previous history if exists
            previous_log = st.session_state.rpg_agent.load_history(char_name)
            if previous_log:
                st.sidebar.info("📜 Found previous adventures for this character!")
                if st.sidebar.button("Load Previous History"):
                    st.session_state.story_log = previous_log
    
    # Add separator
    st.markdown("---")
    
    # Dice roller in sidebar
    st.header("🎲 Dice Roller")
    dice_type = st.selectbox("Select dice", ["d20", "d4", "d6", "d8", "d10", "d12", "d100"])
    if dice_type == "d20":
        difficulty = st.selectbox("Difficulty", list(st.session_state.rpg_agent.difficulty_levels.keys()))
    
    if st.button("Roll Dice"):
        result = st.session_state.rpg_agent.roll_dice(
            dice_type, 
            difficulty if dice_type == "d20" else "Medium"
        )
        if "outcome" in result:
            st.markdown(f"""
            <div class='dice-roll'>
                🎲 {result['roll']}<br>
                <small>{result['outcome']}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='dice-roll'>🎲 {result['roll']}</div>", unsafe_allow_html=True)
        st.session_state.last_roll = result

# Main game interface
if st.session_state.character:
    # Display character sheet
    with st.expander("📜 Character Sheet", expanded=False):
        st.markdown(f"### {st.session_state.character['name']}")
        st.markdown(f"**Race:** {st.session_state.character['race']}")
        st.markdown(f"**Class:** {st.session_state.character['class']}")
        st.markdown("---")
        st.markdown(st.session_state.character['profile'])
    
    st.header("📊 Story Progress")
    col1, col2 = st.columns([2,1])
    
    with col1:
        progress = st.session_state.rpg_agent.progress
        st.markdown(f"**Current Quest:** {progress['current_quest'] or 'No active quest'}")
        st.markdown(f"**Location:** {progress['last_location'] or 'Unknown'}")
        
        if progress['major_events']:
            st.markdown("**Recent Events:**")
            for event in progress['major_events'][-3:]:
                st.markdown(f"⚔️ {event}")
        
        if progress['known_npcs']:
            st.markdown("**Known NPCs:**")
            for npc in progress['known_npcs'][-3:]:
                st.markdown(f"👤 {npc}")
    
    with col2:
        st.progress(progress['story_progress'] / 100)
        st.caption(f"Story Progress: {progress['story_progress']}%")
        st.caption(f"Completed Quests: {len(progress['completed_quests'])}")

    st.markdown("---")
    
    # Story interaction
    st.header("📖 Story Progression")
    
    for entry in st.session_state.story_log:
        st.markdown(f"<div class='story-block'>{entry}</div>", unsafe_allow_html=True)
    
    player_action = st.text_area("What do you do?", height=100)
    
    col1, col2 = st.columns([4,1])
    with col1:
        if st.button("⚡ Take Action", use_container_width=True):
            if player_action.strip():
                with st.spinner("The story unfolds..."):
                    recent_docs = st.session_state.rpg_agent.memory.similarity_search(
                        player_action, k=3
                    )
                    context = "\n".join([doc.page_content for doc in recent_docs])
                    
                    roll_result = st.session_state.last_roll
                    response = st.session_state.rpg_agent.generate_lore(
                        context, 
                        player_action,
                        roll_result
                    )
                    
                    if roll_result and "outcome" in roll_result:
                        st.session_state.story_log.append(
                            f"**Roll:** 🎲 {roll_result['roll']} - {roll_result['outcome']}"
                        )
                    st.session_state.story_log.append(f"**You:** {player_action}")
                    st.session_state.story_log.append(f"**Story:** {response}")
                    
                    st.session_state.last_roll = None
                    st.rerun()
    
    with col2:
        if st.button("💾 Save Game", use_container_width=True):
            st.session_state.rpg_agent.save_history(
                st.session_state.character["name"],
                st.session_state.story_log
            )
            st.success("Game saved!")

else:
    st.info("👈 Create your character to begin the adventure!")

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered RPG text game made by @manthysbr")