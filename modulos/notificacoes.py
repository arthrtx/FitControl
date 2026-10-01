from projeto_ginasio.dados import alunos
from projeto_ginasio.db_adapter import (
    guardar_notificacao,
    get_notificacoes,
    contar_notificacoes_pendentes,
    marcar_notificacao_lida,
    marcar_notificacoes_lidas,
    apagar_notificacao,
    apagar_notificacoes_lidas,
)
from modulos.pagamentos import situacao_mensalidade


def verificar():
    atuais = {}

    for aluno in alunos:
        estado, vencimento = situacao_mensalidade(aluno["id"])
        id_aluno = aluno["id"]
        nome = aluno["nome"]

        if estado == "sem_pagamento":
            atuais[f"pagamento:{id_aluno}"] = {
                "chave": f"pagamento:{id_aluno}",
                "tipo": "pagamento",
                "titulo": "Adicionar pagamento",
                "mensagem": f"{nome} não tem nenhum pagamento registado.",
                "ref_id": id_aluno,
            }
        elif estado == "atrasada":
            atuais[f"atraso:{id_aluno}"] = {
                "chave": f"atraso:{id_aluno}",
                "tipo": "atraso",
                "titulo": "Mensalidade em atraso",
                "mensagem": f"A mensalidade de {nome} venceu a {vencimento}.",
                "ref_id": id_aluno,
            }

    existentes = {registo["chave"]: registo for registo in get_notificacoes()}

    for registo in existentes.values():
        if registo["chave"] not in atuais:
            apagar_notificacao(registo["chave"])

    for chave, notificacao in atuais.items():
        actual = existentes.get(chave)
        if (
            actual
            and actual["titulo"] == notificacao["titulo"]
            and actual["mensagem"] == notificacao["mensagem"]
        ):
            continue
        guardar_notificacao(notificacao)


def listar():
    return get_notificacoes()


def por_ler():
    return contar_notificacoes_pendentes()


def marcar_lida(id_notificacao):
    marcar_notificacao_lida(id_notificacao)


def marcar_todas_lidas():
    marcar_notificacoes_lidas()


def limpar_lidas():
    apagar_notificacoes_lidas()
