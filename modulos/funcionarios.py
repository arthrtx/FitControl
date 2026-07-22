import json
import os
from datetime import datetime

from projeto_ginasio.config import *
from projeto_ginasio.dados import funcionarios


# ======================================================
# inicialização
# ======================================================
def inicializar():
    carregar_funcionarios()


# ======================================================
# guardar funcionários
# ======================================================
def guardar_funcionarios():
    try:
        with open(ARQUIVO_FUNCIONARIOS, "w", encoding="utf-8") as ficheiro:
            json.dump(
                funcionarios,
                ficheiro,
                indent=4,
                ensure_ascii=False
            )

    except Exception as erro:
        raise Exception(f"Não foi possível guardar funcionários: {erro}")


# ======================================================
# carregar funcionários
# ======================================================
def carregar_funcionarios():

    if not os.path.exists(ARQUIVO_FUNCIONARIOS):

        funcionarios.clear()

        funcionarios.append({

            "id": 1,

            "nome": "Administrador Temporário",

            "usuario": "adm",

            "senha": "adm",

            "tipo": "Administrador",

            "temporario": True

        })

        guardar_funcionarios()

        return

    try:
        with open(ARQUIVO_FUNCIONARIOS, "r", encoding="utf-8") as ficheiro:
            dados = json.load(ficheiro)

            funcionarios.clear()
            if isinstance(dados, list):
                funcionarios.extend(dados)

        if not funcionarios:

            funcionarios.append({

                "id": 1,

                "nome": "Administrador Temporário",

                "usuario": "adm",

                "senha": "adm",

                "tipo": "Administrador",

                "temporario": True

            })

            guardar_funcionarios()

    except Exception as erro:
        raise Exception(f"Não foi possível carregar funcionários: {erro}")


# ======================================================
# logs
# ======================================================
def escrever_log(evento):

    try:
        with open(ARQUIVO_LOG, "a", encoding="utf-8") as ficheiro:

            data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            ficheiro.write(
                f"{data} - {evento}\n"
            )

    except Exception as erro:
        raise Exception(f"Erro no log: {erro}")


# ======================================================
# gerar ID
# ======================================================
def gerar_id():

    if not funcionarios:
        return 1

    maior = max(
        funcionario["id"]
        for funcionario in funcionarios
    )

    return maior + 1


# ======================================================
# verificar usuário
# ======================================================
def utilizador_existe(usuario):

    for funcionario in funcionarios:

        if funcionario["usuario"] == usuario:
            return True

    return False


# ======================================================
# criar funcionário
# ======================================================
def criar_funcionario(nome, usuario, senha, tipo):

    nome = nome.strip()
    usuario = usuario.strip()
    senha = senha.strip()


    if nome == "":
        return False

    if usuario == "":
        return False

    if senha == "":
        return False
    
    tipos_validos = [
            "Funcionario",
            "Administrador"
    ]

    if tipo not in tipos_validos:
        return False


    if utilizador_existe(usuario):
        return False


    novo_funcionario = {

        "id": gerar_id(),

        "nome": nome,

        "usuario": usuario,

        "senha": senha,

        "tipo": tipo,

        "temporario": False
    }


    funcionarios.append(novo_funcionario)

    guardar_funcionarios()

    escrever_log(
        f"Funcionário '{nome}' criado."
    )


    return True


# ======================================================
# listar funcionários
# ======================================================
def listar_funcionarios():

    return sorted(
        funcionarios,
        key=lambda funcionario:
        funcionario["nome"].lower()
    )
# ======================================================
# editar funcionário
# ======================================================

def editar_funcionario(id_funcionario, nome, usuario, senha, tipo):

    nome = nome.strip()
    usuario = usuario.strip()
    senha = senha.strip()

    if nome == "":
        return False

    if usuario == "":
        return False

    if senha == "":
        return False

    for funcionario in funcionarios:

        if (
            funcionario["usuario"] == usuario
            and
            funcionario["id"] != id_funcionario
        ):
            return False

    for funcionario in funcionarios:

        if funcionario["id"] == id_funcionario:

            funcionario["nome"] = nome
            funcionario["usuario"] = usuario
            funcionario["senha"] = senha
            funcionario["tipo"] = tipo

            funcionario["temporario"] = False

            guardar_funcionarios()

            escrever_log(
                f"Funcionário '{nome}' editado."
            )

            return True

    return False
# ======================================================
# eliminar funcionário
# ======================================================
def eliminar_funcionario(id_funcionario):

    for funcionario in funcionarios:

        if funcionario["id"] == id_funcionario:

            funcionarios.remove(funcionario)

            guardar_funcionarios()

            escrever_log(
                f"Funcionário '{funcionario['nome']}' eliminado."
            )

            return True

    return False