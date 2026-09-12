import sqlite3
import json
import os
import shutil
from datetime import datetime
from projeto_ginasio.config import DADOS

DB_PATH = os.path.join(DADOS, "fitcontrol.db")
BACKUP_DIR = os.path.join(DADOS, "backups")

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _init_database():
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Tabela de alunos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            telemovel TEXT NOT NULL,
            documento TEXT NOT NULL UNIQUE,
            plano TEXT NOT NULL,
            foto TEXT,
            embedding TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de alunos excluídos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos_excluidos (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            telemovel TEXT NOT NULL,
            documento TEXT NOT NULL,
            plano TEXT NOT NULL,
            foto TEXT,
            embedding TEXT,
            data_exclusao TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de funcionários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    ''')
    
    # Tabela de pagamentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_aluno INTEGER NOT NULL,
            plano TEXT NOT NULL,
            valor REAL NOT NULL,
            data_pagamento TEXT NOT NULL,
            data_vencimento TEXT NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY (id_aluno) REFERENCES alunos(id)
        )
    ''')
    
    # Tabela de presenças
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS presencas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_aluno INTEGER NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            FOREIGN KEY (id_aluno) REFERENCES alunos(id)
        )
    ''')
    
    # Tabela de logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'geral',
            evento TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()


def _migrar_esquema():
    """Aplica migrações de esquema a bases de dados já existentes."""
    conn = _get_connection()
    cursor = conn.cursor()

    # Adicionar coluna 'tipo' à tabela logs, caso ainda não exista
    colunas = [row[1] for row in cursor.execute('PRAGMA table_info(logs)')]
    if 'tipo' not in colunas:
        try:
            cursor.execute("ALTER TABLE logs ADD COLUMN tipo TEXT NOT NULL DEFAULT 'geral'")
            # Assume que os logs antigos são do tipo 'geral'
            print("Coluna 'tipo' adicionada à tabela logs.")
        except Exception as e:
            print(f"Não foi possível adicionar a coluna 'tipo': {e}")

    # Remover a tabela 'historico_acessos' (Histórico de Acessos foi abolido;
    # todos os registos passam a viver na tabela 'logs' com a coluna 'tipo')
    tabelas = [row[0] for row in cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='historico_acessos'"
    )]
    if tabelas:
        try:
            cursor.execute("DROP TABLE IF EXISTS historico_acessos")
            print("Tabela 'historico_acessos' removida (abolido o Histórico de Acessos).")
        except Exception as e:
            print(f"Não foi possível remover a tabela 'historico_acessos': {e}")

    conn.commit()
    conn.close()

def migrate_from_json():
    """Migra dados dos arquivos JSON para o banco de dados SQLite."""
    from projeto_ginasio.config import (
        ARQUIVO, ARQUIVO_ALUNOS_EXCLUIDOS, ARQUIVO_FUNCIONARIOS,
        ARQUIVO_PAGAMENTOS, ARQUIVO_PRESENCAS, ARQUIVO_LOG,
        ARQUIVO_HISTORICO_ACESSOS
    )
    
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Migrar alunos
    if os.path.exists(ARQUIVO):
        try:
            with open(ARQUIVO, 'r', encoding='utf-8') as f:
                alunos = json.load(f)
                for aluno in alunos:
                    embedding_json = json.dumps(aluno.get('embedding')) if aluno.get('embedding') else None
                    cursor.execute('''
                        INSERT OR REPLACE INTO alunos 
                        (id, nome, telemovel, documento, plano, foto, embedding)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        aluno['id'], aluno['nome'], aluno['telemovel'],
                        aluno['documento'], aluno['plano'], aluno.get('foto'),
                        embedding_json
                    ))
            print("Alunos migrados com sucesso.")
        except Exception as e:
            print(f"Erro ao migrar alunos: {e}")
    
    # Migrar alunos excluídos
    if os.path.exists(ARQUIVO_ALUNOS_EXCLUIDOS):
        try:
            with open(ARQUIVO_ALUNOS_EXCLUIDOS, 'r', encoding='utf-8') as f:
                alunos_excluidos = json.load(f)
                for aluno in alunos_excluidos:
                    embedding_json = json.dumps(aluno.get('embedding')) if aluno.get('embedding') else None
                    cursor.execute('''
                        INSERT OR REPLACE INTO alunos_excluidos 
                        (id, nome, telemovel, documento, plano, foto, embedding, data_exclusao)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        aluno['id'], aluno['nome'], aluno['telemovel'],
                        aluno['documento'], aluno['plano'], aluno.get('foto'),
                        embedding_json, aluno.get('data_exclusao', '')
                    ))
            print("Alunos excluídos migrados com sucesso.")
        except Exception as e:
            print(f"Erro ao migrar alunos excluídos: {e}")
    
    # Migrar funcionários
    if os.path.exists(ARQUIVO_FUNCIONARIOS):
        try:
            with open(ARQUIVO_FUNCIONARIOS, 'r', encoding='utf-8') as f:
                funcionarios = json.load(f)
                for func in funcionarios:
                    cursor.execute('''
                        INSERT OR REPLACE INTO funcionarios 
                        (id, nome, usuario, senha, tipo)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        func.get('id'), func['nome'], func['usuario'],
                        func['senha'], func['tipo']
                    ))
            print("Funcionários migrados com sucesso.")
        except Exception as e:
            print(f"Erro ao migrar funcionários: {e}")
    
    # Migrar pagamentos
    if os.path.exists(ARQUIVO_PAGAMENTOS):
        try:
            with open(ARQUIVO_PAGAMENTOS, 'r', encoding='utf-8') as f:
                pagamentos = json.load(f)
                for pag in pagamentos:
                    cursor.execute('''
                        INSERT INTO pagamentos 
                        (id_aluno, plano, valor, data_pagamento, data_vencimento, estado)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        pag['id_aluno'], pag['plano'], pag['valor'],
                        pag['data_pagamento'], pag['data_vencimento'], pag['estado']
                    ))
            print("Pagamentos migrados com sucesso.")
        except Exception as e:
            print(f"Erro ao migrar pagamentos: {e}")
    
    # Migrar presenças
    if os.path.exists(ARQUIVO_PRESENCAS):
        try:
            with open(ARQUIVO_PRESENCAS, 'r', encoding='utf-8') as f:
                presencas = json.load(f)
                for pres in presencas:
                    cursor.execute('''
                        INSERT INTO presencas (id_aluno, data, hora)
                        VALUES (?, ?, ?)
                    ''', (pres['id_aluno'], pres['data'], pres['hora']))
            print("Presenças migradas com sucesso.")
        except Exception as e:
            print(f"Erro ao migrar presenças: {e}")
    
    # Migrar logs
    if os.path.exists(ARQUIVO_LOG):
        try:
            with open(ARQUIVO_LOG, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
                for linha in linhas:
                    if ' - ' in linha:
                        partes = linha.split(' - ', 1)
                        if len(partes) == 2:
                            data = partes[0].strip()
                            evento = partes[1].strip()
                            cursor.execute('''
                                INSERT INTO logs (data, evento)
                                VALUES (?, ?)
                            ''', (data, evento))
            print("Logs migrados com sucesso.")
        except Exception as e:
            print(f"Erro ao migrar logs: {e}")
    
    # Migrar histórico de acessos (removido o separado — agora vão para os Logs)
    if os.path.exists(ARQUIVO_HISTORICO_ACESSOS):
        try:
            with open(ARQUIVO_HISTORICO_ACESSOS, 'r', encoding='utf-8') as f:
                historico = json.load(f)
                for reg in historico:
                    cursor.execute('''
                        INSERT INTO logs (data, tipo, evento)
                        VALUES (?, ?, ?)
                    ''', (
                        reg.get('data_acesso', ''),
                        'administracao',
                        f"Acesso {reg.get('tipo', '')} - {reg.get('usuario', '')}"
                    ))
            print("Histórico de acessos migrado para os Logs.")
        except Exception as e:
            print(f"Erro ao migrar histórico de acessos: {e}")
    
    conn.commit()
    conn.close()
    print("Migração concluída!")

# Inicializar o banco de dados ao importar o módulo
if not os.path.exists(DB_PATH):
    _init_database()
    print("Banco de dados SQLite criado com sucesso.")
else:
    print("Banco de dados SQLite já existe.")
    _migrar_esquema()

# Criar diretório de backups
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_database():
    """Cria um backup do banco de dados SQLite."""
    if not os.path.exists(DB_PATH):
        print("Nenhum banco de dados encontrado para backup.")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"fitcontrol_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"Backup criado com sucesso: {backup_path}")
        
        # Manter apenas os últimos 10 backups
        backups = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.startswith("fitcontrol_backup_")],
            reverse=True
        )
        for old_backup in backups[10:]:
            os.remove(os.path.join(BACKUP_DIR, old_backup))
            print(f"Backup antigo removido: {old_backup}")
        
        return True
    except Exception as e:
        print(f"Erro ao criar backup: {e}")
        return False

def restore_database(backup_filename):
    """Restaura um backup específico do banco de dados."""
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    if not os.path.exists(backup_path):
        print(f"Backup não encontrado: {backup_path}")
        return False
    
    try:
        # Backup do banco atual antes de restaurar
        if os.path.exists(DB_PATH):
            temp_backup = os.path.join(BACKUP_DIR, f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            shutil.copy2(DB_PATH, temp_backup)
            print(f"Backup pré-restauração criado: {temp_backup}")
        
        shutil.copy2(backup_path, DB_PATH)
        print(f"Banco de dados restaurado de: {backup_path}")
        return True
    except Exception as e:
        print(f"Erro ao restaurar backup: {e}")
        return False

def list_backups():
    """Lista todos os backups disponíveis."""
    if not os.path.exists(BACKUP_DIR):
        return []
    
    backups = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.startswith("fitcontrol_backup_"):
            path = os.path.join(BACKUP_DIR, filename)
            backups.append({
                'filename': filename,
                'path': path,
                'size': os.path.getsize(path),
                'created': datetime.fromtimestamp(os.path.getctime(path))
            })
    
    return sorted(backups, key=lambda x: x['created'], reverse=True)