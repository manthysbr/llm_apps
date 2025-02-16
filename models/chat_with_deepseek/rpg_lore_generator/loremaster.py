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
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np
import fitz 


qdrant_client = QdrantClient(host="localhost", port=6333)

# Initialize Qdrant client
def initialize_qdrant_collections():
    """Initialize Qdrant collections if they don't exist"""
    try:
        for collection in ["lore_chunks", "story_memory"]:
            try:
                collections = qdrant_client.get_collections().collections
                collection_names = [c.name for c in collections]
                
                if collection not in collection_names:
                    qdrant_client.create_collection(
                        collection_name=collection,
                        vectors_config=models.VectorParams(
                            size=384, 
                            distance=models.Distance.COSINE
                        )
                    )
                    print(f"Created collection: {collection}")
            except Exception as e:
                print(f"Error with collection {collection}: {e}")
                # Try to recreate if there's an issue
                try:
                    qdrant_client.recreate_collection(
                        collection_name=collection,
                        vectors_config=models.VectorParams(
                            size=384,
                            distance=models.Distance.COSINE
                        )
                    )
                    print(f"Recreated collection: {collection}")
                except Exception as e:
                    print(f"Failed to recreate collection {collection}: {e}")
                    raise
    except Exception as e:
        print(f"Critical Qdrant initialization error: {e}")
        raise

# Init
initialize_qdrant_collections()

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
        self.qdrant = qdrant_client
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!"]
        )
        self.history_path = Path.cwd() / "rpg_history"
        self.history_path.mkdir(exist_ok=True)
        self.progress = {
            "major_events": [],
            "current_quest": None,
            "completed_quests": [],
            "story_progress": 0,
            "last_location": "",
            "known_npcs": []
        }
        self.difficulty_levels = {
            "Easy": 10,
            "Medium": 15,
            "Hard": 20,
            "Very Hard": 25,
            "Legendary": 30
        }
        # Initialize FAISS memory
        self._add_to_memory("Campaign begins.")


    def _add_to_memory(self, text: str):
        """Add text to story memory in Qdrant"""
        vector = self._get_embedding(text)
        self.qdrant.upsert(
            collection_name="story_memory",
            points=[models.PointStruct(
                id=int(datetime.now().timestamp() * 1000),
                vector=vector,
                payload={"content": text}
            )]
        )

    def get_recent_memory(self, query: str, k: int = 3) -> str:
        """Get recent relevant memory entries"""
        query_vector = self._get_embedding(query)
        results = self.qdrant.search(
            collection_name="story_memory",
            query_vector=query_vector,
            limit=k
        )
        return "\n".join([hit.payload["content"] for hit in results])


    def _get_embedding(self, text: str) -> list:
        """Get embedding for text using HuggingFace embeddings"""
        return self.embeddings.embed_query(text)

    def process_lore_pdf(self, pdf_content: bytes) -> dict:
        """Process PDF content and store in Qdrant"""
        # Extract text from PDF
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        
        # Split into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Store chunks in Qdrant
        for i, chunk in enumerate(chunks):
            vector = self._get_embedding(chunk)
            self.qdrant.upsert(
                collection_name="lore_chunks",
                points=[models.PointStruct(
                    id=int(datetime.now().timestamp() * 1000) + i,
                    vector=vector,
                    payload={"content": chunk}
                )]
            )
        
        return {
            "chunks": len(chunks),
            "preview": text[:500] + "..."
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

    def query_lore(self, query: str, limit: int = 3) -> list:
        """Query the lore database"""
        query_vector = self._get_embedding(query)
        
        search_result = self.qdrant.search(
            collection_name="lore_chunks",
            query_vector=query_vector,
            limit=limit
        )
        
        return [hit.payload["content"] for hit in search_result]

    def filter_think_content(self, text: str) -> str:
        """Remove content between <think> tags"""
        return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    
    def generate_character(self, name: str, race: str, class_type: str) -> str:
        """Generate character profile and backstory using available lore"""
        # Query lore for relevant background information
        lore_context = "\n\n".join(self.query_lore(f"{race} {class_type} background culture history"))
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Create a character profile for a fantasy RPG character using the provided lore.
            Use the lore context to tie the character's background to the world's history and culture.
            
            LORE CONTEXT:
            {lore_context}
            
            Include:
            - Brief backstory connected to the world's lore
            - Personality traits
            - Notable skills
            - Distinctive features
            - Cultural elements from their race/class background
            
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
                "class_type": class_type,
                "lore_context": lore_context
            })
            
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
        lore_context = "\n\n".join(self.query_lore(player_action))
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
            Using the context, lore, progress, and player action, continue the story.
            
            PREVIOUS CONTEXT:
            {context}
            
            LORE CONTEXT:
            {lore_context}
            
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
            "lore_context": lore_context,
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
if 'lore_uploaded' not in st.session_state:
    st.session_state.lore_uploaded = False
if 'trigger_action' not in st.session_state:
    st.session_state.trigger_action = False
if 'current_action' not in st.session_state:
    st.session_state.current_action = ""
if 'lore_processed' not in st.session_state:
    st.session_state.lore_processed = False

# Main title
st.title("🎲 Save the Kingdom - IA RPG")
st.caption("Interactive Storytelling & Character Management")

# Sidebar UI
with st.sidebar:
    if not st.session_state.lore_processed:  # Change condition from lore_uploaded
        st.header("📚 Upload World Lore")
        st.info("⚠️ You must upload a fantasy book (PDF) to begin the adventure!")
        uploaded_file = st.file_uploader("Upload Fantasy Book (PDF)", type="pdf")
        if uploaded_file:
            with st.spinner("Processing world lore..."):
                try:
                    result = st.session_state.rpg_agent.process_lore_pdf(uploaded_file.read())
                    st.success(f"Processed {result['chunks']} lore chunks!")
                    st.session_state.lore_uploaded = True
                    st.session_state.lore_processed = True  # Set processed state
                    with st.expander("World Preview"):
                        st.markdown(f"<div class='story-block'>{result['preview']}</div>", 
                                  unsafe_allow_html=True)
                    st.rerun()  # Force UI update
                except Exception as e:
                    st.error(f"Error processing lore: {e}")
                    st.session_state.lore_uploaded = False
                    st.session_state.lore_processed = False
    
    elif not st.session_state.character:
        st.header("⚔️ Character Creation")
        st.info("Create your character using the world's lore")
        
        char_name = st.text_input("Character Name", key="char_name")
        char_race = st.selectbox("Race", ["Human", "Elf", "Dwarf", "Halfling", "Orc"])
        char_class = st.selectbox("Class", ["Warrior", "Mage", "Rogue", "Cleric", "Ranger"])
        
        if st.button("🎭 Generate Character", disabled=not char_name):
            with st.spinner("Creating character from world lore..."):
                profile = st.session_state.rpg_agent.generate_character(
                    char_name, char_race, char_class
                )
                st.session_state.character = {
                    "name": char_name,
                    "race": char_race,
                    "class": char_class,
                    "profile": profile
                }
                
                # Check for previous adventures
                previous_log = st.session_state.rpg_agent.load_history(char_name)
                if previous_log:
                    st.info("📜 Found previous adventures!")
                    if st.button("Load Previous History"):
                        st.session_state.story_log = previous_log
                        st.rerun()
    
    else:
        # Game Controls
        st.header("🎮 Game Controls")
        
        # Dice Roller
        st.subheader("🎲 Dice Roller")
        dice_type = st.selectbox("Select dice", ["d20", "d4", "d6", "d8", "d10", "d12", "d100"])
        
        if dice_type == "d20":
            difficulty = st.selectbox("Difficulty", 
                                   list(st.session_state.rpg_agent.difficulty_levels.keys()))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎲 Roll", use_container_width=True):
                result = st.session_state.rpg_agent.roll_dice(
                    dice_type, 
                    difficulty if dice_type == "d20" else "Medium"
                )
                st.session_state.last_roll = result
                st.session_state.trigger_action = True  # Auto-trigger action
                
                if "outcome" in result:
                    st.markdown(f"""
                    <div class='dice-roll'>
                        🎲 {result['roll']}<br>
                        <small>{result['outcome']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='dice-roll'>🎲 {result['roll']}</div>", 
                              unsafe_allow_html=True)
        
        with col2:
            if st.button("💾 Save", use_container_width=True):
                st.session_state.rpg_agent.save_history(
                    st.session_state.character["name"],
                    st.session_state.story_log
                )
                st.success("Saved!")
        
        # Quick Lore Search
        st.subheader("📚 Quick Lore")
        lore_query = st.text_input("Search world lore...")
        if lore_query:
            results = st.session_state.rpg_agent.query_lore(lore_query)
            for result in results:
                st.markdown(f"<div class='story-block'>{result}</div>", 
                          unsafe_allow_html=True)

# Main game area
if st.session_state.character:
    # Character Sheet
    with st.expander("📜 Character Sheet", expanded=False):
        st.markdown(f"### {st.session_state.character['name']}")
        st.markdown(f"**Race:** {st.session_state.character['race']}")
        st.markdown(f"**Class:** {st.session_state.character['class']}")
        st.markdown("---")
        st.markdown(st.session_state.character['profile'])
    
    # Story Progress
    progress = st.session_state.rpg_agent.progress
    col1, col2 = st.columns([3,1])
    
    with col1:
        st.header("📖 Adventure Status")
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
        st.metric("Story Progress", f"{progress['story_progress']}%")
        st.metric("Completed Quests", len(progress['completed_quests']))
        st.progress(progress['story_progress'] / 100)
    
    st.markdown("---")
    
    # Story Display
    st.header("📜 Story")
    for entry in st.session_state.story_log:
        st.markdown(f"<div class='story-block'>{entry}</div>", unsafe_allow_html=True)
    
    # Action Input
    player_action = st.text_area("What do you do?", height=100, key="current_action")
    
    if st.button("⚡ Take Action", use_container_width=True) or st.session_state.trigger_action:
        if player_action.strip():
            with st.spinner("The story unfolds..."):
                context = st.session_state.rpg_agent.get_recent_memory(player_action)
                roll_result = st.session_state.last_roll
                response = st.session_state.rpg_agent.generate_lore(
                    context, 
                    player_action,
                    roll_result
                )
                
                # Add entries to memory
                if roll_result and "outcome" in roll_result:
                    roll_entry = f"**Roll:** 🎲 {roll_result['roll']} - {roll_result['outcome']}"
                    st.session_state.rpg_agent._add_to_memory(roll_entry)
                    st.session_state.story_log.append(roll_entry)
                
                action_entry = f"**You:** {player_action}"
                story_entry = f"**Story:** {response}"
                
                st.session_state.rpg_agent._add_to_memory(action_entry)
                st.session_state.rpg_agent._add_to_memory(story_entry)
                
                st.session_state.story_log.append(action_entry)
                st.session_state.story_log.append(story_entry)
                
                # Reset states
                st.session_state.last_roll = None
                st.session_state.trigger_action = False
                st.rerun()

else:
    if not st.session_state.lore_uploaded:
        st.warning("👈 First, upload a fantasy book (PDF) to create the game world!")
    else:
        st.info("👈 Create your character to begin the adventure!")

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered RPG text game made by @manthysbr")