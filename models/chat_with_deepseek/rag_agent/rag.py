import streamlit as st
import os
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
import re
import time

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

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None

st.title("🤖 DeepSeek RAG Assistant")

# Configure components
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

llm = Ollama(model="deepseek-r1:14b")

# Document processing
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

# Document upload
uploaded_files = st.file_uploader("Upload Documents", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("Processing documents..."):
        documents = []
        for file in uploaded_files:
            temp_path = f"temp_{file.name}"
            with open(temp_path, "wb") as f:
                f.write(file.getvalue())
            
            loader = PyPDFLoader(temp_path)
            documents.extend(loader.load())
            os.remove(temp_path)
            
        # Split documents
        texts = text_splitter.split_documents(documents)
        
        # Create vector store
        st.session_state.vector_store = FAISS.from_documents(texts, embeddings)
        st.success("Documents processed successfully!")

# Chat interface
if st.session_state.vector_store:
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(msg["user"])
        with st.chat_message("assistant"):
            st.write(msg["assistant"])

    # Query input
    query = st.chat_input("Ask about your documents...")
    
    if query:
        with st.chat_message("user"):
            st.write(query)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Retrieve relevant documents
                docs = st.session_state.vector_store.similarity_search(query, k=3)
                context = "\n\n".join([doc.page_content for doc in docs])
                
                # Create prompt
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are a helpful AI assistant using DeepSeek.
                    Analyze the context and provide detailed answers.
                    
                    CONTEXT:
                    {context}
                    
                    Answer the user's question based on the context above.
                    If you're unsure, say so."""),
                    ("human", "{question}")
                ])
                
                # Generate response
                chain = (prompt | llm | StrOutputParser())
                response = chain.invoke({
                    "context": context,
                    "question": query
                })
                
                # Extract thinking process
                thinking = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
                if thinking:
                    with st.expander("🧠 Reasoning Process", expanded=True):
                        st.markdown(thinking.group(1).strip())
                    main_response = response.replace(f'<think>{thinking.group(1)}</think>', '').strip()
                else:
                    main_response = response
                
                # Display response
                st.write(main_response)
                
                # Show sources
                with st.expander("📚 Sources"):
                    for i, doc in enumerate(docs, 1):
                        st.markdown(f"**Source {i}:**")
                        st.markdown(doc.page_content[:200] + "...")
                
                # Update chat history
                st.session_state.chat_history.append({
                    "user": query,
                    "assistant": main_response
                })

else:
    st.info("Please upload some documents to get started!")

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered RAG made by @manthysbr")