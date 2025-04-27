Este projeto demonstra a aplicação de um sistema multiagente baseado em Modelos de Linguagem Grandes (LLMs) para a validação avançada de templates Helm do Kubernetes. Utilizando a framework AutoGen (AG2) e LLMs locais (via Ollama), o sistema decompõe a complexa tarefa de validação em sub-tarefas atribuídas a agentes especializados, coordenando seus resultados para gerar um relatório consolidado. O objetivo é ir além das verificações sintáticas tradicionais (`helm lint`, `kubeval`), incorporando análise semântica de segurança, otimização de recursos e boas práticas.

## Problema Abordado

A validação de templates Helm apresenta desafios significativos:

1.  **Complexidade Sintática e Semântica**: Templates Helm misturam YAML, Go templating e lógica condicional, tornando a análise estática complexa.
2.  **Superficialidade das Ferramentas Tradicionais**: `helm lint` foca em estrutura e `kubeval` em conformidade com o schema K8s, mas ambos falham em detectar problemas lógicos, de segurança ou de otimização mais profundos.
3.  **Conhecimento Multidisciplinar**: Uma validação completa exige expertise em YAML, Helm, Kubernetes API, segurança (CIS, OWASP), otimização de recursos e boas práticas de engenharia de software.
4.  **Escalabilidade da Análise**: A revisão manual detalhada é demorada e propensa a erros, especialmente em charts complexos ou em grande volume.

Este projeto implementa um `HelmValidationSystem` que orquestra múltiplos agentes de IA e ferramentas CLI:

1.  **Agentes Especializados (AutoGen)**: Quatro `AssistantAgent` são inicializados, cada um com um *system prompt* detalhado que define seu papel e regras de análise:
    *   `SyntaxAgent`: Focado em YAML, Go templating, convenções de nomenclatura e versões de API.
    *   `SecurityAgent`: Analisa configurações de segurança (`securityContext`, RBAC, NetworkPolicy, secrets) com base em benchmarks como OWASP K8s Top 10 e CIS.
    *   `ResourceAgent`: Avalia a definição de `requests`/`limits`, configurações de HPA, Probes (liveness, readiness) e PDB.
    *   `BestPracticesAgent`: Verifica a estrutura do chart, uso de `values.yaml`, helpers (`_helpers.tpl`), documentação (`NOTES.txt`, `README.md`) e labels padrão.
2.  **Agente Coordenador (AutoGen)**: Um `AssistantAgent` adicional recebe as análises dos agentes especializados e os resultados das ferramentas CLI. Sua tarefa é integrar essas informações, priorizar problemas críticos e gerar um relatório final coeso em Markdown.
3.  **Integração com Ferramentas CLI**: O sistema executa `helm lint --strict` e `helm template | kubeval --strict` em um ambiente temporário para obter validações técnicas básicas.
4.  **Interface Streamlit**: Uma interface web simples permite o upload de arquivos de template YAML e a visualização dos resultados detalhados por agente e do relatório consolidado.

## Arquitetura

*   **Sistema Multiagente (MAS)**: Utilização da biblioteca `autogen` para criar e gerenciar múltiplos agentes LLM colaborativos. Cada agente opera com autonomia dentro de seu domínio de especialização definido pelo prompt.
*   **Modelos de Linguagem Grandes (LLMs)**: Integração com LLMs locais via Ollama (`codellama`, `llama3.2`, etc.). A configuração `temperature: 0.1` busca respostas mais determinísticas e focadas.
*   **Engenharia de Prompt**: Elaboração cuidadosa de *system prompts* para cada agente, especificando:
    *   **Contexto**: Persona do agente (ex: "especialista em segurança K8s").
    *   **Tarefa**: O que analisar no template.
    *   **Regras Obrigatórias**: Critérios específicos de verificação.
    *   **Formato de Resposta**: Estrutura desejada (Markdown, tabelas).
    *   **Restrições**: Limites da análise (ex: "não invente problemas").
*   **Processamento Paralelo**: Uso de `concurrent.futures.ThreadPoolExecutor` para executar as análises dos agentes LLM em paralelo, otimizando o tempo total de validação.
*   **Extração de Conteúdo LLM**: Função `extract_llm_content` para lidar com diferentes formatos de resposta das APIs LLM e da biblioteca AutoGen, garantindo a extração do texto relevante.
*   **Manipulação de Arquivos Temporários**: Uso do módulo `tempfile` para criar um ambiente de chart Helm temporário (`Chart.yaml`, `templates/`) necessário para a execução dos comandos `helm lint` e `helm template`.
*   **Interação com Subprocessos**: Utilização do módulo `subprocess` para executar comandos CLI (`helm`, `kubeval`) e capturar seus outputs (stdout, stderr) e códigos de retorno.
*   **Chunking de Mensagens**: Função `chunk_message` para dividir prompts ou resultados muito longos, evitando limites de tokens da API do LLM ou truncamento na exibição.
*   **Caching de Recursos (Streamlit)**: Uso de `@st.cache_resource` para evitar a reinicialização custosa dos agentes LLM a cada interação na interface Streamlit.

## Execução

1.  Usuário faz upload de um arquivo `template.yaml` via Streamlit.
2.  `validate_template_content` é chamado.
3.  Um diretório temporário é criado.
4.  Um `Chart.yaml` mínimo e o `template.yaml` (em `templates/`) são escritos no diretório temporário.
5.  `helm lint` e `helm template | kubeval` são executados no diretório temporário. Seus resultados são armazenados.
6.  As tarefas de análise dos agentes (`Syntax`, `Security`, `Resource`, `BestPractices`) são submetidas a um `ThreadPoolExecutor`. O conteúdo do template é passado como parte do prompt do usuário para cada agente.
7.  Os resultados de cada agente são coletados e o conteúdo textual é extraído usando `extract_llm_content`.
8.  Um `summary_message` é construído, concatenando os resultados (truncados se necessário com `chunk_message`) dos agentes e das ferramentas CLI.
9.  O `CoordinatorAgent` é invocado com o `summary_message` para gerar o relatório consolidado (`results["summary"]`).
10. O dicionário `results` completo (contendo timestamp, validações LLM individuais, validações técnicas e o sumário) é retornado.
11. A interface Streamlit exibe o sumário e permite a navegação por abas para ver os detalhes de cada análise.
