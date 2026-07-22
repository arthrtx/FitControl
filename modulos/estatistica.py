from datetime import datetime

from projeto_ginasio.dados import alunos, pagamentos, presencas
from modulos.pagamentos import mensalidade_valida
from modulos.funcionarios import funcionarios


# estatisticas
# ======================================================

def estatisticas():

    total = len(alunos)

    diario = 0
    mensal = 0
    trimestral = 0
    anual = 0

    mensalidades_validas = 0
    mensalidades_atrasadas = 0

    presencas_hoje = 0

    receita_total = 0
    receita_mes = 0

    agora = datetime.now()

    hoje = agora.strftime("%d/%m/%Y")
    mes_atual = agora.strftime("%m")
    ano_atual = agora.strftime("%Y")

    # alunos
    # ==========================

    for aluno in alunos:

        if aluno["plano"] == "Diário":
            diario += 1

        elif aluno["plano"] == "Mensal":
            mensal += 1

        elif aluno["plano"] == "Trimestral":
            trimestral += 1

        elif aluno["plano"] == "Anual":
            anual += 1

        if mensalidade_valida(aluno["id"]):
            mensalidades_validas += 1
        else:
            mensalidades_atrasadas += 1


    # presenças
    # ==========================

    for presenca in presencas:

        if presenca["data"] == hoje:
            presencas_hoje += 1

    # pagamentos
    # ==========================

    for pagamento in pagamentos:

        valor = float(pagamento.get("valor", 0))

        receita_total += valor

        try:

            data = datetime.strptime(
                pagamento["data_pagamento"],
                "%d/%m/%Y"
            )

            if (
                data.strftime("%m") == mes_atual
                and
                data.strftime("%Y") == ano_atual
            ):
                receita_mes += valor

        except:
            pass


    # resultado
    # ==========================

    return {

        "total_alunos": total,

        "plano_diario": diario,

        "plano_mensal": mensal,

        "plano_trimestral": trimestral,

        "plano_anual": anual,

        "mensalidades_validas": mensalidades_validas,

        "mensalidades_atrasadas": mensalidades_atrasadas,

        "total_presencas": len(presencas),

        "presencas_hoje": presencas_hoje,

        "receita_total": receita_total,

        "receita_mes": receita_mes,

        "funcionarios_registados": len(funcionarios)

    }