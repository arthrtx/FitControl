import json
import os
from datetime import datetime, timedelta
from modulos import acessos
from projeto_ginasio.dados import *
from projeto_ginasio.config import ARQUIVO_FUNCIONARIOS
from tkinter import messagebox

# CONFIGURAÇÕES
# =====================================================

import os
from projeto_ginasio.config import (
    ARQUIVO_FUNCIONARIOS,
    ARQUIVO_LOG
)

MAX_TENTATIVAS = 3
TEMPO_BLOQUEIO = 60


funcionarios = []
sessao = None
tentativas_falhadas = {}

# INICIALIZAÇÃO
# =====================================================

def inicializar():
    carregar_funcionarios()


# funcionarios
# =====================================================

def carregar_funcionarios():

    global funcionarios

    if not os.path.exists(ARQUIVO_FUNCIONARIOS):
        funcionarios = []

    else:
        try:

            with open(
                ARQUIVO_FUNCIONARIOS,
                "r",
                encoding="utf-8"
            ) as ficheiro:

                funcionarios = json.load(ficheiro)

        except:

            funcionarios = []


    # CRIAR ADMIN TEMPORÁRIO SE NÃO EXISTIR
    if not procurar_utilizador("adm"):

        funcionarios.append({
            "id": 1,
            "nome": "Administrador Temporário",
            "usuario": "adm",
            "senha": "adm",
            "tipo": "Administrador",
            "temporario": True

        })

        guardar_funcionarios()
def guardar_funcionarios():

    with open(
        ARQUIVO_FUNCIONARIOS,
        "w",
        encoding="utf-8"
    ) as ficheiro:

        json.dump(
            funcionarios,
            ficheiro,
            indent=4,
            ensure_ascii=False
        )

# LOGS
# =====================================================

def escrever_log(evento):

    try:

        os.makedirs(
            os.path.dirname(ARQUIVO_LOG),
            exist_ok=True
        )

        with open(
            ARQUIVO_LOG,
            "a",
            encoding="utf-8"
        ) as ficheiro:

            ficheiro.write(
                f"{datetime.now():%d/%m/%Y %H:%M:%S} - [AUTENTICACAO] {evento}\n"
            )

    except:
        pass


# AUXILIARES
# =====================================================

def procurar_utilizador(usuario):

    for utilizador in funcionarios:

        if utilizador["usuario"].lower() == usuario.lower():

            return utilizador

    return None

# BLOQUEIO DE LOGIN
# =====================================================

def usuario_bloqueado(usuario):

    registo = tentativas_falhadas.get(usuario.lower())

    if not registo:
        return False

    bloqueado = registo.get("bloqueado_ate")

    if not bloqueado:
        return False

    if datetime.now() < bloqueado:
        return True

    tentativas_falhadas[usuario.lower()] = {
        "tentativas": 0,
        "bloqueado_ate": None
    }

    return False


def registar_tentativa_falhada(usuario):

    chave = usuario.lower()

    registo = tentativas_falhadas.get(
        chave,
        {
            "tentativas": 0,
            "bloqueado_ate": None
        }
    )

    registo["tentativas"] += 1

    if registo["tentativas"] >= MAX_TENTATIVAS:

        registo["tentativas"] = 0

        registo["bloqueado_ate"] = (
            datetime.now() +
            timedelta(seconds=TEMPO_BLOQUEIO)
        )

        escrever_log(
            f"Utilizador bloqueado: {usuario}"
        )

    tentativas_falhadas[chave] = registo


def limpar_tentativas(usuario):

    tentativas_falhadas[usuario.lower()] = {

        "tentativas": 0,

        "bloqueado_ate": None

    }

# LOGIN
# =====================================================

def autenticar(usuario, senha):

    global sessao

    carregar_funcionarios()

    if usuario_bloqueado(usuario):

        registo = tentativas_falhadas[usuario.lower()]

        segundos = int(
            (
                registo["bloqueado_ate"] -
                datetime.now()
            ).total_seconds()
        )

        return (
            False,
            f"Utilizador bloqueado.\nTente novamente em {segundos} segundos.",
            None
        )

    utilizador = procurar_utilizador(usuario)

    if not utilizador:

        registar_tentativa_falhada(usuario)

        escrever_log(
            f"Login inválido: {usuario}"
        )

        return (
            False,
            "Utilizador inexistente.",
            None
        )

    if utilizador["senha"] != senha:

        registar_tentativa_falhada(usuario)

        escrever_log(
            f"senha incorreta: {usuario}"
        )

        restantes = (
            MAX_TENTATIVAS -
            tentativas_falhadas[usuario.lower()]["tentativas"]
        )

        return (
            False,
            f"senha incorreta.\nTentativas restantes: {restantes}",
            None
        )

    limpar_tentativas(usuario)

    sessao = utilizador
    
    if utilizador.get("temporario", False):

        messagebox.showwarning(

            "Administrador Temporário",

            "Está a utilizar a conta criada automaticamente.\n\n"

            "Por motivos de segurança altere:\n"

            "- Nome\n"

            "- Utilizador\n"

            "- Palavra-passe"

        )

    try:
        acessos.registar_login(
            utilizador["usuario"]
        )
    except:
        pass

    escrever_log(
        f"Login: {utilizador['usuario']}"
    )

    return (
        True,
        f"Bem-vindo {utilizador['nome']}",
        utilizador
    )


# LOGOUT
# =====================================================

def terminar_sessao():

    global sessao

    if not sessao:
        return

    try:

        acessos.registar_logout(
            sessao["usuario"]
        )

    except:
        pass

    escrever_log(
        f"Logout: {sessao['usuario']}"
    )

    sessao = None

# SESSÃO
# =====================================================

def sessao_ativa():

    return sessao is not None


def obter_utilizador_atual():

    return sessao

# PERMISSÕES
# =====================================================

def tem_permissao(tipo):

    if not sessao:
        return False

    if sessao.get("tipo") == "Administrador":
        return True

    return sessao.get("tipo") == tipo


def validar_acesso(tipo="Utilizador"):

    if not sessao:

        escrever_log(
            "Acesso negado - sem sessão."
        )

        return False

    if tem_permissao(tipo):

        escrever_log(
            f"Acesso autorizado: "
            f"{sessao['usuario']} "
            f"({tipo})"
        )

        return True

    escrever_log(
        f"Acesso negado: "
        f"{sessao['usuario']}"
    )

    return False

# FUNCIONÁRIOS
# =====================================================

def listar_funcionarios():

    carregar_funcionarios()

    return funcionarios


def adicionar_funcionario(

    nome,
    usuario,
    senha,
    tipo="Funcionario"

):

    carregar_funcionarios()

    if procurar_utilizador(usuario):

        return False

    funcionarios.append({

        "nome": nome,

        "usuario": usuario,

        "senha": senha,

        "tipo": tipo,

        "temporario": False

    })

    guardar_funcionarios()

    escrever_log(

        f"Funcionário criado: {usuario}"

    )

    return True


def eliminar_funcionario(usuario):

    global funcionarios

    carregar_funcionarios()

    funcionarios = [

        u

        for u in funcionarios

        if u["usuario"] != usuario

    ]

    guardar_funcionarios()

    escrever_log(

        f"Funcionário eliminado: {usuario}"

    )

    return True


def alterar_senha(

    usuario,
    nova_senha

):

    carregar_funcionarios()

    utilizador = procurar_utilizador(usuario)

    if not utilizador:

        return False

    utilizador["senha"] = nova_senha

    guardar_funcionarios()

    escrever_log(

        f"senha alterada: {usuario}"

    )

    return True


def alterar_permissao(

    usuario,
    tipo

):

    carregar_funcionarios()

    utilizador = procurar_utilizador(usuario)

    if not utilizador:

        return False

    utilizador["tipo"] = tipo

    guardar_funcionarios()

    escrever_log(

        f"Permissão alterada: "
        f"{usuario} -> {tipo}"

    )

    return True