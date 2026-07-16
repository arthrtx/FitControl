import json
import os
from datetime import datetime

from projeto_ginasio.config import *
from projeto_ginasio.dados import presencas, alunos
from modulos.gestao_alunos import escrever_log


# guardar presenças
# ======================================================
def guardar_presencas():
    try:
        with open(ARQUIVO_PRESENCAS, "w", encoding="utf-8") as ficheiro:
            json.dump(presencas, ficheiro, indent=4, ensure_ascii=False)

    except Exception as erro:
        raise Exception(
            f"Não foi possível guardar as presenças: {erro}"
        )


# carregar presenças
# ======================================================
def carregar_presencas():

    if not os.path.exists(ARQUIVO_PRESENCAS):

        presencas.clear()

        guardar_presencas()

        return

    try:

        with open(ARQUIVO_PRESENCAS, "r", encoding="utf-8") as ficheiro:

            dados = json.load(ficheiro)

            presencas.clear()

            presencas.extend(dados)

    except Exception as erro:

        raise Exception(
            f"Não foi possível carregar as presenças: {erro}"
        )


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

    # Verificar se já existe presença hoje
    for presenca in presencas:
        if (
            presenca["id_aluno"] == id_aluno and
            presenca["data"] == hoje
        ):
            return "PRESENCA_JA_REGISTADA"

    agora = datetime.now()

    presenca = {
        "id_aluno": id_aluno,
        "data": hoje,
        "hora": agora.strftime("%H:%M")
    }

    presencas.append(presenca)

    guardar_presencas()

    nome_aluno = ""

    for aluno in alunos:
        if aluno["id"] == id_aluno:
            nome_aluno = aluno["nome"]
            break

    escrever_log(
        f"Entrada do aluno '{nome_aluno}'."
    )

    return "OK"