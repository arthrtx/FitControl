import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from projeto_ginasio.config import PASTA_RELATORIOS

COR_MARCA = colors.HexColor("#6558e8")
COR_CABECALHO = colors.HexColor("#15151c")
COR_LINHA = colors.HexColor("#f6f6fa")
COR_BORDA = colors.HexColor("#dcdce6")
COR_TEXTO = colors.HexColor("#16161d")
COR_SUAVE = colors.HexColor("#6b6b7b")
COR_VERDE = colors.HexColor("#047857")
COR_LARANJA = colors.HexColor("#b45309")
COR_VERMELHO = colors.HexColor("#dc2626")

LARGURA = A4[0] - 32 * mm

ESTILO_BANNER_TITULO = ParagraphStyle(
    "BannerTitulo",
    fontName="Helvetica-Bold",
    fontSize=16,
    textColor=colors.white,
    leading=19,
)
ESTILO_BANNER_SUB = ParagraphStyle(
    "BannerSub",
    fontName="Helvetica",
    fontSize=8.5,
    textColor=colors.HexColor("#dedaff"),
    leading=11,
)
ESTILO_BANNER_MES = ParagraphStyle(
    "BannerMes",
    fontName="Helvetica-Bold",
    fontSize=14,
    textColor=colors.white,
    alignment=TA_RIGHT,
    leading=17,
)
ESTILO_BANNER_MES_SUB = ParagraphStyle(
    "BannerMesSub",
    fontName="Helvetica",
    fontSize=8,
    textColor=colors.HexColor("#dedaff"),
    alignment=TA_RIGHT,
    leading=10,
)
ESTILO_CARTAO_VALOR = ParagraphStyle(
    "CartaoValor",
    fontName="Helvetica-Bold",
    fontSize=15,
    textColor=COR_MARCA,
    leading=18,
    alignment=TA_CENTER,
)
ESTILO_CARTAO_ROTULO = ParagraphStyle(
    "CartaoRotulo",
    fontName="Helvetica",
    fontSize=7.5,
    textColor=COR_SUAVE,
    leading=10,
    alignment=TA_CENTER,
)
ESTILO_SECCAO = ParagraphStyle(
    "Secao",
    fontName="Helvetica-Bold",
    fontSize=11.5,
    textColor=COR_MARCA,
    leading=14,
)
ESTILO_CORPO = ParagraphStyle(
    "Corpo",
    fontName="Helvetica",
    fontSize=9,
    textColor=COR_TEXTO,
    leading=13,
)
ESTILO_VAZIO = ParagraphStyle(
    "Vazio",
    fontName="Helvetica-Oblique",
    fontSize=9,
    textColor=COR_SUAVE,
    leading=13,
)
ESTILO_CELULA = ParagraphStyle(
    "Celula",
    fontName="Helvetica",
    fontSize=8.5,
    textColor=COR_TEXTO,
    leading=11,
)
ESTILO_CELULA_DIREITA = ParagraphStyle(
    "CelulaDireita",
    fontName="Helvetica",
    fontSize=8.5,
    textColor=COR_TEXTO,
    leading=11,
    alignment=TA_RIGHT,
)
ESTILO_CELULA_CENTRO = ParagraphStyle(
    "CelulaCentro",
    fontName="Helvetica",
    fontSize=8.5,
    textColor=COR_TEXTO,
    leading=11,
    alignment=TA_CENTER,
)
ESTILO_CABECALHO = ParagraphStyle(
    "Cabecalho",
    fontName="Helvetica-Bold",
    fontSize=8,
    textColor=colors.white,
    leading=10,
)
ESTILO_CABECALHO_DIREITA = ParagraphStyle(
    "CabecalhoDireita",
    fontName="Helvetica-Bold",
    fontSize=8,
    textColor=colors.white,
    leading=10,
    alignment=TA_RIGHT,
)
ESTILO_CABECALHO_CENTRO = ParagraphStyle(
    "CabecalhoCentro",
    fontName="Helvetica-Bold",
    fontSize=8,
    textColor=colors.white,
    leading=10,
    alignment=TA_CENTER,
)


def _euros(valor):
    return f"{valor:,.2f}".replace(",", " ").replace(".", ",") + " €"


def _celula(valor, estilo=None):
    return Paragraph(escape(str(valor)), estilo or ESTILO_CELULA)


def _cabecalho(valor, estilo=None):
    return Paragraph(escape(str(valor)), estilo or ESTILO_CABECALHO)


def _banner(dados):
    esquerda = [
        Paragraph("RELATÓRIO DE PAGAMENTOS", ESTILO_BANNER_TITULO),
        Paragraph(
            f"Gerado em {escape(dados['gerado_em'])} · FitControl",
            ESTILO_BANNER_SUB,
        ),
    ]
    direita = [
        Paragraph(escape(dados["titulo"]), ESTILO_BANNER_MES),
        Paragraph("Resumo mensal", ESTILO_BANNER_MES_SUB),
    ]

    tabela = Table(
        [[esquerda, direita]],
        colWidths=[LARGURA - 46 * mm, 46 * mm],
    )
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COR_MARCA),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return tabela


def _cartao(valor, rotulo, cor):
    estilo = ParagraphStyle(
        "CartaoDinamico",
        parent=ESTILO_CARTAO_VALOR,
        textColor=cor,
    )
    return [
        Paragraph(escape(str(valor)), estilo),
        Paragraph(escape(rotulo), ESTILO_CARTAO_ROTULO),
    ]


def _cartoes(dados):
    total_recebido = _euros(dados["total_recebido"])

    celulas = [
        _cartao(dados["total_alunos"], "Alunos registados", COR_TEXTO),
        _cartao(dados["total_pagamentos"], "Pagamentos no mês", COR_MARCA),
        _cartao(total_recebido, "Receita do mês", COR_VERDE),
        _cartao(len(dados["atrasados"]), "Mensalidades em atraso", COR_VERMELHO),
        _cartao(len(dados["sem_pagamento"]), "Alunos sem pagamento", COR_LARANJA),
    ]

    larguras = [LARGURA / 5] * 5
    tabela = Table([celulas], colWidths=larguras)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, COR_BORDA),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, COR_BORDA),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return tabela


def _secao(titulo):
    tabela = Table(
        [[Paragraph(escape(titulo), ESTILO_SECCAO), ""]],
        colWidths=[None, 20 * mm],
    )
    tabela.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.8, COR_BORDA),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return tabela


def _tabela(colunas, linhas, larguras, alinhamentos=None):
    alinhamentos = alinhamentos or ["esquerda"] * len(colunas)
    estilos_cabecalho = {
        "esquerda": ESTILO_CABECALHO,
        "direita": ESTILO_CABECALHO_DIREITA,
        "centro": ESTILO_CABECALHO_CENTRO,
    }
    estilos_celula = {
        "esquerda": ESTILO_CELULA,
        "direita": ESTILO_CELULA_DIREITA,
        "centro": ESTILO_CELULA_CENTRO,
    }

    cabecalho = [
        _cabecalho(coluna, estilos_cabecalho[alinhamento])
        for coluna, alinhamento in zip(colunas, alinhamentos)
    ]
    dados = [cabecalho]
    for linha in linhas:
        dados.append(
            [
                _celula(valor, estilos_celula[alinhamento])
                for valor, alinhamento in zip(linha, alinhamentos)
            ]
        )

    tabela = Table(dados, colWidths=larguras, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), COR_MARCA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, COR_MARCA),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, COR_BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for indice in range(1, len(dados)):
        if indice % 2 == 0:
            estilo.append(("BACKGROUND", (0, indice), (-1, indice), COR_LINHA))

    tabela.setStyle(TableStyle(estilo))
    return tabela


def _caixa(fluxo):
    tabela = Table([[fluxo]], colWidths=[LARGURA])
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COR_LINHA),
                ("BOX", (0, 0), (-1, -1), 0.6, COR_BORDA),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return tabela


def _vazio(texto):
    return _caixa(Paragraph(escape(texto), ESTILO_VAZIO))


def _elementos(dados):
    elementos = [
        _banner(dados),
        Spacer(1, 8 * mm),
        _cartoes(dados),
    ]

    elementos.append(_secao("Pagamentos do mês"))
    if dados["pagamentos"]:
        elementos.append(
            _tabela(
                ["Aluno", "Plano", "Valor", "Pagamento", "Vencimento"],
                [
                    [
                        pagamento["aluno"],
                        pagamento["plano"],
                        _euros(pagamento["valor"]),
                        pagamento["data_pagamento"],
                        pagamento["data_vencimento"],
                    ]
                    for pagamento in dados["pagamentos"]
                ],
                [62 * mm, 26 * mm, 26 * mm, 32 * mm, 32 * mm],
                ["esquerda", "esquerda", "direita", "centro", "centro"],
            )
        )
    else:
        elementos.append(_vazio("Sem pagamentos registados neste mês."))

    elementos.append(Spacer(1, 6 * mm))
    elementos.append(_secao("Receita por plano"))
    if dados["por_plano"]:
        total_recebido = dados["total_recebido"]
        elementos.append(
            _tabela(
                ["Plano", "Pagamentos", "Total", "% da receita"],
                [
                    [
                        item["plano"],
                        str(item["quantidade"]),
                        _euros(item["total"]),
                        f"{(item['total'] / total_recebido * 100):.1f} %"
                        if total_recebido
                        else "—",
                    ]
                    for item in dados["por_plano"]
                ],
                [58 * mm, 34 * mm, 44 * mm, 42 * mm],
                ["esquerda", "centro", "direita", "centro"],
            )
        )
        elementos.append(Spacer(1, 2 * mm))
        elementos.append(
            Paragraph(
                f"Valor médio por pagamento: <b>{_euros(dados['valor_medio'])}</b>",
                ESTILO_CORPO,
            )
        )
    else:
        elementos.append(_vazio("Sem receita registada neste mês."))

    elementos.append(Spacer(1, 6 * mm))
    elementos.append(_secao("Mensalidades em atraso"))
    if dados["atrasados"]:
        elementos.append(
            _tabela(
                ["Aluno", "Último vencimento"],
                [[item["aluno"], item["vencimento"]] for item in dados["atrasados"]],
                [112 * mm, 66 * mm],
                ["esquerda", "centro"],
            )
        )
    else:
        elementos.append(_vazio("Não há mensalidades vencidas de momento."))

    elementos.append(Spacer(1, 6 * mm))
    elementos.append(_secao("Alunos sem pagamento registado"))
    if dados["sem_pagamento"]:
        nomes = "  ·  ".join(escape(nome) for nome in dados["sem_pagamento"])
        elementos.append(_caixa(Paragraph(nomes, ESTILO_CORPO)))
    else:
        elementos.append(_vazio("Todos os alunos têm pagamento registado."))

    elementos.append(Spacer(1, 8 * mm))
    return elementos


def _construir(caminho, dados, total_paginas=None):
    def rodape(canvas, documento):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COR_SUAVE)
        canvas.drawString(
            16 * mm,
            11 * mm,
            f"FitControl · Relatório de Pagamentos · {dados['titulo']}",
        )
        pagina = canvas.getPageNumber()
        if total_paginas:
            canvas.drawRightString(
                A4[0] - 16 * mm, 11 * mm, f"Página {pagina} de {total_paginas}"
            )
        else:
            canvas.drawRightString(A4[0] - 16 * mm, 11 * mm, f"Página {pagina}")
        canvas.restoreState()

    documento = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=f"Relatório de Pagamentos - {dados['titulo']}",
        author="FitControl",
    )
    documento.build(_elementos(dados), onFirstPage=rodape, onLaterPages=rodape)
    return documento.page


def gerar_relatorio(dados):
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    caminho = os.path.join(
        PASTA_RELATORIOS,
        f"relatorio-{dados['ano']}-{dados['mes']:02d}.pdf",
    )

    total_paginas = _construir(caminho, dados)
    _construir(caminho, dados, total_paginas)

    return caminho