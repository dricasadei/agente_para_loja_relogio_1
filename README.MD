# Chat Relógio DeepDive 1000

Projeto de um chat que auxilia o cliente sobre atendimentos já abertos e sobre dúvidas do relógio DeepDive 1000.
O usuário pode tirar dúvidas de chamados em aberto ou finalizados informando o número do chamado ou para esclarecer dúvidas sobre garantia, autorizadas e funcionamento do relógio.
A aplicação tem um agente que ao receber a pergunta do usuário avalia onde realizar a busca, no banco de dado de registro dos chamados ou na documentação do produto.

## Rodando a aplicação
- Crie um ambiente virtual próprio e instale as bibliotecas indicadas no documento requirements.txt com o comando: 'pip install -r requirements.txt'.

- Indicado versão do python 3.11 ou inferior.

- No código é usado o modelo da OpenAI, portanto importante indicar a API KEY para acesso ao modelo de LLM.

### Para rodar a aplicação
- Inicializar o servidor Flask:
    - python app.py

- Inicializar o chat (outro terminal):
    - python -m streamlit run chat.py

## Descrição dos arquivos do projeto
- app.py: código contém a aplicação Flask e a definição do agente que irá verificar, conforme pergunta do usuário, se tiver indicaçõ de número de atendimento irá procurar no banco de dados, caso contrário em algum dos documentos, como manual, garantia e autorizadas. A busca na pergunta do usuário será feita usando expressões regulares.

- app2.py: código contém a aplicação Flask e a definição do agente que irá verificar, conforme pergunta do usuário, se tiver indicaçõ de número de atendimento irá procurar no banco de dados, caso contrário em algum dos documentos, como manual, garantia e autorizadas. A busca na pergunta do usuário será feita usando a LLM.

- chat.py: código da interface da aplicação usando Streamlit.

- cria_db.py: script de criação do arquivo de banco de dados caso necessário modificações ou nova geração do arquivo atendimento.db.

- atendimento.db: arquivo que contém os dados dos chamados.

- relogio.jpg: imagem usada na página do chat.

- requirements.txt: definição das bibliotecas necessárias para o funcionamento da aplicação.

- documents: pasta que contém os documentos: Autorizada.txt, Garantia.txt e Manual.txt com informações sobre o produto.

- config_exemplo.yaml: arquivo de definição do modelo e da chave de acesso da api do modelo utilizado. No caso, o exemplo da OPENAI.


Material referente ao curso: Crie Agentes de Inteligência Artificial: do Zero ao Deploy da Escola de Inteligência Artificial.