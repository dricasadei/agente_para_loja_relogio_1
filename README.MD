# Chat Relógio DeepDive 1000

Projeto de um chat que auxilia o cliente sobre atendimentos já abertos e sobre dúvidas do relógio DeepDive 1000.
O usuário pode tirar dúvidas de chamados em aberto ou finalizados informando o número do chamado ou para esclarecer dúvidas sobre garantia, autorizadas e funcionamento do relógio.
A aplicação tem um agente que ao receber a pergunta do usuário avalia onde realizar a busca, no banco de dado de registro dos chamados ou na documentação do produto.

## Rodando a aplicação:
- Crie um ambiente virtual próprio e instale as bibliotecas indicadas no documento requirements.txt com o comando: 'pip install -r requirements.txt'.

- Indicado versão do python 3.11 ou inferior.

- No código é usado o modelo da OpenAI, portanto importante indicar a API KEY para acesso ao modelo de LLM.

### Para rodar a aplicação: 
- Inicializar o servidor Flask:
    - python app.py

- Inicializar o chat (outro terminal):
    - python -m streamlit run chat.py