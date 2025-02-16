import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import json
import re
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np
import fitz

# Initialize Qdrant client
qdrant_client = QdrantClient("localhost", port=6333)

# Create collection if not exists
try:
    qdrant_client.create_collection(
        collection_name="expenses",
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
    )
except Exception:
    pass

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
    .expense-block {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #00FF00;
        background-color: #0A2A0A;
    }
    .data-block {
        padding: 1rem;
        border: 2px solid #00FF00;
        border-radius: 0.5rem;
        background-color: #0A2A0A;
    }
    .insights {
        background-color: #0A2A0A;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #00FF00;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

class FinanceAgent:
    def __init__(self):
        self.llm = Ollama(model="deepseek-r1:14b")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.history_path = Path.home() / "finance_history"
        self.history_path.mkdir(exist_ok=True)
        self.qdrant = qdrant_client
        
        self.categories = {
            "House Bills": ["Water", "Electricity", "Internet", "Phone"],
            "Food & Drink": ["Groceries", "Restaurants", "Delivery"],
            "Credit Cards": ["Card 1", "Card 2"],
            "Entertainment": ["Games", "Streaming", "Books"],
            "Healthcare": ["Medicine", "Consultations"],
            "Savings": ["Investments", "Emergency Fund"],
            "Others": ["Miscellaneous"]
        }

    def _get_embedding(self, text: str) -> list:
        """Get embedding for text"""
        return self.embeddings.embed_query(text)

    def save_monthly_data(self, year: int, month: int, expenses: list):
        """Save monthly expense data"""
        filename = self.history_path / f"{year}_{month:02d}.json"
        data = {
            "timestamp": datetime.now().isoformat(),
            "expenses": expenses
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_monthly_data(self, year: int, month: int) -> dict:
        """Load monthly expense data"""
        filename = self.history_path / f"{year}_{month:02d}.json"
        if filename.exists():
            with open(filename) as f:
                return json.load(f)
        return {"expenses": []}

    def process_pdf(self, content: str) -> dict:
        """Process PDF content using DeepSeek"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial analyst specializing in bill analysis.
            Extract expense information and provide insights.
            
            Available categories: {categories}
            
            Analyze the bill and return a JSON with:
            {
                "expense": {
                    "category": str,
                    "subcategory": str,
                    "amount": float,
                    "date": str,
                    "description": str
                },
                "insights": {
                    "comparison": str,
                    "savings_tips": list,
                    "warnings": list
                }
            }
            
            CONTENT:
            {content}""")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        response = chain.invoke({
            "categories": json.dumps(self.categories, indent=2),
            "content": content
        })
        
        return json.loads(response)

    def add_expense(self, expense_data: dict):
        """Add expense to Qdrant and save to file"""
        # Create embedding for expense
        text_for_embedding = f"{expense_data['category']} {expense_data['subcategory']} {expense_data['description']}"
        vector = self._get_embedding(text_for_embedding)
        
        # Add to Qdrant
        self.qdrant.upsert(
            collection_name="expenses",
            points=[models.PointStruct(
                id=int(datetime.now().timestamp() * 1000),
                vector=vector,
                payload=expense_data
            )]
        )
        
        # Save to file
        date = datetime.fromisoformat(expense_data["date"])
        data = self.load_monthly_data(date.year, date.month)
        data["expenses"].append(expense_data)
        self.save_monthly_data(date.year, date.month, data["expenses"])

    def query_expenses(self, query: str) -> str:
        """Query expense history using natural language"""
        # Get query embedding
        query_vector = self._get_embedding(query)
        
        # Search Qdrant
        search_result = self.qdrant.search(
            collection_name="expenses",
            query_vector=query_vector,
            limit=5
        )
        
        # Format context from results
        context = "\n".join([json.dumps(hit.payload) for hit in search_result])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial advisor with expertise in personal finance.
            Analyze the expenses and provide detailed insights.
            
            CONTEXT:
            {context}
            
            QUESTION:
            {query}
            
            Use <think> tags for analysis:
            <think>
            1. Analyze spending patterns
            2. Compare to typical benchmarks
            3. Identify potential savings
            4. Generate specific recommendations
            </think>
            
            [Your response with specific advice and insights]""")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        response = chain.invoke({
            "context": context,
            "query": query
        })
        
        return self._filter_think_content(response)

    def get_spending_insights(self) -> str:
        """Generate AI-powered spending insights"""
        search_result = self.qdrant.scroll(
            collection_name="expenses",
            limit=100
        )[0]
        
        expenses = [hit.payload for hit in search_result]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze these expenses and provide detailed financial insights.
            Focus on:
            1. Unusual spending patterns
            2. Potential savings opportunities
            3. Budget recommendations
            4. Category-specific advice
            
            EXPENSES:
            {expenses}
            
            Format response in Markdown with clear sections.""")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        return chain.invoke({"expenses": json.dumps(expenses)})

    def _filter_think_content(self, text: str) -> str:
        return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

    def get_year_summary(self, year: int) -> pd.DataFrame:
        """Get year summary of expenses"""
        all_expenses = []
        for month in range(1, 13):
            data = self.load_monthly_data(year, month)
            if data["expenses"]:
                for expense in data["expenses"]:
                    expense["month"] = month
                    all_expenses.append(expense)
        return pd.DataFrame(all_expenses)

# Initialize session state
if 'finance_agent' not in st.session_state:
    st.session_state.finance_agent = FinanceAgent()

st.title("💰 Financial Advisor")

# Sidebar for expense entry
with st.sidebar:
    st.header("📝 Add Expense")
    
    # PDF Upload
    st.subheader("📄 Upload Bill")
    uploaded_file = st.file_uploader("Upload PDF bill", type="pdf")
    if uploaded_file:
        with st.spinner("Processing bill..."):
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            
            result = st.session_state.finance_agent.process_pdf(text)
            expense = result["expense"]
            insights = result["insights"]
            
            st.session_state.finance_agent.add_expense(expense)
            st.success("Bill processed!")
            
            with st.expander("📊 Bill Analysis"):
                st.markdown(f"**Comparison:** {insights['comparison']}")
                st.markdown("**Savings Tips:**")
                for tip in insights['savings_tips']:
                    st.markdown(f"- {tip}")
                if insights['warnings']:
                    st.markdown("**⚠️ Warnings:**")
                    for warning in insights['warnings']:
                        st.markdown(f"- {warning}")
    
    # Manual Entry
    st.subheader("✍️ Manual Entry")
    category = st.selectbox("Category", list(st.session_state.finance_agent.categories.keys()))
    subcategory = st.selectbox("Subcategory", st.session_state.finance_agent.categories[category])
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    date = st.date_input("Date")
    description = st.text_area("Description")
    
    if st.button("💾 Save Expense"):
        expense = {
            "category": category,
            "subcategory": subcategory,
            "amount": amount,
            "date": date.isoformat(),
            "description": description
        }
        st.session_state.finance_agent.add_expense(expense)
        st.success("Expense saved!")

# Main interface - Monthly Overview
st.header("📊 Monthly Overview")
col1, col2 = st.columns(2)
with col1:
    year = st.selectbox("Year", range(2024, 2025))
with col2:
    month = st.selectbox("Month", range(1, 13))

data = st.session_state.finance_agent.load_monthly_data(year, month)
if data["expenses"]:
    df = pd.DataFrame(data["expenses"])
    
    # Monthly summary
    total = df['amount'].sum()
    st.markdown(f"### Total Expenses: ${total:,.2f}")
    
    # Category breakdown
    fig = px.pie(df, values='amount', names='category', title="Expenses by Category")
    st.plotly_chart(fig)
    
    # Expense table
    with st.expander("📋 Detailed Expenses"):
        st.dataframe(df)

# Chat interface
st.header("💬 Financial Assistant")
with st.expander("ℹ️ Chat Help"):
    st.markdown("""
    Ask questions like:
    - What are my highest expenses this month?
    - Compare my spending between categories
    - Show my savings progress
    - Analyze my spending patterns
    """)

query = st.text_input("Ask about your finances...")
if query:
    with st.spinner("Analyzing..."):
        response = st.session_state.finance_agent.query_expenses(query)
        st.markdown(f"<div class='expense-block'>{response}</div>", unsafe_allow_html=True)

# AI Insights
st.header("🤖 AI Insights")
if st.button("Generate Spending Insights"):
    with st.spinner("Analyzing your spending patterns..."):
        insights = st.session_state.finance_agent.get_spending_insights()
        st.markdown(f"<div class='insights'>{insights}</div>", unsafe_allow_html=True)

# Year Analysis
if st.checkbox("📈 Show Yearly Analysis"):
    yearly_data = st.session_state.finance_agent.get_year_summary(year)
    if not yearly_data.empty:
        st.header("Year Overview")
        
        # Monthly trend
        monthly_trend = yearly_data.groupby('month')['amount'].sum()
        fig = px.line(x=monthly_trend.index, y=monthly_trend.values,
                     title="Monthly Expense Trend",
                     labels={'x': 'Month', 'y': 'Total Expenses'})
        st.plotly_chart(fig)
        
        # Category breakdown by month
        pivot = pd.pivot_table(yearly_data, 
                             values='amount',
                             index='month',
                             columns='category',
                             aggfunc='sum',
                             fill_value=0)
        fig = px.bar(pivot, title="Monthly Expenses by Category", barmode='stack')
        st.plotly_chart(fig)

st.markdown("---")
st.caption("🤖 Powered by DeepSeek-R1")

# Install dependencies
# cd /llm_apps/models/chat_with_deepseek/finance_agent_team/finance_tracker
# pip install -r requirements.txt
# Start Qdrant (if not running)
# docker run -d -p 6333:6333 qdrant/qdrant
# Run the app
# streamlit run finance_tracker.py