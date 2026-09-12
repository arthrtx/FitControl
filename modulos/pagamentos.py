from datetime import datetime, timedelta

from projeto_ginasio.config import *
from projeto_ginasio.dados import pagamentos, alunos
from projeto_ginasio.db_adapter import (
    save_pagamentos,
    add_pagamento,
    apagar_historico_pagamentos,
    delete_pagamento,
)
from modulos.gestao_alunos import escrever_log


# guardar pagamentos
# ======================================================
def guardar_pagamentos():
    try:
        save_pagamentos(pagamentos)
    except Exception as erro:
        raise Exception(f"Não foi possível guardar os pagamentos: {erro}")


# carregar pagamentos
# ======================================================
def carregar_pagamentos():
    # Dados agora são carregados do banco de dados em dados.py
    pass


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

    novo_id = add_pagamento(pagamento)
    pagamento["id"] = novo_id
    pagamentos.append(pagamento)

    nome_aluno = ""

    for aluno in alunos:
        if aluno["id"] == id_aluno:
            nome_aluno = aluno["nome"]
            break
    escrever_log(
         f"Pagamento registado para o aluno '{nome_aluno}'.",
         tipo="pagamento"
    )


    return True


# apagar um pagamento específico
# ======================================================
def eliminar_pagamento(id_pagamento):
    """Apaga um pagamento individual. Deve ser usado apenas por
    administradores."""
    if not id_pagamento:
        return False
    encontrado = None
    for pagamento in pagamentos:
        if pagamento.get("id") == id_pagamento:
            encontrado = pagamento
            break
    if not encontrado:
        return False
    delete_pagamento(id_pagamento)
    pagamentos.remove(encontrado)
    escrever_log(
        f"Pagamento apagado (ID {id_pagamento}).",
        tipo="administracao"
    )
    return True


# apagar histórico de pagamentos
# ======================================================
def apagar_historico():
    """Apaga todo o histórico de pagamentos. Deve ser usado apenas por
    administradores."""
    global pagamentos
    total = len(pagamentos)
    apagar_historico_pagamentos()
    pagamentos.clear()
    escrever_log(
        f"Histórico de pagamentos apagado ({total} registos).",
        tipo="administracao"
    )
    return total



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