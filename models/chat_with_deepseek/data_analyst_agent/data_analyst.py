import streamlit as st
import pandas as pd
import duckdb
import tempfile
import csv
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

class DataAnalyst:
    def __init__(self):
        self.llm = Ollama(model="deepseek-r1:14b")
        self.db = duckdb.connect(database=':memory:')
        
    def analyze_query(self, query, table_info):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert SQL analyst.
            
            TABLE INFORMATION:
            {table_info}
            
            USER QUERY:
            {query}
            
            Generate a SQL query to answer the question.
            First think through the steps needed, then provide the SQL query.
            Include explanations of your approach."""),
            ("human", "Generate SQL analysis")
        ])
        
        chain = (prompt | self.llm | StrOutputParser())
        return chain.invoke({
            "table_info": table_info,
            "query": query
        })
    
    def execute_sql(self, sql_query, df):
        try:
            self.db.register('data', df)
            result = self.db.execute(sql_query).df()
            return result
        except Exception as e:
            return f"SQL Error: {str(e)}"

def preprocess_data(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            return None, "Unsupported file format"
        
        # Basic preprocessing
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df, None
    except Exception as e:
        return None, str(e)

# Initialize session state
if 'analyst' not in st.session_state:
    st.session_state.analyst = DataAnalyst()
if 'current_df' not in st.session_state:
    st.session_state.current_df = None

st.title("HeraCorps Data Analyst")
st.caption("SQL Analysis powered by DeepSeek")

# File upload
uploaded_file = st.file_uploader("Upload Dataset", type=['csv', 'xlsx'])

if uploaded_file:
    df, error = preprocess_data(uploaded_file)
    if error:
        st.error(error)
    else:
        st.session_state.current_df = df
        st.success("Data loaded successfully!")
        
        # Display sample
        with st.expander("Preview Data"):
            st.dataframe(df.head())
            st.write("Columns:", df.columns.tolist())
            st.write("Shape:", df.shape)

if st.session_state.current_df is not None:
    # Query input
    user_query = st.text_area("What would you like to analyze?", 
                             placeholder="e.g., Show me the top 5 sales by category")
    
    if st.button("🔍 Analyze"):
        with st.spinner("Analyzing..."):
            # Generate analysis
            table_info = f"""
            Table name: data
            Columns: {', '.join(st.session_state.current_df.columns)}
            Sample data: {st.session_state.current_df.head().to_dict()}
            """
            
            response = st.session_state.analyst.analyze_query(user_query, table_info)
            
            # Thinking process
            thinking = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
            if thinking:
                with st.expander("🧠 Analysis Process", expanded=True):
                    st.markdown(thinking.group(1).strip())
                main_response = response.replace(f'<think>{thinking.group(1)}</think>', '').strip()
            else:
                main_response = response
            
            # SQL query
            sql_match = re.search(r'```sql\n(.*?)\n```', main_response, re.DOTALL)
            if sql_match:
                sql_query = sql_match.group(1)
                st.code(sql_query, language='sql')
                
                # Execute query
                result = st.session_state.analyst.execute_sql(sql_query, st.session_state.current_df)
                
                if isinstance(result, pd.DataFrame):
                    st.success("Query executed successfully!")
                    st.dataframe(result)
                else:
                    st.error(result)
            else:
                st.error("No SQL query found in the response")

else:
    st.info("Please upload a dataset to begin analysis")

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered data analyst simulation made by @manthysbr")