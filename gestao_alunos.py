import json
import os
from datetime import datetime, timedelta
from Camara import tirarFoto

# Constantes
# ======================================================
ARQUIVO = "C:/V1/MinhaPasta/alunos.txt"
ARQUIVO_LOG = "C:/V1/MinhaPasta/logs.txt"
ARQUIVO_PAGAMENTOS = "C:/V1/MinhaPasta/pagamentos.txt"
ARQUIVO_PRESENCAS = "C:/V1/MinhaPasta/presencas.txt"

# Variaveis globais
# ======================================================
alunos = []
pagamentos = []
presencas = []

# inicialização
# ======================================================
def inicializar():
    carregar_alunos()
    carregar_pagamentos()
    carregar_presencas()
    
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
    global alunos

    if not os.path.exists(ARQUIVO):
        alunos = []
        guardar_alunos()
        return
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as ficheiro:
            alunos = json.load(ficheiro)
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

    id_aluno = gerar_id()

    if documento_existe(documento):
        return False
    
    caminho_foto = tirarFoto(str(id_aluno))
        
    if not caminho_foto:
        return False

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
    return sorted(alunos, key=lambda aluno: aluno["nome"].lower())

# editar alunos
# ======================================================
def editar_aluno(id_aluno, nome, telemovel, documento, plano):
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

            alunos.remove(aluno)
            guardar_alunos()
            escrever_log(f"Aluno '{aluno['nome']}' eliminado.")
            return True
    return False

# estatisticas
# ======================================================
def estatisticas():
    total = len(alunos)
    diario = 0
    mensal = 0
    mensalidades_validas = 0
    mensalidades_atrasadas = 0
    presencas_hoje = 0
    
    hoje = datetime.now().strftime("%d/%m/%Y")
    
    for aluno in alunos:
        if aluno["plano"] == "Diário":
            diario += 1
        else:
            mensal += 1
        if mensalidade_valida(aluno["id"]):
            mensalidades_validas += 1
        else:
            mensalidades_atrasadas += 1
    
    for presenca in presencas:
        if presenca["data"] == hoje:
            presencas_hoje += 1

    return {
        "total_alunos": total,
        "plano_diario": diario,
        "plano_mensal": mensal,
        "mensalidades_validas": mensalidades_validas,
        "mensalidades_atrasadas": mensalidades_atrasadas,
        "total_presencas": len(presencas),
        "presencas_hoje": presencas_hoje
    }

# guardar pagamentos
# ======================================================
def guardar_pagamentos():
    try:
        with open(ARQUIVO_PAGAMENTOS, "w", encoding="utf-8") as ficheiro:
            json.dump(pagamentos, ficheiro, indent=4, ensure_ascii=False)
    except Exception as erro:
        raise Exception(f"Não foi possível guardar os pagamentos: {erro}")

# carregar pagamentos
# ======================================================
def carregar_pagamentos():
    global pagamentos
    if not os.path.exists(ARQUIVO_PAGAMENTOS):
        pagamentos = []
        guardar_pagamentos()
        return
    try:
        with open(ARQUIVO_PAGAMENTOS, "r", encoding="utf-8") as ficheiro:
            pagamentos = json.load(ficheiro)
    except Exception as erro:
        raise Exception(f"Não foi possível carregar os pagamentos: {erro}")

# registar pagamentos
# ======================================================
def registar_pagamento(id_aluno, valor):
    plano = ""
    for aluno in alunos:
        if aluno["id"] == id_aluno:
            plano = aluno["plano"]
            break
    if plano == "":
        return False
    
    hoje = datetime.now()
    if plano == "Mensal":
        vencimento = hoje + timedelta(days=30)
    else:
        vencimento = hoje
    
    pagamento = {
        "id_aluno": id_aluno,
        "plano": plano,
        "valor": valor,
        "data_pagamento": hoje.strftime("%d/%m/%Y"),
        "data_vencimento": vencimento.strftime("%d/%m/%Y"),
        "estado": "Pago"
    }
    pagamentos.append(pagamento)
    guardar_pagamentos()
    escrever_log(f"Pagamento registado para o aluno {id_aluno}.")

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

            return vencimento >= datetime.now()

    return False

# guardar presenças
# ======================================================
def guardar_presencas():
    try:
        with open(ARQUIVO_PRESENCAS, "w", encoding="utf-8") as ficheiro:
            json.dump(presencas, ficheiro, indent=4, ensure_ascii=False)
    except Exception as erro:
        raise Exception(f"Não foi possível guardar as presenças: {erro}")

# carregar presenças
# ======================================================
def carregar_presencas():
    global presencas
    if not os.path.exists(ARQUIVO_PRESENCAS):
        presencas = []
        guardar_presencas()
        return
    try:
        with open(ARQUIVO_PRESENCAS, "r", encoding="utf-8") as ficheiro:
            presencas = json.load(ficheiro)
    except Exception as erro:
        raise Exception(f"Não foi possível carregar as presenças: {erro}")

# registar presenças
# ======================================================
def registar_presenca(id_aluno):
    existe = False
    for aluno in alunos:
        if aluno["id"] == id_aluno:
            existe = True
            break
    if not existe:
        return False

    agora = datetime.now()
    presenca = {
        "id_aluno": id_aluno,
        "data": agora.strftime("%d/%m/%Y"),
        "hora": agora.strftime("%H:%M")
    }

    presencas.append(presenca)
    guardar_presencas()
    escrever_log(f"Entrada do aluno {id_aluno}.")

    return True



                               