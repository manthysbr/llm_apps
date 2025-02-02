import streamlit as st
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import re
from datetime import datetime

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

class TeachingAgent:
    def __init__(self, role):
        self.llm = Ollama(model="deepseek-r1:14b")
        self.role = role
    
    def generate_content(self, topic, context=""):
        prompts = {
            "Professor": """You are an expert professor.
            Create a comprehensive knowledge base for: {topic}
            
            Include:
            1. Core concepts and principles
            2. Advanced topics
            3. Practical applications
            4. Key terminology
            
            Previous context: {context}""",
            
            "Academic Advisor": """You are a learning path specialist.
            Design a structured roadmap for learning: {topic}
            
            Include:
            1. Progressive learning stages
            2. Time estimates
            3. Prerequisites
            4. Learning objectives
            
            Previous context: {context}""",
            
            "Research Librarian": """You are a research specialist.
            Curate learning resources for: {topic}
            
            Include:
            1. Online courses
            2. Books and documentation
            3. Video tutorials
            4. Practice platforms
            
            Previous context: {context}""",
            
            "Teaching Assistant": """You are an educational content creator.
            Design practice materials for: {topic}
            
            Include:
            1. Progressive exercises
            2. Practice projects
            3. Assessment questions
            4. Solution guides
            
            Previous context: {context}"""
        }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompts[self.role]),
            ("human", "Generate educational content")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        return chain.invoke({
            "topic": topic,
            "context": context
        })

# Initialize session state
if 'documents' not in st.session_state:
    st.session_state.documents = {}

st.title("HeraCorps Educational Team")
st.caption("Powered by DeepSeek")

# Topic input
topic = st.text_input("What would you like to learn?", 
                     placeholder="e.g., Machine Learning, Python, etc.")

if st.button("Generate Learning Materials"):
    # Initialize agents
    agents = {
        "Professor": TeachingAgent("Professor"),
        "Academic Advisor": TeachingAgent("Academic Advisor"),
        "Research Librarian": TeachingAgent("Research Librarian"),
        "Teaching Assistant": TeachingAgent("Teaching Assistant")
    }
    
    # Process with each agent
    for role, agent in agents.items():
        with st.spinner(f"{role} is working..."):
            response = agent.generate_content(
                topic,
                context=str(st.session_state.documents.get(topic, ""))
            )
            
            # Extract thinking process
            thinking = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
            
            # Create document section
            with st.expander(f"📚 {role}'s Materials", expanded=True):
                if thinking:
                    with st.expander("🧠 Thought Process"):
                        st.markdown(thinking.group(1).strip())
                    main_content = response.replace(f'<think>{thinking.group(1)}</think>', '').strip()
                else:
                    main_content = response
                
                st.markdown(main_content)
                
                # Save to local storage
                if topic not in st.session_state.documents:
                    st.session_state.documents[topic] = {}
                st.session_state.documents[topic][role] = main_content
                
                # Export option
                if st.button(f"Export {role}'s Content", key=f"export_{role}"):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{topic}_{role}_{timestamp}.md"
                    with open(filename, "w") as f:
                        f.write(f"# {topic} - {role}'s Materials\n\n")
                        f.write(main_content)
                    st.success(f"Exported to {filename}")

# Agent descriptions
st.markdown("---")
st.markdown("""
### 🤖 Meet Your Educational Team
- **Professor**: Creates comprehensive knowledge base
- **Academic Advisor**: Designs learning roadmap
- **Research Librarian**: Curates learning resources
- **Teaching Assistant**: Creates practice materials
""")

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered educational content generation made by @manthysbr")