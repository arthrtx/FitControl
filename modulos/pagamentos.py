import json
import os
from datetime import datetime, timedelta

from projeto_ginasio.config import *
from projeto_ginasio.dados import pagamentos, alunos
from modulos.gestao_alunos import escrever_log


# guardar pagamentos
# ======================================================
def guardar_pagamentos():

    try:

        with open(ARQUIVO_PAGAMENTOS, "w", encoding="utf-8") as ficheiro:

            json.dump(
                pagamentos,
                ficheiro,
                indent=4,
                ensure_ascii=False
            )

    except Exception as erro:

        raise Exception(
            f"Não foi possível guardar os pagamentos: {erro}"
        )


# carregar pagamentos
# ======================================================
def carregar_pagamentos():

    if not os.path.exists(ARQUIVO_PAGAMENTOS):

        pagamentos.clear()

        guardar_pagamentos()

        return


    try:

        with open(ARQUIVO_PAGAMENTOS, "r", encoding="utf-8") as ficheiro:

            dados = json.load(ficheiro)

            pagamentos.clear()

            pagamentos.extend(dados)


    except Exception as erro:

        raise Exception(
            f"Não foi possível carregar os pagamentos: {erro}"
        )


# registar pagamentos
# ======================================================
def registar_pagamento(id_aluno, valor):

    # Validar valor
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return False

    if valor <= 0:
        return False

    plano = ""

    for aluno in alunos:

        if aluno["id"] == id_aluno:

            plano = aluno["plano"]

            break

    if plano == "":

        return False
    
    hoje = datetime.now()

    if plano == "Diário":
        
        data_hoje = hoje.strftime("%d/%m/%Y")
        
        for pagamento in pagamentos:
            if (
                pagamento["id_aluno"] == id_aluno and
                pagamento["plano"] == "Diário" and
                pagamento["data_pagamento"] == data_hoje
            ):
                return False
        vencimento = hoje
            
    elif plano == "Mensal":

        vencimento = hoje + timedelta(days=30)


    elif plano == "Trimestral":

        vencimento = hoje + timedelta(days=90)


    elif plano == "Anual":

        vencimento = hoje + timedelta(days=365)


    else:

        return False



    pagamento = {

        "id_aluno": id_aluno,

        "plano": plano,

        "valor": round(valor, 2),

        "data_pagamento": hoje.strftime("%d/%m/%Y"),

        "data_vencimento": vencimento.strftime("%d/%m/%Y"),

        "estado": "Pago"

    }


    pagamentos.append(pagamento)


    guardar_pagamentos()

    nome_aluno = ""

    for aluno in alunos:
        if aluno["id"] == id_aluno:
            nome_aluno = aluno["nome"]
            break
    escrever_log(
         f"Pagamento registado para o aluno '{nome_aluno}'."
    )


    return True



# verificar mensalidades
# ======================================================
def mensalidade_valida(id_aluno):

    for pagamento in reversed(pagamentos):

        if pagamento["id_aluno"] == id_aluno:


            if pagamento["plano"] == "Diário":

                return pagamento["data_pagamento"] == datetime.now().strftime("%d/%m/%Y")


            vencimento = datetime.strptime(
                pagamento["data_vencimento"],
                "%d/%m/%Y"
            )


            return vencimento.date() >= datetime.now().date()



    return False