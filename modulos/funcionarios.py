from datetime import datetime

from projeto_ginasio.config import *
from projeto_ginasio.dados import funcionarios
from projeto_ginasio.db_adapter import (
    save_funcionarios, add_funcionario, update_funcionario, delete_funcionario, add_log
)


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
        save_funcionarios(funcionarios)
    except Exception as erro:
        raise Exception(f"Não foi possível guardar funcionários: {erro}")


# ======================================================
# carregar funcionários
# ======================================================
def carregar_funcionarios():
    # Dados agora são carregados do banco de dados em dados.py
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


# ======================================================
# logs
# ======================================================
def escrever_log(evento, tipo="funcionario"):
    try:
        add_log(evento, tipo=tipo)
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


    add_funcionario(novo_funcionario)
    funcionarios.append(novo_funcionario)

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
            print("ID recebido:", id_funcionario, type(id_funcionario))
            print("ID guardado :", funcionario["id"], type(funcionario["id"]))
            

            funcionario["nome"] = nome
            funcionario["usuario"] = usuario
            funcionario["senha"] = senha
            funcionario["tipo"] = tipo

            funcionario["temporario"] = False

            update_funcionario(funcionario)

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

            delete_funcionario(id_funcionario)
            funcionarios.remove(funcionario)

            escrever_log(
                f"Funcionário '{funcionario['nome']}' eliminado."
            )

            return True

    return False