import streamlit as st
import time
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

st.title("🏋️‍♂️ AI Health & Fitness Planner")

# Configure LLM
llm = Ollama(model="deepseek-r1:14b")

# Profile Input
st.header("👤 Your Profile")
col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age", min_value=10, max_value=100, step=1)
    height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, step=0.1)
    activity_level = st.selectbox(
        "Activity Level",
        ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"]
    )

with col2:
    weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, step=0.1)
    goals = st.selectbox(
        "Goals",
        ["Weight Loss", "Muscle Gain", "Endurance", "General Fitness"]
    )
    dietary_pref = st.selectbox(
        "Dietary Preference",
        ["No Restrictions", "Vegetarian", "Vegan", "Keto", "Paleo"]
    )

if st.button("🎯 Generate Plan"):
    with st.spinner("Analyzing and creating your personalized plan..."):
        # Prepare user data
        user_data = {
            "age": age,
            "height": height,
            "weight": weight,
            "activity_level": activity_level,
            "goals": goals,
            "dietary_pref": dietary_pref
        }
        
        # Enhanced fitness prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert fitness and nutrition consultant.
            Analyze the client's data and provide a detailed plan:
            
            CLIENT DATA:
            {user_data}
            
            Create a comprehensive plan including:
            1. Fitness routine (with specific exercises)
            2. Nutrition plan (with meal suggestions)
            3. Progress tracking metrics
            4. Important health considerations
            
            Use professional terminology and provide scientific reasoning."""),
            ("human", "Generate a complete fitness and nutrition plan.")
        ])

        # Generate plan
        chain = (prompt | llm | StrOutputParser())
        response = chain.invoke({"user_data": str(user_data)})
        
        # Extract thinking process
        thinking = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
        if thinking:
            with st.expander("🧠 Analysis Process", expanded=True):
                st.markdown(thinking.group(1).strip())
            main_plan = response.replace(f'<think>{thinking.group(1)}</think>', '').strip()
        else:
            main_plan = response

        # Display plan
        st.header("📋 Your Personalized Plan")
        st.write(main_plan)

        # Display metrics
        st.header("📊 Health Metrics") 
        col1, col2, col3 = st.columns(3)
        with col1:
            bmi = weight / ((height/100) ** 2)
            st.metric("BMI", f"{bmi:.1f}")
        with col2:
            st.metric("Weekly Training Days", "4-5")
        with col3:
            st.metric("Daily Calorie Target", "2000-2500")

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered fitness and health simulation made by @manthysbr")
st.caption("⚠️ Always consult a healthcare professional before starting a new fitness program.")