import threading
from datetime import datetime

from projeto_ginasio.config import *
from projeto_ginasio.dados import presencas, alunos
from projeto_ginasio.db_adapter import (
    add_presenca,
    save_presencas,
    get_presencas_dia,
    limpar_presencas_anteriores,
)
from modulos.gestao_alunos import escrever_log

# A lista `presencas` é partilhada entre a interface (thread principal) e o
# Face ID (thread em segundo plano). Sem este lock, uma leitura na interface
# ao mesmo tempo que uma escrita do Face ID pode causar erros intermitentes
# ou dados corrompidos.
_presencas_lock = threading.Lock()


# guardar presenças
# ======================================================
def guardar_presencas():
    try:
        with _presencas_lock:
            save_presencas(presencas)
    except Exception as erro:
        raise Exception(f"Não foi possível guardar as presenças: {erro}")


# carregar presenças (histórico diário)
# ======================================================
def carregar_presencas():
    """Limpa as presenças de dias anteriores da tabela e carrega apenas as
    entradas do dia atual. As presenças antigas permanecem registadas nos
    Logs (tipo 'presenca')."""
    try:
        hoje = datetime.now().strftime("%d/%m/%Y")
        limpar_presencas_anteriores(hoje)
        with _presencas_lock:
            presencas[:] = get_presencas_dia(hoje)
    except Exception as erro:
        raise Exception(f"Não foi possível carregar as presenças: {erro}")


# registar presenças
# ======================================================
def registar_presenca(id_aluno):

    # Verificar se o aluno existe
    existe = False

    for aluno in alunos:
        if aluno["id"] == id_aluno:
            existe = True
            break

    if not existe:
        return "ALUNO_NAO_EXISTE"

    hoje = datetime.now().strftime("%d/%m/%Y")

    agora = datetime.now()

    presenca = {
        "id_aluno": id_aluno,
        "data": hoje,
        "hora": agora.strftime("%H:%M")
    }

    with _presencas_lock:
        add_presenca(presenca)
        presencas.append(presenca)

    nome_aluno = ""

    for aluno in alunos:
        if aluno["id"] == id_aluno:
            nome_aluno = aluno["nome"]
            break

    escrever_log(
        f"Entrada do aluno '{nome_aluno}'.",
        tipo="presenca"
    )

    return "OK"