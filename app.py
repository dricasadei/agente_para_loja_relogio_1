''' 
Aplicação Flask que ficará escutando as requisições dos clientes, funionando como uma API.
E também está codificado o agente.
No código abaixo usa-se expressões regulares (regex) para extrair a informação do número do chamado e direcionar para procura no banco de dados.
'''

# Importação das bibliotecas
import os
import glob
import sqlite3
import re
import yaml
from flask import Flask, request, jsonify

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.docstore.document import Document
from langchain.schema import SystemMessage

# Arquivo de configuração
CONFIG_FILE = "config.yaml"
with open(CONFIG_FILE, "r") as file:
    config = yaml.safe_load(file)

# Lê chave openai e armazena em variável de ambiente
os.environ["OPENAI_API_KEY"] = config["api_key"]["key"]

# Nome do banco de dados para dados de suporte
DATABASE_PATH = "atendimentos.db"

# Instanciando o objeto do Flash
app = Flask(__name__)

# Memória e Contexto, usa Dicionário do Python
client_memories = {}  # armazena a conversa
client_context = {}  # armazena o número do atendimento do cliente - pode não ser usado

def get_db_connection():
    '''Faz a conexão com o banco de dados sqlite e retorna dados como dicionário'''
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  
    return conn

def extrair_id_atendimento(question):
    '''Procura no prompt enviado pelo usuário se é informado o número do atendimento'''
    match = re.search(r'atendimento\s*(?:número|de número)?\s*(\d+)', question, re.IGNORECASE)
    return int(match.group(1)) if match else None

def buscar_atendimento(question, client_id):
    '''Percorre os registros no banco de dados e verifica se tem atendimento do cliente. Se sim indica o status ou pergunta se o número de atendimento está correto.
       Caso não seja indicado o número do atendimento é verificado se no contexto do usuário (client_context) tem registro anterior'''
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Busca id do atendimento, pode não existir
    atendimento_id = extrair_id_atendimento(question)
    if atendimento_id:
        cursor.execute("SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,))
        atendimento = cursor.fetchone()
        if atendimento:
            # Guarda atendimento no dicionário de contexto do usuário
            client_context[client_id] = atendimento_id  
            return f"Olá {atendimento['cliente_nome']}, o status do atendimento {atendimento_id} é {atendimento['status']}."
        return f"Não encontrei o atendimento número {atendimento_id}. Pode verificar se o número está correto?"

    # Se fez pergunta sem citar atendimento, usa último contexto
    if client_id in client_context:
        atendimento_id = client_context[client_id]
        cursor.execute("SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,))
        atendimento = cursor.fetchone()
        if atendimento:
            if "defeito" in question.lower():
                return f"O defeito registrado no atendimento {atendimento_id} foi: {atendimento['defeito']}."
            if "descrição" in question.lower():
                return f"A descrição do atendimento {atendimento_id} é: {atendimento['descricao']}."
            if "data" in question.lower():
                return f"A data do atendimento {atendimento_id} foi {atendimento['data']}."
            if "status" in question.lower():
                return f"O status do atendimento {atendimento_id} é {atendimento['status']}."

    # Se for uma pergunta genérica de atendimento
    if "atendimento" in question.lower():
        return "Olá, para Informações sobre atendimento é preciso o número do atendimento"
    return None

def load_documents(folder_path):
    '''Carrega os documentos sobre o produto:Autorizadas.txt, Garantia.txt e Manual.txt e retorna a lista documents'''
    documents = []
    for filepath in glob.glob(os.path.join(folder_path, "*.txt")):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            documents.append(Document(page_content=content, metadata={"source": filepath}))
    return documents

# Carrega os documentos
documents = load_documents("documents")

# Cria embeddings com API da OpenAI
embeddings = OpenAIEmbeddings()

# Cria vectorstore com FAISS
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
    "Responda sempre de maneira clara e objetiva, priorizando a precisão das informações."
    "Caso a pergunta não esteja relacionada ao atendimento ao cliente, especificações de relógios, garantias, manutenções ou suporte técnico, responda: 'Desculpe, mas não posso responder a esse tipo de pergunta.'"
))

# Cria retriever a partir do vectorstore para fazer a busca por similaridade
retriever = vectorstore.as_retriever()

# Aplicação Flask
@app.route('/ask', methods=['POST'])
def ask():
    '''Enpoint que recebe e trata a pergunta do usário e retorna a resposta do modelo'''
    data = request.get_json()
    if not data or "client_id" not in data or "question" not in data:
        return jsonify({"error": "Requisição inválida. Forneça 'client_id' e 'question'."}), 400

    client_id = data["client_id"]
    question = data["question"]

    # Verifica se é sobre atendimento chamando a função buscar_atendimento()
    atendimento_resposta = buscar_atendimento(question, client_id)
    if atendimento_resposta:
        return jsonify({"answer": atendimento_resposta})

    # Recupera ou cria a memória de conversa
    if client_id not in client_memories:
        client_memories[client_id] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    # Prompt de orientação a LLMs a memória (system_message)
    memory = client_memories[client_id]
    memory.chat_memory.messages.append(system_message)
    

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
