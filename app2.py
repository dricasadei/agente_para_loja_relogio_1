''' 
Aplicação Flask que ficará escutando as requisições dos clientes, funcionando como uma API.
E também está codificado o agente.
No código abaixo o próprio modelo avalia a mensagem enviada pelo usuário para verificar se é referente a algum chamado aberto.
'''

import os
import glob
import sqlite3
import json
import yaml
from flask import Flask, request, jsonify

# LangChain
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.docstore.document import Document
from langchain.schema import SystemMessage, HumanMessage

# Arquivo de configuração
CONFIG_FILE = "config.yaml"
with open(CONFIG_FILE, "r") as file:
    config = yaml.safe_load(file)

# Lê chave openai e armazena em variável de ambiente
os.environ["OPENAI_API_KEY"] = config["api_key"]["key"]

# Nome do banco de dados para dados de suporte
DATABASE_PATH = "atendimentos.db"

# Flask
app = Flask(__name__)

# Memória e Contexto, usa Dicionário do Python
client_memories = {}  # conversa
client_context = {}  # número do atendimento do cliente - pode não ser usado

# Conecta com bd e retorna dados como dicionário
def get_db_connection():
    """Conecta ao banco de dados e configura para retornar dicionários."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  
    return conn

# carrega documentos e retorna uma lista 
def load_documents(folder_path):
    """Carrega documentos TXT da pasta indicada e retorna uma lista de Documentos."""
    documents = []
    for filepath in glob.glob(os.path.join(folder_path, "*.txt")):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            documents.append(Document(page_content=content, metadata={"source": filepath}))
    return documents

# Carrega os documentos 
documents = load_documents("documents")

# Cria vectorstore com FAISS
embeddings = OpenAIEmbeddings()

vectorstore = FAISS.from_documents(documents, embeddings)

# Inicializa o modelo de chat com a mensagem do sistema
# Temperatura zero = respostas determinísticas
model = config["model"]["name"]
chat = ChatOpenAI(model=model, temperature=0)

# Definir o comportamento do agente
system_message = SystemMessage(content=(
    "Você é um assistente virtual especializado no atendimento ao cliente para uma renomada marca de relógios. "
    "Sua função é responder perguntas sobre especificações dos produtos, garantias, manutenções e suporte técnico. "
    "Além disso, você também fornece informações sobre atendimentos na assistência técnica, incluindo status, defeitos relatados e datas dos atendimentos. "
    "Responda sempre de maneira clara e objetiva, priorizando a precisão das informações. "
    "Caso a pergunta não esteja relacionada ao atendimento ao cliente, especificações de relógios, garantias, manutenções ou suporte técnico, "
    "responda: 'Desculpe, mas não posso responder a esse tipo de pergunta.'"
))

# Cria o retriever a partir do vectorstore
retriever = vectorstore.as_retriever()

# Avaliação se é atendimento através de LLM
def avaliar_atendimento(question):
    system_prompt = (
        "Você é um assistente que analisa perguntas para determinar se elas se referem a um atendimento técnico. "
        "Se a pergunta for sobre atendimento, extraia o número do atendimento (um número inteiro) se presente e identifique o tipo de consulta, "
        "que pode ser: 'status', 'defeito', 'descrição' ou 'data'. "
        "Caso a pergunta não seja sobre atendimento, retorne is_atendimento como false. "
        "Sua resposta DEVE ser **exclusivamente** um JSON válido, sem qualquer texto adicional, no seguinte formato: "
        '{"is_atendimento": <true ou false>, "ticket_id": <número ou null>, "consulta": <"status", "defeito", "descrição", "data" ou null>}.'
    )
    human_prompt = f"Pergunta: \"{question}\""
    response = chat([SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)])
    response_content = response.content.strip()
    return json.loads(response_content)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    if not data or "client_id" not in data or "question" not in data:
        return jsonify({"error": "Requisição inválida. Forneça 'client_id' e 'question'."}), 400

    client_id = data["client_id"]
    question = data["question"]

    # Verifica se é sobre atendimento usando LLM
    atendimento_info = avaliar_atendimento(question)
    if atendimento_info.get("is_atendimento"):
        ticket_id = atendimento_info.get("ticket_id")
        consulta = atendimento_info.get("consulta")
        
        # Se atendimento não foi identificado, tenta usar o último contexto salvo
        if not ticket_id and client_id in client_context:
            ticket_id = client_context[client_id]
        if not ticket_id:
            return jsonify({"answer": "Por favor, informe o número do atendimento para que eu possa buscar as informações."})
        
        # Consulta o banco de dados pelo numero do chamado
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM atendimentos WHERE id = ?", (ticket_id,))
        atendimento = cursor.fetchone()
        if atendimento:
            client_context[client_id] = ticket_id  # atualiza o contexto do cliente
            if consulta == "defeito":
                answer = f"O defeito registrado no atendimento {ticket_id} foi: {atendimento['defeito']}."
            elif consulta == "descrição":
                answer = f"A descrição do atendimento {ticket_id} é: {atendimento['descricao']}."
            elif consulta == "data":
                answer = f"A data do atendimento {ticket_id} foi: {atendimento['data']}."
            elif consulta == "status":
                answer = f"O status do atendimento {ticket_id} é: {atendimento['status']}."
            else:
                answer = f"Olá {atendimento['cliente_nome']}, o status do atendimento {ticket_id} é: {atendimento['status']}."
        else:
            answer = f"Não encontrei o atendimento número {ticket_id}. Verifique se o número está correto."
        return jsonify({"answer": answer})
    
    # Se não for sobre atendimento, segue com a cadeia padrão
    if client_id not in client_memories:
        client_memories[client_id] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    memory = client_memories[client_id]
    
    # Cria a cadeia de conversação com Retrieval
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=chat,
        retriever=retriever,
        memory=memory
    )

    # Executa a cadeia com a pergunta do usuário
    result = qa_chain.invoke({"question": question})
    answer = result.get("answer", "")

    return jsonify({"answer": answer})

if __name__ == '__main__':
    # Servidor Flask na porta 5000
    app.run(port=5000, debug=True)
