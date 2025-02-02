import streamlit as st
import tempfile
import os
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
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

class LegalAgent:
    def __init__(self, role, knowledge_base=None):
        self.llm = Ollama(model="deepseek-r1:14b")
        self.role = role
        self.knowledge_base = knowledge_base
    
    def analyze(self, query, context):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a {role} analyzing legal documents.
            Use the following context to provide analysis:
            
            DOCUMENT CONTEXT:
            {context}
            
            QUERY:
            {query}
            
            Provide detailed analysis from your specialist perspective."""),
            ("human", "Analyze this legal matter")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        return chain.invoke({
            "role": self.role,
            "context": context,
            "query": query
        })

class LegalTeam:
    def __init__(self):
        self.researcher = LegalAgent("Legal Research Specialist")
        self.analyst = LegalAgent("Contract Analysis Specialist")
        self.strategist = LegalAgent("Legal Strategy Specialist")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
    def process_document(self, file):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            loader = PyPDFLoader(tmp_file.name)
            documents = loader.load()
            
            # Split documents
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = splitter.split_documents(documents)
            
            # Create vector store
            knowledge_base = FAISS.from_documents(texts, self.embeddings)
            
            os.unlink(tmp_file.name)
            return knowledge_base
    
    def analyze(self, query, knowledge_base, analysis_type):
        # Get relevant context
        docs = knowledge_base.similarity_search(query, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        responses = {
            "research": self.researcher.analyze(query, context),
            "contract": self.analyst.analyze(query, context),
            "strategy": self.strategist.analyze(query, context)
        }
        
        return responses

# Initialize session state
if 'legal_team' not in st.session_state:
    st.session_state.legal_team = LegalTeam()
if 'knowledge_base' not in st.session_state:
    st.session_state.knowledge_base = None

st.title("🤖 AI Legal Team")
st.caption("Powered by DeepSeek")

# Document upload
uploaded_file = st.file_uploader("Upload Legal Document", type=['pdf'])

if uploaded_file:
    with st.spinner("Processing document..."):
        st.session_state.knowledge_base = st.session_state.legal_team.process_document(uploaded_file)
        st.success("Document processed successfully!")

if st.session_state.knowledge_base:
    # Analysis options
    analysis_type = st.selectbox(
        "Analysis Type",
        ["Contract Review", "Legal Research", "Risk Assessment", "Custom Analysis"]
    )
    
    queries = {
        "Contract Review": "Review this contract and identify key terms, obligations, and risks.",
        "Legal Research": "Research relevant legal precedents and citations for this document.",
        "Risk Assessment": "Analyze potential legal risks and liabilities.",
        "Custom Analysis": None
    }
    
    if analysis_type == "Custom Analysis":
        query = st.text_area("Enter your analysis query:")
    else:
        query = queries[analysis_type]
    
    if st.button("🔍 Analyze"):
        with st.spinner("Analyzing document..."):
            responses = st.session_state.legal_team.analyze(
                query=query,
                knowledge_base=st.session_state.knowledge_base,
                analysis_type=analysis_type
            )
            
            # Display results
            tabs = st.tabs(["Research", "Contract Analysis", "Strategy"])
            
            for tab, (role, response) in zip(tabs, responses.items()):
                with tab:
                    # Extract thinking process
                    thinking = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
                    if thinking:
                        with st.expander("🧠 Analysis Process"):
                            st.markdown(thinking.group(1).strip())
                        main_response = response.replace(f'<think>{thinking.group(1)}</think>', '').strip()
                    else:
                        main_response = response
                    
                    st.markdown(main_response)
            
            # Summary
            with st.expander("📋 Summary", expanded=True):
                st.markdown("### Key Points")
                for role, response in responses.items():
                    st.markdown(f"**{role.title()}**")
                    st.markdown("- " + "\n- ".join(response.split("\n")[:3]))

else:
    st.info("Please upload a legal document to begin analysis")

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered legal team simulation made by @manthysbr")
st.caption("⚠️ Not a substitute for professional legal advice")