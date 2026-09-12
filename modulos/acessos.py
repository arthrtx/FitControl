"""Gestão de logs/registos do sistema — baseados na tabela SQLite 'logs'.

Todos os registos (presenças, pagamentos, alunos, funcionários, acesso/adm)
são guardados numa única fonte de dados: a tabela 'logs', identificados pela
coluna 'tipo'. Este módulo apenas fornece facilitadores de leitura e limpeza.
O Histórico de Acessos separado foi removido.
"""
from datetime import datetime

from projeto_ginasio.db_adapter import (
    get_logs_por_tipo,
    get_logs,
    limpar_logs_por_tipo,
)


def data_atual():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


# LOGS DE ADMINISTRAÇÃO / ACESSOS
# ================================
def listar_administracao(limite=None):
    """Devolve os logs de administração/acessos (login, logout, permissões,
    apagar históricos, etc.)."""
    return get_logs_por_tipo("administracao", limite=limite)


# ARQUIVO DE PRESENÇAS (histórico permanente)
# ============================================
def arquivo_presencas(limite=None):
    """Devolve o histórico permanente das presenças, obtido exclusivamente
    a partir dos Logs do tipo 'presenca'."""
    return get_logs_por_tipo("presenca", limite=limite)


def apagar_arquivo_presencas():
    """Apaga permanentemente o histórico de presenças (apenas administrador).

    Como o histórico diário guarda apenas as entradas do dia atual (nas
    presenças do sistema) e o histórico permanente fica nos Logs, apagar o
    arquivo de presenças também limpa as presenças do dia atual."""
    from modulos import presencas
    from projeto_ginasio.db_adapter import limpar_presencas_anteriores
    limpar_logs_por_tipo("presenca")
    # Limpar também as presenças do dia atual (tabela e lista em memória)
    hoje = datetime.now().strftime("%d/%m/%Y")
    limpar_presencas_anteriores(hoje)
    with presencas._presencas_lock:
        presencas.presencas[:] = []


# LOGS GERAIS
# ================================
def todos_logs(limite=1000):
    return get_logs()[:limite] if limite else get_logs()


def obter_tipos():
    from projeto_ginasio.db_adapter import get_tipos_logs
    return get_tipos_logs()
