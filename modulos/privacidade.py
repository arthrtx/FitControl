import json
import os
from datetime import datetime

from projeto_ginasio.config import PASTA_ARQUIVOS
from projeto_ginasio.dados import alunos, alunos_excluidos, pagamentos
from projeto_ginasio.db_adapter import (
    get_termos_aceites,
    get_todos_termos_aceites,
    registar_termos_aceites,
    get_logs_por_tipo,
    apagar_logs_antigos,
    add_log,
)

# sobe-se a versão sempre que os termos mudam -> todos voltam a aceitar
VERSAO_TERMOS = "2.0"

# os logs (entradas, pagamentos, acessos) guardam-se 2 anos
DIAS_CONSERVACAO_LOGS = 730

PASTA_TITULARES = os.path.join(PASTA_ARQUIVOS, "pedidos_rgpd")


# termos
# ======================================================
def termos_aceites(usuario):

    registo = get_termos_aceites(usuario)

    if not registo:
        return False

    return registo["versao"] == VERSAO_TERMOS


def aceitar_termos(usuario):

    registar_termos_aceites(usuario, VERSAO_TERMOS)

    add_log(
        f"Termos e Política de Privacidade v{VERSAO_TERMOS} aceites: {usuario}",
        tipo="administracao"
    )


def recusar_termos(usuario):

    add_log(
        f"Termos v{VERSAO_TERMOS} recusados: {usuario}",
        tipo="administracao"
    )


def aceitacoes():

    return get_todos_termos_aceites()


# conservação dos dados
# ======================================================
def limpar_logs_antigos():

    try:
        apagados = apagar_logs_antigos(DIAS_CONSERVACAO_LOGS)
    except Exception as erro:
        print(f"Não foi possível limpar logs antigos: {erro}")
        return 0

    if apagados:
        add_log(
            f"{apagados} registos com mais de {DIAS_CONSERVACAO_LOGS} dias apagados (prazo de conservação).",
            tipo="administracao"
        )

    return apagados


# direito de acesso / portabilidade
# ======================================================
def _procurar_aluno(id_aluno):

    for aluno in alunos:
        if aluno["id"] == id_aluno:
            return aluno, False

    for aluno in alunos_excluidos:
        if aluno["id"] == id_aluno:
            return aluno, True

    return None, False


def exportar_dados_aluno(id_aluno, pedido_por=""):

    aluno, arquivado = _procurar_aluno(id_aluno)

    if not aluno:
        return None

    nome = aluno["nome"]

    lista_pagamentos = []
    for pagamento in pagamentos:
        if pagamento["id_aluno"] == id_aluno:
            lista_pagamentos.append({
                "plano": pagamento["plano"],
                "valor": pagamento["valor"],
                "data_pagamento": pagamento["data_pagamento"],
                "data_vencimento": pagamento["data_vencimento"],
                "estado": pagamento["estado"],
            })

    lista_presencas = []
    for log in get_logs_por_tipo("presenca"):
        if f"'{nome}'" in log["evento"]:
            lista_presencas.append(log["data"])

    tem_foto = bool(aluno.get("foto")) and aluno.get("foto") != "sem_foto"

    dados = {
        "exportado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "pedido_tratado_por": pedido_por,
        "titular": {
            "id": aluno["id"],
            "nome": nome,
            "telemovel": aluno["telemovel"],
            "documento": aluno["documento"],
            "plano": aluno["plano"],
            "arquivado": arquivado,
            "data_exclusao": aluno.get("data_exclusao", ""),
        },
        "reconhecimento_facial": {
            "fotografia_guardada": tem_foto,
            "modelo_facial_guardado": bool(aluno.get("embedding")),
            "nota": "O modelo facial é um vetor numérico usado só para registar presenças.",
        },
        "pagamentos": lista_pagamentos,
        "presencas": lista_presencas,
    }

    os.makedirs(PASTA_TITULARES, exist_ok=True)
    nome_ficheiro = f"aluno_{id_aluno}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    caminho = os.path.join(PASTA_TITULARES, nome_ficheiro)

    with open(caminho, "w", encoding="utf-8") as ficheiro:
        json.dump(dados, ficheiro, ensure_ascii=False, indent=2)

    add_log(
        f"Dados do aluno ID {id_aluno} exportados (pedido de acesso RGPD).",
        tipo="administracao"
    )

    return caminho
