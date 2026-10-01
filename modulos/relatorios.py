from datetime import datetime

from projeto_ginasio.dados import alunos, pagamentos
from modulos.pagamentos import situacao_mensalidade

MESES = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


def meses_disponiveis(quantidade=18):
    agora = datetime.now()
    ano = agora.year
    mes = agora.month
    opcoes = []

    for _ in range(quantidade):
        opcoes.append({
            "ano": ano,
            "mes": mes,
            "rotulo": f"{MESES[mes - 1]} {ano}",
        })
        mes -= 1
        if mes == 0:
            mes = 12
            ano -= 1

    return opcoes


def dados_relatorio(ano, mes):
    nomes = {aluno["id"]: aluno["nome"] for aluno in alunos}
    pagamentos_do_mes = []
    receita = 0.0

    for pagamento in pagamentos:
        try:
            data = datetime.strptime(pagamento["data_pagamento"], "%d/%m/%Y")
        except (ValueError, TypeError, KeyError):
            continue

        if data.year != ano or data.month != mes:
            continue

        valor = float(pagamento.get("valor", 0))
        receita += valor

        pagamentos_do_mes.append({
            "aluno": nomes.get(pagamento["id_aluno"], "Aluno removido"),
            "plano": pagamento.get("plano", ""),
            "valor": valor,
            "data_pagamento": pagamento.get("data_pagamento", ""),
            "data_vencimento": pagamento.get("data_vencimento", ""),
        })

    atrasados = []
    sem_pagamento = []

    for aluno in alunos:
        estado, vencimento = situacao_mensalidade(aluno["id"])

        if estado == "atrasada":
            atrasados.append({"aluno": aluno["nome"], "vencimento": vencimento})
        elif estado == "sem_pagamento":
            sem_pagamento.append(aluno["nome"])

    pagamentos_do_mes.sort(key=lambda p: p["aluno"].lower())
    atrasados.sort(key=lambda p: p["aluno"].lower())
    sem_pagamento.sort(key=lambda nome: nome.lower())

    por_plano = {}
    for pagamento in pagamentos_do_mes:
        plano = pagamento["plano"] or "—"
        if plano not in por_plano:
            por_plano[plano] = {"plano": plano, "quantidade": 0, "total": 0.0}
        por_plano[plano]["quantidade"] += 1
        por_plano[plano]["total"] += pagamento["valor"]

    resumo_planos = sorted(
        por_plano.values(),
        key=lambda item: item["total"],
        reverse=True,
    )

    valor_medio = receita / len(pagamentos_do_mes) if pagamentos_do_mes else 0.0

    return {
        "ano": ano,
        "mes": mes,
        "titulo": f"{MESES[mes - 1]} {ano}",
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total_alunos": len(alunos),
        "total_recebido": receita,
        "total_pagamentos": len(pagamentos_do_mes),
        "valor_medio": valor_medio,
        "por_plano": resumo_planos,
        "pagamentos": pagamentos_do_mes,
        "atrasados": atrasados,
        "sem_pagamento": sem_pagamento,
    }
