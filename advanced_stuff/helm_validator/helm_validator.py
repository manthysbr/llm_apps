import streamlit as st
import yaml
import json
import os
import tempfile
import subprocess
import re
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from autogen.agentchat.assistant_agent import AssistantAgent
from autogen.agentchat.user_proxy_agent import UserProxyAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    # Descomente para logar em arquivo
    # filename='helm_validation.log',
    # filemode='a'
)
logger = logging.getLogger(__name__)

def chunk_message(message, max_tokens=1500):
    """Divide uma mensagem longa em partes menores para evitar truncamento."""
    if len(message) <= max_tokens:
        return message
    
    # Dividir preservando parágrafos
    chunks = []
    paragraphs = message.split('\n\n')
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_tokens:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(para) > max_tokens:
                # Caso um parágrafo seja muito longo, divida-o
                words = para.split()
                current_chunk = ""
                for word in words:
                    if len(current_chunk) + len(word) + 1 <= max_tokens:
                        if current_chunk:
                            current_chunk += " " + word
                        else:
                            current_chunk = word
                    else:
                        chunks.append(current_chunk)
                        current_chunk = word
            else:
                current_chunk = para
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks[0] + "\n\n[Mensagem truncada devido ao tamanho]"

def extract_llm_content(response):
    """
    Extrai o conteúdo textual de uma resposta LLM, que pode vir em diferentes formatos.
    """
    if response is None:
        return "Nenhuma resposta recebida."
        
    # Se já for uma string, retorna diretamente
    if isinstance(response, str):
        return response
        
    # Se for um dicionário (formato comum na API de chat)
    if isinstance(response, dict):
        if 'content' in response:
            return response['content']
        # Alguns modelos retornam em formatos diferentes
        for key in ['text', 'message', 'choices', 'result']:
            if key in response:
                return extract_llm_content(response[key])  # Recursivo para estruturas aninhadas
                
    # Se for uma lista (como retornado por alguns modelos)
    if isinstance(response, list):
        if response and isinstance(response[-1], dict) and 'content' in response[-1]:
            return response[-1]['content']
        if response:
            return extract_llm_content(response[-1])  # Tenta o último item
            
    # Para outros tipos de objetos (como os objetos de resposta do AutoGen)
    try:
        # Tenta acessar atributos comuns
        if hasattr(response, 'content'):
            return response.content
        if hasattr(response, 'message'):
            return extract_llm_content(response.message)
        # Em último caso, converte para string
        return str(response)
    except:
        return f"Não foi possível extrair conteúdo: {str(response)[:100]}..."

# --- Configurações Streamlit ---
st.set_page_config(page_title="Validador AG2 de Templates Helm", layout="wide")

# --- Configuração do Ollama ---
st.sidebar.header("Configuração do Ollama")
ollama_url = st.sidebar.text_input("URL do Ollama", value="http://localhost:11434")
ollama_model = st.sidebar.selectbox(
    "Modelo LLM",
    ["codellama", "llama3.2", "mistral", "deepseek-coder-v2:latest", "gemma"],
    index=0,
    help="Modelos como CodeLlama ou Llama 3.2 são recomendados para análise de código."
)

# --- Prompts Refinados para Agentes Especializados ---
VALIDATION_PROMPTS = {
    "sintaxe": """
    CONTEXTO: Você é um especialista em validação de sintaxe YAML e templates Helm para Kubernetes.
    TAREFA: Analise o template Helm fornecido. Identifique erros de sintaxe YAML, formatação, estrutura e uso de Go templates.
    REGRAS OBRIGATÓRIAS:
    1. Verifique indentação YAML (2 espaços).
    2. Confirme fechamento de colchetes, chaves, parênteses.
    3. Valide sintaxe Go template: `{{ .Values.xyz }}`.
    4. Verifique convenções de nomenclatura K8s (minúsculas, hifens).
    5. Verifique versões de API (ex: `apps/v1` vs. obsoletas).
    FORMATO DE RESPOSTA:
    - Use Markdown. Liste cada problema com número de linha (se possível) e sugestão.
    - Categorize por severidade: Crítico, Alto, Médio, Baixo.
    - Forneça exemplos de código correto.
    - Se sem problemas, liste as verificações feitas.
    RESTRIÇÕES:
    - Foque apenas em sintaxe e estrutura. Não analise lógica de segurança ou recursos.
    - Não invente problemas. Baseie-se estritamente no conteúdo fornecido.
    """,
    "seguranca": """
    CONTEXTO: Você é um especialista em segurança Kubernetes e Helm.
    TAREFA: Analise o template Helm para identificar vulnerabilidades e configurações inseguras.
    REGRAS OBRIGATÓRIAS:
    1. Identifique containers como root ou com privilégios (`privileged: true`).
    2. Verifique RBAC: `ClusterRoleBinding` excessivo, `subjects` genéricos.
    3. Valide `securityContext`: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities` (drop ALL, add specific).
    4. Confirme ausência de secrets em plaintext (env vars, configmaps).
    5. Verifique `NetworkPolicy` (ausência pode ser um risco).
    6. Analise `hostPath` mounts, `hostNetwork: true`, `hostPID: true`.
    FONTES DE REFERÊNCIA: OWASP K8s Top 10, CIS K8s Benchmark, K8s Pod Security Standards.
    FORMATO DE RESPOSTA (Use tabela Markdown):
    | Severidade | Problema Detectado                     | Impacto Potencial        | Localização (Recurso/Campo) | Correção Recomendada (Exemplo) |
    |------------|----------------------------------------|--------------------------|-----------------------------|--------------------------------|
    | Crítico    | Container rodando como root            | Comprometimento do nó    | Deployment/spec/...         | `securityContext: {runAsUser: 1001, runAsGroup: 1001, runAsNonRoot: true}` |
    | Alto       | `allowPrivilegeEscalation: true`       | Escalação de privilégios | Pod/spec/...                | `allowPrivilegeEscalation: false` |
    | Médio      | Ausência de NetworkPolicy              | Movimentação lateral     | Namespace (implícito)       | Criar NetworkPolicy default deny |
    | Baixo      | Secret em variável de ambiente         | Exposição de credencial  | Deployment/env/...          | Usar `secretKeyRef` ou volume  |
    RESTRIÇÕES:
    - Evite falsos positivos. Analise o contexto.
    - Foque em riscos de segurança concretos no K8s.
    """,
    "recursos": """
    CONTEXTO: Você é um especialista em otimização de recursos Kubernetes.
    TAREFA: Analise a configuração de recursos (CPU/Memória), probes e escalabilidade no template Helm.
    REGRAS OBRIGATÓRIAS:
    1. Verifique `requests` e `limits` para CPU/Memória em todos os containers.
    2. Analise proporção `limits` vs `requests` (limits > requests é normal, mas limites muito altos podem desperdiçar).
    3. Verifique `HorizontalPodAutoscaler` (HPA): métricas (CPU/memória/custom), min/max replicas.
    4. Confirme `livenessProbe`, `readinessProbe`, `startupProbe`: configurações adequadas (timeouts, thresholds).
    5. Analise `PodDisruptionBudget` (PDB): `minAvailable` ou `maxUnavailable`.
    6. Verifique `terminationGracePeriodSeconds`.
    FORMATO DA ANÁLISE (Use Markdown):
    - Liste problemas por prioridade (Alta, Média, Baixa).
    - Dê recomendações específicas (ex: "Adicionar requests/limits", "Ajustar initialDelaySeconds").
    - Explique o impacto (ex: "Sem limits, pode consumir todo o nó", "Probe agressivo causa reinicializações").
    RESTRIÇÕES:
    - Considere trade-offs (ex: performance vs. custo).
    - Não sugira valores exatos sem contexto, mas aponte a ausência ou valores claramente inadequados.
    """,
    "boas_praticas": """
    CONTEXTO: Você é um especialista em arquitetura e boas práticas Helm/Kubernetes.
    TAREFA: Analise o template Helm quanto à organização, manutenibilidade e design.
    REGRAS OBRIGATÓRIAS:
    1. Estrutura do Chart: Presença de `Chart.yaml`, `values.yaml`, `templates/`, `NOTES.txt`.
    2. Values: Padrões seguros, boa parametrização (evitar hardcoding nos templates).
    3. Templates: Uso de helpers (`_helpers.tpl`) para DRY, nomes de recursos padronizados (`{{ include "chart.fullname" . }}`).
    4. Documentação: `README.md` claro, `NOTES.txt` útil, comentários no `values.yaml`.
    5. Labels/Annotations: Uso de labels padrão do Helm (`helm.sh/chart`, `app.kubernetes.io/name`, etc.).
    6. Hooks: Uso apropriado (ex: `pre-install` para validações, `post-install` para setup).
    7. Versionamento: `apiVersion` no `Chart.yaml`, `appVersion`.
    FORMATO DE RESPOSTA (Use Markdown):
    - Avaliação por categoria (Estrutura, Values, Templates, Documentação, Labels).
    - Liste desvios das boas práticas com recomendações e exemplos.
    - Destaque pontos positivos encontrados.
    RESTRIÇÕES:
    - Foco em manutenibilidade e padrões Helm.
    - Alerte sobre mudanças que quebram compatibilidade.
    - Considere legibilidade.
    """
}

# --- Classe Principal do Sistema de Validação ---
class HelmValidationSystem:
    """Sistema para validar templates Helm usando LLMs e ferramentas CLI."""

    def __init__(self, ollama_url, ollama_model):
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.helm_path = self._find_executable("helm")
        self.kubeval_path = self._find_executable("kubeval")
        self.initialize_agents()
        logger.info(f"HelmValidationSystem inicializado com model={ollama_model}, helm={self.helm_path}, kubeval={self.kubeval_path}")

    def _find_executable(self, name):
        """Encontra o caminho de um executável no PATH."""
        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            exe_path = os.path.join(path_dir, name)
            if os.path.exists(exe_path) and os.access(exe_path, os.X_OK):
                return exe_path
        logger.warning(f"Executável '{name}' não encontrado no PATH.")
        return None

    def initialize_agents(self):
        """Inicializa os agentes LLM especializados."""
        self.agents = {}
        llm_config = {
            "config_list": [{
                "model": self.ollama_model,
                "base_url": self.ollama_url,
                "api_type": "ollama",
                "temperature": 0.1, # Temperatura baixa para respostas mais determinísticas
            }]
        }
        for agent_type, prompt in VALIDATION_PROMPTS.items():
            self.agents[agent_type] = AssistantAgent(
                name=f"{agent_type.capitalize()}Agent",
                system_message=prompt,
                llm_config=llm_config
            )
        self.coordinator_agent = AssistantAgent(
            name="ValidationCoordinator",
            system_message="""
            Você é um coordenador de validação de templates Helm. Sua função é:
            1. Receber os resultados das análises dos agentes especializados (sintaxe, segurança, etc.) e das ferramentas CLI (helm lint, kubeval).
            2. Integrar esses resultados em um relatório consolidado e coerente em Markdown.
            3. Priorizar os problemas mais críticos no sumário executivo.
            4. O relatório final DEVE incluir:
               - Sumário Executivo: Pontos críticos e avaliação geral.
               - Detalhes por Categoria: Seções separadas para Sintaxe, Segurança, Recursos, Boas Práticas e Validações Técnicas.
               - Lista Completa: Todos os problemas encontrados, agrupados por categoria.
            Seja conciso e direto ao ponto. Use formatação Markdown para clareza.
            """,
            llm_config=llm_config
        )
        logger.info(f"Agentes LLM inicializados: {list(self.agents.keys())}, Coordinator")

    def _run_command(self, command, cwd=None):
        """Executa um comando de shell e retorna stdout ou erro."""
        logger.debug(f"Executando comando: {' '.join(command)} em {cwd or os.getcwd()}")
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False, # Não lança exceção em caso de erro, tratamos pelo returncode
                cwd=cwd
            )
            if result.returncode == 0:
                logger.debug(f"Comando bem-sucedido. Output: {result.stdout[:100]}...")
                # Limita o tamanho do output para evitar sobrecarregar
                return result.stdout if len(result.stdout) < 5000 else result.stdout[:5000] + "\n... (output truncado)"
            else:
                logger.warning(f"Comando falhou (código {result.returncode}). Erro: {result.stderr}")
                return f"ERRO (Código {result.returncode}): {result.stderr}"
        except FileNotFoundError:
            logger.error(f"Erro: Comando '{command[0]}' não encontrado.")
            return f"ERRO: Comando '{command[0]}' não encontrado. Verifique a instalação e o PATH."
        except Exception as e:
            logger.exception(f"Erro inesperado ao executar comando: {command}")
            return f"Erro inesperado ao executar comando: {str(e)}"

    def helm_lint(self, chart_dir):
        """Executa 'helm lint --strict' no diretório do chart."""
        if not self.helm_path:
            return "ERRO: Executável 'helm' não encontrado."
        # Verifica se Chart.yaml existe, senão o lint falha
        if not os.path.exists(os.path.join(chart_dir, "Chart.yaml")):
             logger.warning(f"Arquivo Chart.yaml não encontrado em {chart_dir}. 'helm lint' pode falhar.")
             # Poderia criar um dummy Chart.yaml aqui se necessário
        return self._run_command([self.helm_path, "lint", "--strict", chart_dir], cwd=chart_dir)

    def helm_template_validate(self, chart_dir):
        """Executa 'helm template' e valida com 'kubeval'."""
        if not self.helm_path:
            return "ERRO: Executável 'helm' não encontrado."
        if not self.kubeval_path:
            return "ERRO: Executável 'kubeval' não encontrado. Instale-o para validação de schema."

        logger.info(f"Executando helm template | kubeval em {chart_dir}")
        try:
            # Executa helm template
            template_process = subprocess.Popen(
                [self.helm_path, "template", chart_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=chart_dir
            )
            template_stdout, template_stderr = template_process.communicate()

            if template_process.returncode != 0:
                logger.warning(f"helm template falhou: {template_stderr}")
                return f"ERRO (helm template): {template_stderr}"
            if not template_stdout.strip():
                 logger.warning(f"helm template não gerou output para {chart_dir}")
                 return "AVISO: 'helm template' não gerou nenhum manifesto YAML."

            # Executa kubeval com o output do helm template
            kubeval_process = subprocess.Popen(
                [self.kubeval_path, "--strict", "-"], # Lê do stdin
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            kubeval_stdout, kubeval_stderr = kubeval_process.communicate(input=template_stdout)

            if kubeval_process.returncode == 0:
                logger.info("kubeval passou.")
                # Retorna uma mensagem de sucesso ou o output se for relevante
                return kubeval_stdout if kubeval_stdout else "Validação Kubeval bem-sucedida (sem output)."
            else:
                logger.warning(f"kubeval falhou: {kubeval_stderr}")
                # Retorna o erro do kubeval que geralmente é mais informativo
                return f"ERRO (kubeval): {kubeval_stderr or kubeval_stdout}"

        except FileNotFoundError as e:
             logger.error(f"Erro: Comando '{e.filename}' não encontrado.")
             return f"ERRO: Comando '{e.filename}' não encontrado. Verifique a instalação e o PATH."
        except Exception as e:
            logger.exception("Erro inesperado durante helm template | kubeval")
            return f"Erro inesperado durante validação com Kubeval: {str(e)}"

    def check_dependencies(self, chart_dir):
        """Executa 'helm dependency build' se Chart.yaml existir."""
        if not self.helm_path:
            return "ERRO: Executável 'helm' não encontrado."
        chart_yaml_path = os.path.join(chart_dir, "Chart.yaml")
        if os.path.exists(chart_yaml_path):
            # Verifica se há dependências declaradas
            try:
                with open(chart_yaml_path, 'r') as f:
                    chart_data = yaml.safe_load(f)
                if chart_data and 'dependencies' in chart_data and chart_data['dependencies']:
                     logger.info(f"Verificando dependências em {chart_dir}")
                     return self._run_command([self.helm_path, "dependency", "build", chart_dir], cwd=chart_dir)
                else:
                    return "Nenhuma dependência declarada no Chart.yaml."
            except Exception as e:
                logger.error(f"Erro ao ler Chart.yaml para verificar dependências: {e}")
                return f"Erro ao ler Chart.yaml: {str(e)}"
        else:
            return "Arquivo Chart.yaml não encontrado, impossível verificar dependências."

    def validate_template_content(self, template_content):
        """Executa a validação completa do conteúdo do template YAML."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "llm_validations": {},
            "technical_validations": {}
        }
        logger.info("Iniciando validação de template.")

        # Usar diretório temporário seguro
        with tempfile.TemporaryDirectory(prefix="helm_validation_") as temp_dir:
            logger.info(f"Diretório temporário criado: {temp_dir}")

            # --- Preparação do Ambiente Temporário ---
            # Salva o conteúdo como um arquivo de template (ex: deployment.yaml)
            # Para que helm lint/template funcione minimamente, precisamos de uma estrutura de chart
            templates_dir = os.path.join(temp_dir, "templates")
            os.makedirs(templates_dir, exist_ok=True)
            template_filename = "uploaded_template.yaml" # Nome genérico
            template_path = os.path.join(templates_dir, template_filename)
            with open(template_path, "w") as f:
                f.write(template_content)
            logger.debug(f"Conteúdo do template salvo em {template_path}")

            # Cria um Chart.yaml mínimo para satisfazer o helm lint/template
            chart_yaml_content = """
apiVersion: v2
name: temp-chart
description: A temporary Helm chart for validation
version: 0.1.0
appVersion: "1.0"
"""
            chart_yaml_path = os.path.join(temp_dir, "Chart.yaml")
            with open(chart_yaml_path, "w") as f:
                f.write(chart_yaml_content)
            logger.debug(f"Chart.yaml mínimo criado em {chart_yaml_path}")

            # --- Execução das Validações Técnicas ---
            logger.info("Executando validações técnicas CLI...")
            results["technical_validations"]["helm_lint"] = self.helm_lint(temp_dir)
            results["technical_validations"]["kubeval"] = self.helm_template_validate(temp_dir)

            # --- Execução das Validações LLM (Paralelo) ---
            logger.info("Executando validações LLM em paralelo...")
            llm_tasks = {}
            # Mensagem base para os agentes LLM
            message_template = f"Analise o seguinte template Helm Kubernetes:\n\n```yaml\n{template_content}\n```\n\nForneça sua análise de acordo com seu CONTEXTO e TAREFA."

            with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
                # Submete cada tarefa de validação LLM com o formato correto de mensagem
                future_to_agent = {
                    executor.submit(
                        agent.generate_reply, 
                        [{"role": "user", "content": message_template}]
                    ): agent_type
                    for agent_type, agent in self.agents.items()
                }
                # Coleta os resultados conforme completam
                for future in future_to_agent:
                    agent_type = future_to_agent[future]
                    try:
                        response = future.result()
                        # Extrai apenas o conteúdo textual da resposta
                        content = extract_llm_content(response)
                        results["llm_validations"][agent_type] = content
                        logger.debug(f"Agente {agent_type} concluiu.")
                    except Exception as exc:
                        logger.exception(f"Agente {agent_type} gerou uma exceção: {exc}")
                        results["llm_validations"][agent_type] = f"ERRO: Falha ao executar agente {agent_type}: {exc}"

            # --- Geração do Relatório Consolidado ---
            logger.info("Gerando relatório consolidado com o Coordinator Agent...")
            summary_message = "Resultados das validações do template Helm:\n\n"

            for val_type, result in results["llm_validations"].items():
                trimmed_result = chunk_message(result) if isinstance(result, str) else "Erro ao obter resultado"
                summary_message += f"### Análise de {val_type.capitalize()}\n{trimmed_result}\n\n"

            cli_summary = "## Validações Técnicas (CLI)\n"
            for tool, output in results["technical_validations"].items():
                tool_name = tool.replace('_', ' ').title()
                
                if len(output) > 500:  # Limite arbitrário para saídas de ferramentas
                    output = output[:497] + "..."
                cli_summary += f"### {tool_name}\n```\n{output}\n```\n\n"

            summary_message += cli_summary
            summary_message += "\n---\nTAREFA: Com base nos resultados acima, produza um relatório consolidado em Markdown, priorizando os problemas críticos."

            try:
                logger.info("Tamanho do prompt final: %d caracteres", len(summary_message))
                
                # Evite tokens duplos BOS adicionando contexto específico 
                formatted_message = [{"role": "system", "content": "Você é um especialista em avaliação de templates Helm."}, 
                                    {"role": "user", "content": summary_message}]
                                    
                summary_response = self.coordinator_agent.generate_reply(formatted_message)
                results["summary"] = extract_llm_content(summary_response)
                logger.info("Relatório consolidado gerado.")
            except Exception as e:
                logger.exception("Erro ao gerar relatório consolidado pelo Coordinator Agent.")
                results["summary"] = f"ERRO: Falha ao gerar o sumário consolidado: {str(e)}"
                # Tente uma versão simplificada como fallback
                results["summary"] = "## Resumo da Análise\n\nNão foi possível gerar um relatório completo devido a limitações do modelo.\n\n### Principais Pontos:\n\n"
                for val_type, result in results["llm_validations"].items():
                    if isinstance(result, str) and len(result) > 10:
                        results["summary"] += f"- **{val_type.capitalize()}**: {result[:100]}...\n"
            return results

# --- Inicialização do Sistema ---
# Cacheia o recurso para evitar recriar agentes a cada interação
@st.cache_resource
def load_validation_system(url, model):
    """Carrega e cacheia a instância do HelmValidationSystem."""
    logger.info(f"Tentando carregar/criar HelmValidationSystem para {url} com {model}")
    return HelmValidationSystem(url, model)

# --- Interface Streamlit ---
st.title("Validador AG2 de Templates Helm para Kubernetes")
st.write("Faça upload de um arquivo YAML de template Helm para análise por Agentes IA e ferramentas CLI.")
st.info("Este sistema usa LLMs locais via Ollama e ferramentas como `helm lint` e `kubeval` (se instalados).")

# Carregar o sistema de validação
try:
    validation_system = load_validation_system(ollama_url, ollama_model)
except Exception as e:
    st.error(f"Falha ao inicializar o sistema de validação: {e}")
    logger.exception("Erro crítico na inicialização do HelmValidationSystem.")
    st.stop()

# Upload do arquivo YAML
uploaded_file = st.file_uploader(
    "Selecione seu template Helm (arquivo YAML único)",
    type=["yaml", "yml"],
    accept_multiple_files=False
)

# Botão de validação e barra de progresso
col1, col2 = st.columns([1, 3])
with col1:
    validation_button = st.button("Validar Template", type="primary", disabled=uploaded_file is None)

# Limpa resultados anteriores se um novo arquivo for carregado ou modelo mudar
if "last_uploaded_filename" not in st.session_state:
     st.session_state.last_uploaded_filename = None
if "last_model" not in st.session_state:
     st.session_state.last_model = None

if (uploaded_file and uploaded_file.name != st.session_state.get("last_uploaded_filename")) or \
   (ollama_model != st.session_state.get("last_model")):
    if "validation_results" in st.session_state:
        del st.session_state["validation_results"]
    if "validation_progress" in st.session_state:
         del st.session_state["validation_progress"]
    st.session_state.last_uploaded_filename = uploaded_file.name if uploaded_file else None
    st.session_state.last_model = ollama_model
    logger.info("Novo arquivo ou modelo detectado, limpando resultados anteriores.")


# Processamento do template
if validation_button and uploaded_file:
    st.session_state.validation_progress = 0
    progress_bar = st.progress(0, text="Iniciando validação...")
    logger.info(f"Botão 'Validar' pressionado para o arquivo: {uploaded_file.name}")

    try:
        # Ler conteúdo do arquivo
        template_content = uploaded_file.getvalue().decode("utf-8")
        progress_bar.progress(10, text="Arquivo lido...")

        try:
            # Tenta carregar, mas não necessariamente interrompe se for erro de template
            list(yaml.safe_load_all(template_content)) # Use safe_load_all para múltiplos documentos
            progress_bar.progress(20, text="Sintaxe YAML básica verificada...")
            logger.debug("Verificação básica de sintaxe YAML passou ou foi ignorada para template.")
        except yaml.YAMLError as e:
            # Verifica se o erro parece ser de template Helm
            if "{{" in template_content and "}}" in template_content:
                 logger.warning(f"Erro de parsing YAML detectado, possivelmente devido a template Helm. Continuando com helm lint/kubeval. Erro: {e}")
                 st.warning(f"Aviso: Erro na validação YAML básica (pode ser sintaxe de template Helm): {e}. As validações Helm/Kubeval prosseguirão.")
                 progress_bar.progress(20, text="Aviso: YAML básico inválido (template?), continuando...")
            else:
                 # Se não parece template, é um erro YAML real
                 st.error(f"Erro crítico de parsing YAML no arquivo: {str(e)}")
                 logger.error(f"Erro crítico de parsing YAML: {e}")
                 st.stop() # Interrompe a execução se o YAML for inválido e não parecer template

        # Processar com o sistema de validação (continua mesmo com warning acima)
        progress_bar.progress(30, text="Iniciando análise completa...")
        with st.spinner("Executando validações LLM e técnicas... Isso pode levar um tempo."):
            results = validation_system.validate_template_content(template_content)
            progress_bar.progress(90, text="Gerando relatório final...")

            # Armazenar resultados na sessão
            st.session_state.validation_results = results
            logger.info("Resultados da validação armazenados na sessão.")

        progress_bar.progress(100, text="Validação concluída!")
        st.success("Validação concluída com sucesso!")

    except Exception as e:
        st.error(f"Erro inesperado durante a validação: {str(e)}")
        logger.exception("Erro inesperado no fluxo de validação principal.")
        if "validation_progress" in st.session_state:
             del st.session_state["validation_progress"] # Limpa progresso em caso de erro

# Mostrar resultados quando disponíveis
if "validation_results" in st.session_state:
    results = st.session_state.validation_results
    
    # Verificação adicional para evitar erro com resultados nulos
    if results is None:
        st.error("A validação não retornou resultados. Tente novamente ou escolha outro arquivo/modelo.")
    else:
        st.divider()
        st.header("Relatório de Validação Consolidado")

        if "summary" in results and results["summary"]:
            st.markdown(results["summary"])
        else:
            st.warning("O relatório consolidado não pôde ser gerado.")

    st.subheader("Detalhes das Validações")

    # Abas para resultados específicos
    tab_names = ["Sumário"] + \
                [t.capitalize() for t in VALIDATION_PROMPTS.keys()] + \
                ["Técnico (CLI)"]

    tabs = st.tabs(tab_names)

    # Tab Sumário (já exibido acima)
    with tabs[0]:
        st.info("O sumário consolidado gerado pelo Agente Coordenador é exibido acima.")
        st.write(f"Validação realizada em: {results.get('timestamp', 'N/A')}")
        st.write(f"Modelo LLM utilizado: {ollama_model}")

    # Abas de Validação LLM
    llm_validation_keys = list(VALIDATION_PROMPTS.keys())
    for i, key in enumerate(llm_validation_keys):
        with tabs[i + 1]:
            st.subheader(f"Análise de {key.capitalize()}")
            if key in results.get("llm_validations", {}):
                st.markdown(results["llm_validations"][key])
            else:
                st.warning(f"Resultado da validação de {key} não disponível.")

    # Tab Técnico (CLI)
    with tabs[len(llm_validation_keys) + 1]:
        st.subheader("Validações Técnicas (CLI)")
        if "technical_validations" in results:
            for tool, output in results["technical_validations"].items():
                 tool_name = tool.replace('_', ' ').title()
                 with st.expander(f"Resultado do {tool_name}", expanded="ERRO" in output):
                     if "ERRO:" in output:
                         st.error(output)
                     elif "AVISO:" in output:
                          st.warning(output)
                     else:
                         st.code(output, language="bash")
        else:
            st.warning("Resultados das validações técnicas não disponíveis.")

# --- Rodapé ---
st.sidebar.divider()
st.sidebar.subheader("Sobre")
st.sidebar.info(
    """
    **Validador AG2 de Templates Helm**

    Utiliza agentes IA (AutoGen/AG2 + Ollama) e ferramentas CLI (`helm`, `kubeval`)
    para análise multifacetada de templates Helm.

    **Categorias de Análise:**
    - Sintaxe e Estrutura YAML/Go Template
    - Segurança (CIS Benchmark, OWASP K8s)
    - Otimização de Recursos (CPU/Memória, Probes)
    - Boas Práticas Helm (Estrutura, Labels, Docs)
    - Validação Técnica (Lint, Schema K8s)
    """
)
st.sidebar.caption(f"v1.1.0 | Data: {datetime.now().strftime('%Y-%m-%d')}")