import streamlit as st
import time
import json
from datetime import datetime, timedelta
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import re

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

class CustomerSupportAgent:
    def __init__(self):
        self.llm = Ollama(model="deepseek-r1:14b")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.memory_store = {}
        
    def handle_query(self, query, user_id, context):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a customer support AI agent for HeraCorps.
            Use the following context about the customer to provide personalized support:
            
            CUSTOMER CONTEXT:
            {context}
            
            CURRENT QUERY:
            {query}
            
            Provide detailed and helpful support while referencing past interactions."""),
            ("human", "{query}")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        response = chain.invoke({
            "context": context,
            "query": query
        })
        
        # Store in memory
        if user_id not in self.memory_store:
            self.memory_store[user_id] = FAISS.from_texts(
                [query, response],
                self.embeddings
            )
        else:
            self.memory_store[user_id].add_texts([query, response])
            
        return response
    
    def generate_synthetic_data(self, user_id):
        today = datetime.now()
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Generate realistic customer data in JSON format including:
            - Customer name and details
            - Recent orders
            - Support history
            - Preferences
            
            Make it detailed but believable."""),
            ("human", f"Generate profile for customer {user_id}")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        response = chain.invoke({})
        
        try:
            return json.loads(response)
        except:
            return None


if 'support_agent' not in st.session_state:
    st.session_state.support_agent = CustomerSupportAgent()
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'customer_data' not in st.session_state:
    st.session_state.customer_data = None

st.title("HeraCorps Customer Support")
st.caption("Powered by DeepSeek")


with st.sidebar:
    st.header("Customer Settings")
    customer_id = st.text_input("Customer ID", placeholder="Enter ID...")
    
    if st.button("Generate Profile"):
        with st.spinner("Creating customer profile..."):
            st.session_state.customer_data = st.session_state.support_agent.generate_synthetic_data(customer_id)
        if st.session_state.customer_data:
            st.success("Profile generated!")
            with st.expander("View Profile"):
                st.json(st.session_state.customer_data)


if customer_id:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    if query := st.chat_input("How can I help?"):
        with st.chat_message("user"):
            st.write(query)
            
    
        context = json.dumps(st.session_state.customer_data) if st.session_state.customer_data else ""
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.support_agent.handle_query(
                    query=query,
                    user_id=customer_id,
                    context=context
                )
                
                
                thinking = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
                if thinking:
                    with st.expander("🧠 Thought Process"):
                        st.markdown(thinking.group(1).strip())
                    main_response = response.replace(f'<think>{thinking.group(1)}</think>', '').strip()
                else:
                    main_response = response
                
                st.write(main_response)
                
                st.session_state.messages.append({"role": "user", "content": query})
                st.session_state.messages.append({"role": "assistant", "content": main_response})
else:
    st.info("Please enter a customer ID to start.")

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered customer support simulation made by @manthysbr")