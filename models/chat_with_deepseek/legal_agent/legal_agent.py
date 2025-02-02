import streamlit as st
import pytesseract
from pdf2image import convert_from_path
from langchain_community.document_loaders import PDFPlumberLoader, UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import Document
import os

# Define color palette (unchanged)
primary_color = "#1B3C73"
secondary_color = "#8B0000"
background_color = "#F5F5F5"
sidebar_background = "#2F4F4F"
text_color = "#000000"

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

st.title("📚 Assistente Jurídico Brasileiro")

# Sidebar configuration (unchanged)
with st.sidebar:
    st.header("Configurações")
    area_juridica = st.selectbox(
        "Área Jurídica",
        ["Direito Civil", "Direito Penal", "Direito Trabalhista", "Direito Tributário"]
    )
    include_jurisprudence = st.checkbox("Incluir Jurisprudência", value=True)
    detail_level = st.slider("Nível de Detalhamento", 1, 5, 3)
    
    st.markdown("---")
    st.markdown("""
    ### Informações do Sistema
    - **Modelo Base**: DeepSeek R1
    - **Embeddings**: BERT Portuguese Legal
    - **Base de Dados**: Legislação Brasileira
    """)

def process_pdf(file_path):
    """Process PDF with OCR support"""
    try:
        loader = PDFPlumberLoader(file_path)
        docs = loader.load()
    except Exception:
        images = convert_from_path(file_path)
        text = "\n".join([pytesseract.image_to_string(image, lang='por') for image in images])
        docs = [Document(page_content=text)]
    
    for doc in docs:
        doc.metadata["area_juridica"] = area_juridica
    return docs

# Legal-specific text splitter (unchanged)
legal_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,
    separators=["\nArt.", "\nArtigo", "\nParágrafo", "\n§", "\nInciso", "\nAlínea"]
)

# Portuguese legal embeddings (unchanged)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True},
    cache_folder="./models"
)

# Main file upload section
st.header("📁 Upload de Documento Jurídico")
uploaded_file = st.file_uploader("Faça upload do documento (PDF)", type="pdf")

if uploaded_file is not None:
    st.success("Documento recebido! Processando...")

    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getvalue())

    # Process document
    docs = process_pdf("temp.pdf")
    documents = legal_splitter.split_documents(docs)
    
    # Create vector store
    vector = FAISS.from_documents(documents, embeddings)
    retriever = vector.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    # Legal-specific prompt (updated)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Você é um especialista em direito brasileiro, especializado em {area_juridica}.
        
        Analise o contexto fornecido e responda seguindo estas etapas:
        1. Identifique os dispositivos legais aplicáveis
        2. {jurisprudence_instruction}
        3. Considere súmulas e orientações dos tribunais superiores
        4. Forneça fundamentação legal completa
        
        Nível de detalhamento: {detail_level}/5
        
        Contexto do documento: {context}"""),
        ("human", "{question}")
    ])

    # Configure LLM
    llm = Ollama(model="deepseek-r1:7b")
    
    # Create chain
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    def get_jurisprudence_instruction(include_jurisprudence):
        return "Analise jurisprudência relevante" if include_jurisprudence else "Pule análise de jurisprudência"

    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
            "area_juridica": lambda _: area_juridica,
            "detail_level": lambda _: detail_level,
            "jurisprudence_instruction": lambda _: get_jurisprudence_instruction(include_jurisprudence)
        }
        | prompt 
        | llm 
        | StrOutputParser()
    )

    # Question interface
    st.header("❓ Consulta Jurídica")
    user_input = st.text_area("Digite sua consulta jurídica:")

    if user_input:
        with st.spinner("Analisando a questão..."):
            try:
                # Execute query with new chain
                response = chain.invoke(user_input)
                
                # Parse chain of thought and main response
                import re
                
                # Extract thinking process
                thinking = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
                if thinking:
                    thought_process = thinking.group(1).strip()
                    # Remove the thinking section from main response
                    main_response = response.replace(f'<think>{thought_process}</think>', '').strip()
                else:
                    thought_process = None
                    main_response = response
                
                # Display thinking process in expander
                with st.expander("💭 Ver processo de pensamento do modelo"):
                    if thought_process:
                        st.markdown("### Processo de Raciocínio")
                        st.markdown(thought_process)
                
                # Display main response
                st.success("📋 Parecer Jurídico:")
                st.write(main_response)
                
                # Show sources
                retrieved_docs = retriever.get_relevant_documents(user_input)
                with st.expander("Ver Fontes"):
                    for doc in retrieved_docs:
                        st.markdown(f"**Fonte:** {doc.metadata.get('source', 'Documento Base')}")
                        st.markdown(f"**Trecho:** {doc.page_content[:200]}...")
                
            except Exception as e:
                st.error(f"Erro no processamento: {str(e)}")

    # Cleanup
    if os.path.exists("temp.pdf"):
        os.remove("temp.pdf")

else:
    st.info("Por favor, faça upload de um documento PDF para iniciar.")

# Footer
st.markdown("---")
st.caption("🐳 Deepseek powered legal agent simulation made by @manthysbr")
st.caption("⚠️ Always consult a law professional, this is only for study purposes.")