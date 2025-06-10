'''Interface da aplicação usando Streamlit'''

import streamlit as st
import requests
import uuid

# Comandos padrão do streamlit, porém mais dificil formatação
#st.title("Abyss Precision")
#st.subheader("Atendimento Exclusivo para DeepDive 1000M")

# Comandos com mesma função dos acima, porém formatados na página
st.markdown("<h1 style='text-align: center;'>Abyss Precision</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Atendimento Exclusivo para DeepDive 1000M</h3>", unsafe_allow_html=True)

# Carrega a imagem centralizada
left_co, cent_co,last_co = st.columns(3)
with cent_co:
    st.image("relogio.jpg", caption="DeepDive 1000M")


# Verifica se o client_id já existe, senão gera um client_id único para a sessão
if "client_id" not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())

# Inicializa histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []

def ask_question(question):
    '''Processa a pergunta feita pelo usuário, verifica o sucesso da resposta e retorna a resposta'''
    
    url = "http://127.0.0.1:5000/ask"
    payload = {
        "client_id": st.session_state.client_id,
        "question": question
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get("answer", "Erro ao obter resposta.")
    return f"Erro: {response.status_code} - {response.text}"

# Exibe histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada do usuário
prompt = st.chat_input("Digite sua pergunta:")
if prompt:
    # Adiciona mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    # Obtém resposta da API
    answer = ask_question(prompt)
    
    # Adiciona resposta ao histórico
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)