import json
import os
from datetime import datetime, timedelta

from projeto_ginasio.Camara import tirarFoto
from projeto_ginasio.config import *
from projeto_ginasio.dados import alunos, alunos_excluidos

# inicialização
# ======================================================
def inicializar():
    carregar_alunos()
    carregar_alunos_excluidos()
    limpar_alunos_expirados()


# guardar alunos
# ======================================================
def guardar_alunos():
    try:
        with open(ARQUIVO, "w", encoding="utf-8") as ficheiro:
            json.dump(alunos, ficheiro, indent=4, ensure_ascii=False)

    except Exception as erro:
        raise Exception(f"Não foi possível guardar os alunos: {erro}")


# logs
# ======================================================
def escrever_log(evento):
    try:
        with open(ARQUIVO_LOG, "a", encoding="utf-8") as ficheiro:
            data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            ficheiro.write(f"{data} - {evento}\n")

    except Exception as erro:
        raise Exception(f"Não foi possível escrever no log: {erro}")


# carregar alunos
# ======================================================
def carregar_alunos():

    if not os.path.exists(ARQUIVO):
        alunos.clear()
        guardar_alunos()
        return

    try:
        with open(ARQUIVO, "r", encoding="utf-8") as ficheiro:
            dados = json.load(ficheiro)

            alunos.clear()
            alunos.extend(dados)

    except Exception as erro:
        raise Exception(f"Não foi possível carregar os alunos: {erro}")


# gerar ID
# ======================================================
def gerar_id():

    if not alunos:
        return 1

    maior = max(aluno["id"] for aluno in alunos)

    return maior + 1


# verificar documento
# ======================================================
def documento_existe(documento):

    for aluno in alunos:
        if aluno["documento"] == documento:
            return True

    return False


# criar alunos
# ======================================================
def criar_aluno(nome, telemovel, documento, plano):
#regras============================
    nome = nome.strip()
    telemovel = telemovel.strip()
    documento = documento.strip()

    if len(nome.split()) < 2:
        return False
    if nome == "":
        return False
        
    if len(documento) > 12:
        return False
    if documento == "":
        return False
        
    if not telemovel.isdigit():
        return False
    if len(telemovel) != 9:
        return False
        
        
    planos_validos = [
        "Diário",
        "Mensal",
        "Trimestral",
        "Anual"
    ]

    if plano not in planos_validos:
            return False


    id_aluno = gerar_id()

    if documento_existe(documento):
            return False


    try:
        caminho_foto = tirarFoto(str(id_aluno))
    except Exception:
        caminho_foto = ""

    if not caminho_foto:
        caminho_foto = "sem_foto"

    novo_aluno = {
        "id": id_aluno,
        "nome": nome,
        "telemovel": telemovel,
        "documento": documento,
        "plano": plano,
        "foto": caminho_foto
    }


    alunos.append(novo_aluno)
    guardar_alunos()
    escrever_log(f"Aluno '{nome}' registado.")

    return True


# listar alunos
# ======================================================
def listar_alunos():

    return sorted(
        alunos,
        key=lambda aluno: aluno["nome"].lower()
    )


# editar alunos
# ======================================================
def editar_aluno(id_aluno, nome, telemovel, documento, plano):
#regras============================
    nome = nome.strip()
    telemovel = telemovel.strip()
    documento = documento.strip()

    if len(nome.split()) < 2:
        return False
    if nome == "":
        return False
        
    if len(documento) > 12:
        return False
    if documento == "":
        return False
        
    if not telemovel.isdigit():
        return False
    if len(telemovel) != 9:
        return False
        
        
    planos_validos = [
        "Diário",
        "Mensal",
        "Trimestral",
        "Anual"
    ]

    if plano not in planos_validos:
        return False


    for outro in alunos:

        if outro["documento"] == documento and outro["id"] != id_aluno:
            return False


    for aluno in alunos:

        if aluno["id"] == id_aluno: 

            aluno["nome"] = nome
            aluno["telemovel"] = telemovel
            aluno["documento"] = documento
            aluno["plano"] = plano

            guardar_alunos()

            escrever_log(f"Aluno '{nome}' editado.")

            return True

    return False


# eliminar alunos
# ======================================================
def eliminar_aluno(id_aluno):

    for aluno in alunos:

        if aluno["id"] == id_aluno:

            aluno_excluido = aluno.copy()

            aluno_excluido["data_exclusao"] = datetime.now().strftime("%d/%m/%Y")

            alunos_excluidos.append(aluno_excluido)

            alunos.remove(aluno)


            guardar_alunos()
            guardar_alunos_excluidos()


            escrever_log(
                f"Aluno '{aluno['nome']}' movido para arquivo de exclusão."
            )

            return True

    return False


# restaurar alunos excluidos
# ======================================================
def restaurar_aluno(id_aluno):

    for aluno in alunos_excluidos:

        if aluno["id"] == id_aluno:

            if documento_existe(aluno["documento"]):
                return False


            aluno.pop("data_exclusao", None)

            alunos.append(aluno)

            alunos_excluidos.remove(aluno)


            guardar_alunos()
            guardar_alunos_excluidos()


            escrever_log(
                f"Aluno '{aluno['nome']}' restaurado."
            )

            return True

    return False


# listar alunos excluidos
# ======================================================
def listar_alunos_excluidos():

    return sorted(
        alunos_excluidos,
        key=lambda aluno: aluno["nome"].lower()
    )


# carregar alunos excluidos
# ======================================================
def carregar_alunos_excluidos():

    if not os.path.exists(ARQUIVO_ALUNOS_EXCLUIDOS):

        alunos_excluidos.clear()

        guardar_alunos_excluidos()

        return


    try:

        with open(ARQUIVO_ALUNOS_EXCLUIDOS, "r", encoding="utf-8") as ficheiro:

            dados = json.load(ficheiro)

            alunos_excluidos.clear()

            alunos_excluidos.extend(dados)


    except Exception as erro:

        raise Exception(
            f"Não foi possível carregar alunos excluídos: {erro}"
        )


# guardar alunos excluidos
# ======================================================
def guardar_alunos_excluidos():

    try:

        with open(ARQUIVO_ALUNOS_EXCLUIDOS, "w", encoding="utf-8") as ficheiro:

            json.dump(
                alunos_excluidos,
                ficheiro,
                indent=4,
                ensure_ascii=False
            )


    except Exception as erro:

        raise Exception(
            f"Não foi possível guardar alunos excluídos: {erro}"
        )


# limpar alunos excluidos
# ======================================================
def limpar_alunos_expirados():

    hoje = datetime.now()

    removidos = []


    for aluno in alunos_excluidos:

        data = datetime.strptime(
            aluno["data_exclusao"],
            "%d/%m/%Y"
        )


        if hoje - data >= timedelta(days=60):

            removidos.append(aluno)


    for aluno in removidos:

        alunos_excluidos.remove(aluno)

        escrever_log(
            f"Aluno '{aluno['nome']}' eliminado definitivamente após 60 dias."
        )


    if removidos:

        guardar_alunos_excluidos()