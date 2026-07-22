import json
import os
import logging
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)

PASTA_DADOS = os.path.join(BASE_DIR, "dados")

os.makedirs(PASTA_DADOS, exist_ok=True)

ARQUIVO_ACESSOS = os.path.join(
    PASTA_DADOS,
    "historico_acessos.json"
)

ARQUIVO_LOG = os.path.join(
    PASTA_DADOS,
    "logs.txt"
)

logging.basicConfig(

    filename=ARQUIVO_LOG,

    level=logging.INFO,

    format="%(asctime)s - %(message)s"

)

def data_atual():

    return datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

# HISTÓRICO
# ==========================
def carregar_historico():

    if not os.path.exists(ARQUIVO_ACESSOS):
        return []

    try:

        with open(
            ARQUIVO_ACESSOS,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return []


def guardar_historico(lista):

    with open(
        ARQUIVO_ACESSOS,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            lista,
            f,
            indent=4,
            ensure_ascii=False
        )


def guardar_evento(

    utilizador,
    estado

):

    historico = carregar_historico()

    historico.append({

        "utilizador": utilizador,

        "estado": estado,

        "data": data_atual()

    })

    guardar_historico(historico)

    logging.info(
        f"{estado} - {utilizador}"
    )


def registar_login(usuario):

    guardar_evento(
        usuario,
        "LOGIN"
    )


def registar_logout(usuario):

    guardar_evento(
        usuario,
        "LOGOUT"
    )


def registar_acesso(

    usuario,
    autorizado

):

    estado = (
        "AUTORIZADO"
        if autorizado
        else
        "NEGADO"
    )

    guardar_evento(
        usuario,
        estado
    )

def listar_historico():

    return carregar_historico()

def listar_historico_utilizador(nome):

    return [

        h

        for h in carregar_historico()

        if h["utilizador"] == nome

    ]

def limpar_historico():

    guardar_historico([])

    logging.info(
        "Histórico apagado."
    )

def limpar_logs():

    with open(
        ARQUIVO_LOG,
        "w",
        encoding="utf-8"
    ) as f:

        pass

    logging.info(
        "Logs apagados."
    )

# ESTATÍSTICAS
# ==========================
def obter_estatisticas():

    historico = listar_historico()

    logins = 0
    logouts = 0
    autorizados = 0
    negados = 0

    for evento in historico:

        estado = evento["estado"]

        if estado == "LOGIN":
            logins += 1

        elif estado == "LOGOUT":
            logouts += 1

        elif estado == "AUTORIZADO":
            autorizados += 1

        elif estado == "NEGADO":
            negados += 1

    return {

        "logins": logins,

        "logouts": logouts,

        "autorizados": autorizados,

        "negados": negados,

        "total_eventos": len(historico)

    }

def inicializar():

    logging.info(
        "Sistema de acessos iniciado."
    )