import sqlite3


DB_NAME = "atendimentos.db"

def create_database():
    """Cria o banco de dados SQLite e a tabela de atendimentos."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nome TEXT NOT NULL,
            data TEXT NOT NULL,
            status TEXT NOT NULL,
            defeito TEXT NOT NULL,
            descricao TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_sample_data():
    """Insere alguns registros de atendimento no banco de dados."""
    atendimentos = [
        ("João Silva", "2024-02-01", "Em andamento", "Falha na Válvula de Escape de Hélio", "Troca válvula"),
        ("Maria Oliveira", "2024-01-25", "Finalizado", "Relógio Parado", "Substituição da bateria"),
        ("Carlos Souza", "2024-01-30", "Aguardando peça", "Coroa Arranhada", "Pedido de nova coroa em andamento"),
        ("Ana Martins", "2024-02-02", "Cancelado", "Troca do ponteiro dos segundos", "Cliente desistiu do conserto"),
        ("Pedro Santos", "2024-02-03", "Finalizado", "Limpeza", "Limpeza especializada")
    ]
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.executemany('''
        INSERT INTO atendimentos (cliente_nome, data, status, defeito, descricao)
        VALUES (?, ?, ?, ?, ?)
    ''', atendimentos)
    
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    create_database()
    insert_sample_data()
    print("Banco de dados e registros de atendimentos criados com sucesso!")
