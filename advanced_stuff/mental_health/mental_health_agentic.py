import os
import logging
import streamlit as st
from autogen import ConversableAgent, GroupChat, GroupChatManager, LLMConfig

# Configurações iniciais
os.environ["AUTOGEN_USE_DOCKER"] = "0"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Estado da sessão
if "output" not in st.session_state:
    st.session_state.output = {"assessment": "", "action": "", "followup": ""}

# Sidebar de configuração
st.sidebar.title("Configuração do Ollama")
ollama_base_url = st.sidebar.text_input("URL do Ollama", value="http://localhost:11434")
ollama_model = st.sidebar.text_input(
    "Modelo", value="llama3.2:3b",
    help="Ex: llama3, llama3.1:8b, gemma:7b"
)
temperature = st.sidebar.slider("Temperatura", 0.0, 1.0, 0.7, 0.1)

st.sidebar.warning("""
## ⚠️ Aviso Importante
Esta aplicação é uma ferramenta de apoio e não substitui atendimento profissional em saúde mental.
Se estiver em crise, ligue 188 (CVV) ou 192 (Emergência).
""")

# Título e descrição
st.title("🧠 Agente de Apoio à Saúde Mental")
st.info("""
**Conheça Sua Equipe de Apoio:**
- 🧠 Agente de Avaliação
- 🎯 Agente de Ação
- 🔄 Agente de Acompanhamento
""")

# Formulário principal
st.subheader("Informações Pessoais")
col1, col2 = st.columns(2)
with col1:
    mental_state = st.text_area("Como você tem se sentido recentemente?")
    sleep_pattern = st.select_slider(
        "Sono (horas/noite)",
        [str(i) for i in range(0, 13)], value="7"
    )
with col2:
    stress_level = st.slider("Nível de Estresse (1-10)", 1, 10, 5)
    support_system = st.multiselect(
        "Sistema de Apoio",
        ["Família", "Amigos", "Terapeuta", "Grupos de Apoio", "Nenhum"]
    )

recent_changes = st.text_area("Mudanças significativas recentes")
current_symptoms = st.multiselect(
    "Sintomas Atuais",
    ["Ansiedade", "Depressão", "Insônia", "Fadiga", "Perda de Interesse",
     "Dificuldade de Concentração", "Mudanças no Apetite", "Isolamento Social",
     "Alterações de Humor", "Desconforto Físico"]
)

# Quando o usuário clica para gerar o plano
if st.button("Obter Plano de Apoio"):
    if not ollama_base_url or not ollama_model:
        st.error("Configure a URL e o modelo do Ollama.")
    else:
        with st.spinner("🤖 Gerando plano de apoio..."):
            try:
                # Monta a tarefa
                task = f"""
Crie um plano abrangente de apoio à saúde mental baseado em:
- Estado Emocional: {mental_state}
- Sono: {sleep_pattern}h/noite
- Estresse: {stress_level}/10
- Apoio: {', '.join(support_system) or 'Nenhum'}
- Mudanças: {recent_changes or 'Nenhuma'}
- Sintomas: {', '.join(current_symptoms) or 'Nenhum'}
"""

                # Mensagens do sistema para cada agente
                system_messages = {
                    "assessment_agent": """
Você é um profissional experiente em saúde mental. Sua tarefa:
1. Reconhecer a coragem do usuário
2. Analisar o estado emocional com empatia
3. Perguntar para entender melhor
4. Avaliar riscos e validar experiências
""",
                    "action_agent": """
Você é um especialista em intervenção de crises. Sua tarefa:
1. Fornecer estratégias imediatas
2. Priorizar intervenções eficazes
3. Sugerir recursos e comunidades
4. Ensinar técnicas de autorregulação
""",
                    "followup_agent": """
Você é um planejador de recuperação a longo prazo. Sua tarefa:
1. Criar metas de progresso
2. Desenvolver sistema de monitoramento
3. Planejar prevenção de recaídas
4. Construir rotina de autocuidado sustentável
"""
                }

                # Configuração do LLM (Ollama)
                llm_config = LLMConfig(
                    api_type="ollama",
                    base_url=ollama_base_url,
                    model=ollama_model,
                    temperature=temperature
                )

                # Cria os agentes
                assessment_agent = ConversableAgent(
                    name="assessment_agent",
                    system_message=system_messages["assessment_agent"],
                    llm_config=llm_config
                )
                action_agent = ConversableAgent(
                    name="action_agent",
                    system_message=system_messages["action_agent"],
                    llm_config=llm_config
                )
                followup_agent = ConversableAgent(
                    name="followup_agent",
                    system_message=system_messages["followup_agent"],
                    llm_config=llm_config
                )

                # Orquestra em grupo
                group = GroupChat(
                    agents=[assessment_agent, action_agent, followup_agent],
                    speaker_selection_method="auto",
                    messages=[]
                )

                
                manager = GroupChatManager(
                    name="flow_manager",
                    groupchat=group,
                    llm_config=llm_config
                )

                # Inicia a conversa pelo manager
                result = manager.initiate_chat(
                    recipient=assessment_agent,
                    message=task,
                    max_turns=3
                )

                # Extrai últimas falas de cada agente
                chat = result.chat_history
                get_last = lambda agent_name: next(
                    (m["content"] for m in reversed(chat) if m.get("name") == agent_name),
                    "Não gerado"
                )
                st.session_state.output = {
                    "assessment": get_last("assessment_agent"),
                    "action": get_last("action_agent"),
                    "followup": get_last("followup_agent")
                }

                # Exibe resultados
                with st.expander("Avaliação"):
                    st.markdown(st.session_state.output["assessment"])
                with st.expander("Plano de Ação"):
                    st.markdown(st.session_state.output["action"])
                with st.expander("Acompanhamento"):
                    st.markdown(st.session_state.output["followup"])

                st.success("✨ Plano de apoio gerado com sucesso!")

            except Exception as e:
                logger.error("Erro na execução", exc_info=True)
                st.error(f"Ocorreu um erro: {e}")