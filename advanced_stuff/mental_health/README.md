Este projeto demonstra a aplicação de um sistema multiagente, construído com a framework AutoGen (AG2) e utilizando Modelos de Linguagem Grandes (LLMs) locais via Ollama, para simular um fluxo de apoio inicial à saúde mental. Baseado nas informações fornecidas pelo usuário através de uma interface Streamlit, o sistema orquestra três agentes especializados (Avaliação, Ação, Acompanhamento) para gerar um plano de apoio preliminar. O objetivo principal é explorar a capacidade de agentes de IA colaborativos em lidar com tarefas complexas e sensíveis, decompondo o problema em fases distintas. **Este é um protótipo de pesquisa e NÃO substitui aconselhamento ou tratamento profissional de saúde mental.**

## Problema Abordado

1.  **Acesso Inicial**: Muitas pessoas hesitam ou têm dificuldade em buscar apoio inicial para questões de saúde mental. Ferramentas automatizadas podem oferecer um primeiro passo de baixa barreira.
2.  **Complexidade da Avaliação**: A saúde mental é multifacetada. Uma abordagem única pode não ser eficaz. Diferentes perspectivas (avaliativa, interventiva, planejamento) são necessárias.
3.  **Limitações de Agente Único**: Um único LLM pode ter dificuldade em manter a consistência e a profundidade em todas as fases de um processo de apoio (compreensão empática, sugestão de ações imediatas, planejamento de longo prazo).
4.  **Privacidade**: O uso de LLMs locais (Ollama) aborda preocupações com a privacidade dos dados sensíveis compartilhados pelo usuário.
5.  **Estruturação da Resposta**: A necessidade de gerar um plano coeso que inclua avaliação, ações e acompanhamento requer uma coordenação que pode ser facilitada por um sistema multiagente.

## Solução Proposta: Sistema Multiagente (AutoGen)

O script `mental_health_agentic.py` implementa um sistema composto por:

1.  **Agentes Especializados (AutoGen `ConversableAgent`)**: Três agentes são definidos, cada um com um *system prompt* específico que molda sua persona e responsabilidades:
    *   `assessment_agent`: Focado em análise empática, validação dos sentimentos do usuário e compreensão inicial da situação.
    *   `action_agent`: Especializado em sugerir estratégias de enfrentamento imediatas, técnicas de autorregulação e recursos relevantes.
    *   `followup_agent`: Orientado para o planejamento de longo prazo, definindo metas progressivas, estratégias de prevenção de recaídas e rotinas de autocuidado.
2.  **Orquestração (AutoGen `GroupChat` e `GroupChatManager`)**:
    *   Os três agentes são colocados em um `GroupChat`.
    *   Um `GroupChatManager` é utilizado para gerenciar o fluxo da conversa entre os agentes, iniciando o processo e controlando o número de turnos. A seleção do próximo agente a falar (`speaker_selection_method="auto"`) é gerenciada pelo LLM do manager.
3.  **Integração com LLM Local (Ollama)**: A configuração (`LLMConfig`) permite conectar-se a um endpoint Ollama local, especificando o modelo (ex: `llama3.2:3b`) e a temperatura, garantindo que o processamento ocorra localmente.
4.  **Interface do Usuário (Streamlit)**: Uma interface web simples coleta informações do usuário (estado emocional, sono, estresse, sintomas, etc.) através de formulários e exibe os resultados gerados por cada agente em seções distintas (`st.expander`).

## Arquitetura

*   **Sistema Multiagente (MAS)**: Uso da biblioteca `autogen` (`ConversableAgent`, `GroupChat`, `GroupChatManager`) para modelar a interação colaborativa entre múltiplos agentes LLM.
*   **Modelos de Linguagem Grandes (LLMs)**: Integração com LLMs locais via Ollama, permitindo flexibilidade na escolha do modelo e garantindo privacidade. Parâmetros como `temperature` são configuráveis.
*   **Engenharia de Prompt**: *System prompts* detalhados são cruciais para definir o comportamento, o tom e as responsabilidades de cada agente especializado, guiando a IA para tarefas específicas dentro do domínio da saúde mental.
*   **Orquestração de Chat em Grupo**: O `GroupChatManager` atua como um orquestrador, iniciando a conversa com uma tarefa baseada na entrada do usuário e gerenciando a interação sequencial (ou automática) entre os agentes.
*   **Interface Web Interativa**: Streamlit é usado para criar rapidamente uma interface gráfica que permite a entrada de dados pelo usuário e a visualização estruturada das respostas dos agentes.
*   **Gerenciamento de Estado da Interface**: `st.session_state` do Streamlit é utilizado para armazenar os resultados da última execução, evitando que se percam ao interagir com a interface.
*   **Processamento da Saída**: Lógica simples para extrair a última mensagem relevante de cada agente do histórico do chat (`result.chat_history`) para exibição.

## Execução

1.  **Entrada do Usuário**: O usuário preenche o formulário na interface Streamlit com informações sobre seu estado atual.
2.  **Início da Validação**: Ao clicar em "Obter Plano de Apoio", as informações do formulário são coletadas e formatadas em uma string `task`.
3.  **Configuração do LLM**: `LLMConfig` é instanciado com os detalhes do Ollama (URL, modelo, temperatura) fornecidos na sidebar.
4.  **Criação dos Agentes**: Três instâncias de `ConversableAgent` são criadas, cada uma recebendo seu *system prompt* específico e a `LLMConfig`.
5.  **Formação do Grupo**: Os agentes são adicionados a um `GroupChat`.
6.  **Inicialização do Manager**: Um `GroupChatManager` é criado para gerenciar o `GroupChat`, usando a mesma `LLMConfig`.
7.  **Início da Conversa**: O método `manager.initiate_chat` é chamado, passando a `task` como mensagem inicial para o `assessment_agent`. O parâmetro `max_turns` limita a duração da conversa entre os agentes.
8.  **Interação dos Agentes**: Os agentes conversam entre si, mediados pelo `GroupChatManager`, cada um contribuindo com sua perspectiva especializada com base na tarefa inicial e nas mensagens anteriores.
9.  **Coleta de Resultados**: Após a conclusão do chat (atingido `max_turns`), o histórico da conversa (`result.chat_history`) é acessado.
10. **Extração e Exibição**: Uma função lambda busca a última mensagem de cada agente no histórico. Os conteúdos extraídos são armazenados no `st.session_state.output`.

## ⚠️ Aviso Importante

Esta aplicação é uma ferramenta de demonstração e apoio educacional. **Não é um substituto para diagnóstico, aconselhamento ou tratamento profissional de saúde mental.** As sugestões geradas pela IA são baseadas em padrões e não levam em conta a totalidade da sua situação individual. Se você estiver passando por dificuldades emocionais ou uma crise, por favor, procure ajuda profissional qualificada ou utilize recursos de emergência (como o CVV - Ligue 188 no Brasil, ou serviços de emergência locais).