import streamlit as st
import yfinance as yf
import pandas as pd
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import requests
from bs4 import BeautifulSoup
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

class FinanceAgent:
    def __init__(self):
        self.llm = Ollama(model="deepseek-r1:14b")
        
    def get_stock_data(self, symbol):
        stock = yf.Ticker(symbol)
        data = {
            "info": stock.info,
            "history": stock.history(period="1mo"),
            "recommendations": stock.recommendations,
            "news": stock.news
        }
        return data
    
    def search_web(self, query):
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(f"https://duckduckgo.com/html/?q={query}", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        for result in soup.find_all('div', class_='result')[:3]:
            results.append({
                'title': result.find('a').text,
                'snippet': result.find('div', class_='snippet').text if result.find('div', class_='snippet') else ''
            })
        return results
    
    def analyze(self, query, stock_data=None, web_data=None):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial analysis expert.
            Analyze the provided data and answer the query.
            
            STOCK DATA:
            {stock_data}
            
            WEB SEARCH RESULTS:
            {web_data}
            
            USER QUERY:
            {query}
            
            Provide detailed analysis with specific data points."""),
            ("human", "Analyze this financial situation")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        return chain.invoke({
            "stock_data": str(stock_data),
            "web_data": str(web_data),
            "query": query
        })

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = FinanceAgent()

st.title("HeraCorps Financial Analyst")
st.caption("AI-powered financial analysis powered by DeepSeek-R1")

# Input section
col1, col2 = st.columns(2)
with col1:
    stock_symbol = st.text_input("Stock Symbol", placeholder="e.g., AAPL")
with col2:
    analysis_query = st.text_area("Analysis Query", placeholder="What's your question about this stock?")

if st.button("🔍 Analyze"):
    with st.spinner("Gathering data..."):
        # Get stock data
        stock_data = st.session_state.agent.get_stock_data(stock_symbol)
        
        # Display basic info
        with st.expander("📊 Stock Information", expanded=True):
            st.write(f"**{stock_data['info'].get('longName', stock_symbol)}**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${stock_data['info'].get('currentPrice', 'N/A')}")
            with col2:
                st.metric("Market Cap", f"${stock_data['info'].get('marketCap', 'N/A'):,}")
            with col3:
                st.metric("52W High", f"${stock_data['info'].get('fiftyTwoWeekHigh', 'N/A')}")
        
        # Get web data
        web_results = st.session_state.agent.search_web(f"{stock_symbol} stock analysis news")
        
        # Generate analysis
        with st.spinner("Analyzing..."):
            response = st.session_state.agent.analyze(
                query=analysis_query,
                stock_data=stock_data,
                web_data=web_results
            )
            
            # Extract thinking process
            thinking = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
            if thinking:
                with st.expander("🧠 Analysis Process", expanded=True):
                    st.markdown(thinking.group(1).strip())
                main_analysis = response.replace(f'<think>{thinking.group(1)}</think>', '').strip()
            else:
                main_analysis = response
            
            # Display analysis
            st.header("📈 Analysis Report")
            st.markdown(main_analysis)
            
            # Show data sources
            with st.expander("🌐 Web Sources"):
                for result in web_results:
                    st.markdown(f"**{result['title']}**")
                    st.markdown(result['snippet'])

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered finance team simulation made by @manthysbr")