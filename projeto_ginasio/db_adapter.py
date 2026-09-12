"""Adaptador para migrar o sistema de arquivos JSON para SQLite mantendo compatibilidade."""
import json
import sqlite3
from datetime import datetime
from projeto_ginasio.database import _get_connection, migrate_from_json
from projeto_ginasio.config import DADOS
import os

# Verificar se precisa migrar
_migration_done = False
def check_and_migrate():
    global _migration_done
    if _migration_done:
        return False
    
    db_path = os.path.join(DADOS, "fitcontrol.db")
    if not os.path.exists(db_path):
        print("Iniciando migração de JSON para SQLite...")
        migrate_from_json()
        _migration_done = True
        return True
    else:
        print(f"Banco de dados encontrado em: {db_path}")
        _migration_done = True
        return False

# Funções para alunos
def get_alunos():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM alunos')
    rows = cursor.fetchall()
    alunos = []
    for row in rows:
        aluno = dict(row)
        if aluno['embedding']:
            try:
                # Tentar carregar como JSON compacto
                embedding_data = json.loads(aluno['embedding'])
                if isinstance(embedding_data, list):
                    aluno['embedding'] = embedding_data
                else:
                    aluno['embedding'] = None
            except:
                aluno['embedding'] = None
        alunos.append(aluno)
    conn.close()
    return alunos

def save_alunos(alunos_list):
    conn = _get_connection()
    cursor = conn.cursor()
    for aluno in alunos_list:
        embedding = aluno.get('embedding')
        if embedding:
            # Converter para lista e salvar como JSON compacto
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            embedding_json = json.dumps(embedding, separators=(',', ':'))  # JSON compacto
        else:
            embedding_json = None
        cursor.execute('''
            INSERT OR REPLACE INTO alunos 
            (id, nome, telemovel, documento, plano, foto, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            aluno['id'], aluno['nome'], aluno['telemovel'],
            aluno['documento'], aluno['plano'], aluno.get('foto'),
            embedding_json
        ))
    conn.commit()
    conn.close()

def add_aluno(aluno):
    conn = _get_connection()
    cursor = conn.cursor()
    embedding = aluno.get('embedding')
    if embedding:
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()
        embedding_json = json.dumps(embedding, separators=(',', ':'))
    else:
        embedding_json = None
    cursor.execute('''
        INSERT INTO alunos (id, nome, telemovel, documento, plano, foto, embedding)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        aluno['id'], aluno['nome'], aluno['telemovel'],
        aluno['documento'], aluno['plano'], aluno.get('foto'),
        embedding_json
    ))
    conn.commit()
    conn.close()

def update_aluno(aluno):
    conn = _get_connection()
    cursor = conn.cursor()
    embedding = aluno.get('embedding')
    if embedding:
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()
        embedding_json = json.dumps(embedding, separators=(',', ':'))
    else:
        embedding_json = None
    cursor.execute('''
        UPDATE alunos SET nome=?, telemovel=?, documento=?, plano=?, foto=?, embedding=?
        WHERE id=?
    ''', (
        aluno['nome'], aluno['telemovel'], aluno['documento'],
        aluno['plano'], aluno.get('foto'), embedding_json, aluno['id']
    ))
    conn.commit()
    conn.close()

def delete_aluno(id_aluno):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM alunos WHERE id=?', (id_aluno,))
    conn.commit()
    conn.close()

# Funções para alunos excluídos
def get_alunos_excluidos():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM alunos_excluidos')
    rows = cursor.fetchall()
    alunos = []
    for row in rows:
        aluno = dict(row)
        if aluno['embedding']:
            try:
                embedding_data = json.loads(aluno['embedding'])
                if isinstance(embedding_data, list):
                    aluno['embedding'] = embedding_data
                else:
                    aluno['embedding'] = None
            except:
                aluno['embedding'] = None
        alunos.append(aluno)
    conn.close()
    return alunos

def save_alunos_excluidos(alunos_list):
    conn = _get_connection()
    cursor = conn.cursor()
    for aluno in alunos_list:
        embedding = aluno.get('embedding')
        if embedding:
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            embedding_json = json.dumps(embedding, separators=(',', ':'))
        else:
            embedding_json = None
        cursor.execute('''
            INSERT OR REPLACE INTO alunos_excluidos 
            (id, nome, telemovel, documento, plano, foto, embedding, data_exclusao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            aluno['id'], aluno['nome'], aluno['telemovel'],
            aluno['documento'], aluno['plano'], aluno.get('foto'),
            embedding_json, aluno.get('data_exclusao', '')
        ))
    conn.commit()
    conn.close()

def add_aluno_excluido(aluno):
    conn = _get_connection()
    cursor = conn.cursor()
    embedding = aluno.get('embedding')
    if embedding:
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()
        embedding_json = json.dumps(embedding, separators=(',', ':'))
    else:
        embedding_json = None
    cursor.execute('''
        INSERT INTO alunos_excluidos (id, nome, telemovel, documento, plano, foto, embedding, data_exclusao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        aluno['id'], aluno['nome'], aluno['telemovel'],
        aluno['documento'], aluno['plano'], aluno.get('foto'),
        embedding_json, aluno.get('data_exclusao', '')
    ))
    conn.commit()
    conn.close()

def remove_aluno_excluido(id_aluno):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM alunos_excluidos WHERE id=?', (id_aluno,))
    conn.commit()
    conn.close()

# Funções para funcionários
def get_funcionarios():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM funcionarios')
    rows = cursor.fetchall()
    funcionarios = [dict(row) for row in rows]
    conn.close()
    return funcionarios

def save_funcionarios(funcionarios_list):
    conn = _get_connection()
    cursor = conn.cursor()
    for func in funcionarios_list:
        cursor.execute('''
            INSERT OR REPLACE INTO funcionarios 
            (id, nome, usuario, senha, tipo)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            func.get('id'), func['nome'], func['usuario'],
            func['senha'], func['tipo']
        ))
    conn.commit()
    conn.close()

def add_funcionario(funcionario):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO funcionarios (nome, usuario, senha, tipo)
        VALUES (?, ?, ?, ?)
    ''', (
        funcionario['nome'], funcionario['usuario'],
        funcionario['senha'], funcionario['tipo']
    ))
    conn.commit()
    conn.close()
    return cursor.lastrowid

def update_funcionario(funcionario):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE funcionarios SET nome=?, usuario=?, senha=?, tipo=?
        WHERE id=?
    ''', (
        funcionario['nome'], funcionario['usuario'],
        funcionario['senha'], funcionario['tipo'], funcionario['id']
    ))
    conn.commit()
    conn.close()

def delete_funcionario(id_funcionario):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM funcionarios WHERE id=?', (id_funcionario,))
    conn.commit()
    conn.close()

# Funções para pagamentos
def get_pagamentos():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pagamentos')
    rows = cursor.fetchall()
    pagamentos = [dict(row) for row in rows]
    conn.close()
    return pagamentos

def save_pagamentos(pagamentos_list):
    conn = _get_connection()
    cursor = conn.cursor()
    for pag in pagamentos_list:
        cursor.execute('''
            INSERT OR REPLACE INTO pagamentos 
            (id, id_aluno, plano, valor, data_pagamento, data_vencimento, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            pag.get('id'), pag['id_aluno'], pag['plano'], pag['valor'],
            pag['data_pagamento'], pag['data_vencimento'], pag['estado']
        ))
    conn.commit()
    conn.close()

def add_pagamento(pagamento):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pagamentos (id_aluno, plano, valor, data_pagamento, data_vencimento, estado)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        pagamento['id_aluno'], pagamento['plano'], pagamento['valor'],
        pagamento['data_pagamento'], pagamento['data_vencimento'], pagamento['estado']
    ))
    conn.commit()
    conn.close()
    return cursor.lastrowid

# Funções para presenças
def get_presencas():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM presencas')
    rows = cursor.fetchall()
    presencas = [dict(row) for row in rows]
    conn.close()
    return presencas

def save_presencas(presencas_list):
    conn = _get_connection()
    cursor = conn.cursor()
    for pres in presencas_list:
        cursor.execute('''
            INSERT OR REPLACE INTO presencas (id, id_aluno, data, hora)
            VALUES (?, ?, ?, ?)
        ''', (pres.get('id'), pres['id_aluno'], pres['data'], pres['hora']))
    conn.commit()
    conn.close()

def add_presenca(presenca):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO presencas (id_aluno, data, hora)
        VALUES (?, ?, ?)
    ''', (presenca['id_aluno'], presenca['data'], presenca['hora']))
    conn.commit()
    conn.close()
    return cursor.lastrowid

def get_presencas_dia(data):
    """Devolve as presenças de um determinado dia ('dd/mm/yyyy')."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM presencas WHERE data=? ORDER BY id DESC', (data,))
    rows = cursor.fetchall()
    presencas = [dict(row) for row in rows]
    conn.close()
    return presencas

def limpar_presencas_anteriores(data):
    """Elimina da base de dados todas as presenças anteriores ao dia indicado.
    Usado para manter apenas o histórico diário na tabela 'presencas'."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM presencas WHERE data<>?', (data,))
    conn.commit()
    conn.close()
    return cursor.rowcount

def apagar_historico_pagamentos():
    """Apaga permanentemente todo o histórico de pagamentos da base de dados."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM pagamentos')
    apagados = cursor.rowcount
    conn.commit()
    conn.close()
    return apagados

def delete_pagamento(id_pagamento):
    """Apaga um pagamento específico da base de dados pelo seu id."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM pagamentos WHERE id=?', (id_pagamento,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

# Funções para logs
def add_log(evento, tipo='geral'):
    conn = _get_connection()
    cursor = conn.cursor()
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    cursor.execute(
        'INSERT INTO logs (data, tipo, evento) VALUES (?, ?, ?)',
        (data, tipo, evento)
    )
    conn.commit()
    conn.close()

def get_logs():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 1000')
    rows = cursor.fetchall()
    logs = [dict(row) for row in rows]
    conn.close()
    return logs

def get_logs_por_tipo(tipo, limite=None):
    """Devolve os logs de um determinado tipo (ex.: 'presenca', 'pagamento',
    'administracao'), ordenados do mais recente para o mais antigo."""
    conn = _get_connection()
    cursor = conn.cursor()
    if limite:
        cursor.execute(
            'SELECT * FROM logs WHERE tipo=? ORDER BY id DESC LIMIT ?',
            (tipo, limite)
        )
    else:
        cursor.execute(
            'SELECT * FROM logs WHERE tipo=? ORDER BY id DESC',
            (tipo,)
        )
    rows = cursor.fetchall()
    logs = [dict(row) for row in rows]
    conn.close()
    return logs

def get_tipos_logs():
    """Devolve a lista de tipos existentes na tabela de logs."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT tipo FROM logs ORDER BY tipo')
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return [r['tipo'] for r in rows]

def limpar_logs_por_tipo(tipo):
    """Apaga permanentemente os logs de um determinado tipo."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM logs WHERE tipo=?', (tipo,))
    conn.commit()
    conn.close()

def limpar_todos_logs():
    """Apaga permanentemente todos os logs do sistema (todos os tipos)."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM logs')
    conn.commit()
    conn.close()