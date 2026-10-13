import re
from datetime import datetime, timedelta

import customtkinter as ctk

from interface_grafica.constants import TEMA, misturar
from interface_grafica.icones import icone
from interface_grafica.widgets import (
    Cartao, CampoPesquisa, Pagina, Tabela, botao, confirmar, mensagem, rotulo, segmentos, toast,
)
from interface_grafica.utils import sem_acentos
from modulos import acessos, gestao_alunos

PERIODOS = {"Hoje": 0, "7 dias": 7, "30 dias": 30, "Tudo": None}


def _aviso(master, texto, cor, nome_icone="info"):
    caixa = ctk.CTkFrame(master, fg_color=misturar(TEMA["bg"], cor, 0.08), corner_radius=14,
                         border_width=1, border_color=misturar(TEMA["bg"], cor, 0.3))
    ctk.CTkLabel(caixa, text="", image=icone(nome_icone, cor, 18)).pack(side="left", padx=(14, 10), pady=12)
    texto_lbl = rotulo(caixa, texto, 12, cor=TEMA["text"], justify="left", anchor="w")
    texto_lbl.pack(side="left", fill="x", expand=True, pady=12, padx=(0, 14))
    caixa.bind("<Configure>", lambda e=None: e is not None and texto_lbl.configure(wraplength=max(200, e.width - 80)), add="+")
    return caixa


# arquivo de presenças
# ======================================================
class PaginaArquivoPresencas(Pagina):
    titulo = "Arquivo de presenças"
    subtitulo = "Histórico de todas as entradas (guardado nos registos do sistema)"
    so_admin = False

    def __init__(self, app):
        super().__init__(app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        barra = self.zona()
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.pesquisa = CampoPesquisa(barra, self.atualizar, "Pesquisar por aluno...", 280)
        self.pesquisa.pack(side="left")
        self.periodo = segmentos(barra, list(PERIODOS), lambda _v: self.atualizar())
        self.periodo.set("30 dias")
        self.periodo.pack(side="left", padx=12)
        if app.admin:
            botao(barra, "Apagar arquivo", self._apagar, "perigo", icone_nome="lixo").pack(side="right")

        cartao = Cartao(self)
        cartao.grid(row=1, column=0, sticky="nsew")
        cartao.grid_columnconfigure(0, weight=1)
        cartao.grid_rowconfigure(1, weight=1)
        self.lbl_total = rotulo(cartao, "", 12, cor=TEMA["muted"])
        self.lbl_total.grid(row=0, column=0, sticky="w", padx=20, pady=(14, 0))
        self.tabela = Tabela(cartao, [
            ("data", "Data", 120, "center"),
            ("hora", "Hora", 90, "center"),
            ("aluno", "Aluno", 400, "w"),
        ], "Sem entradas no período escolhido.")
        self.tabela.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))

    def atualizar(self):
        termo = self.pesquisa.get()
        dias = PERIODOS[self.periodo.get()]
        limite = None
        if dias is not None:
            limite = (datetime.now() - timedelta(days=dias)).date()

        linhas = []
        for log in acessos.arquivo_presencas():
            data_hora = log["data"]
            if limite is not None:
                try:
                    if datetime.strptime(data_hora[:10], "%d/%m/%Y").date() < limite:
                        continue
                except ValueError:
                    pass
            encontrado = re.search(r"'(.+)'", log["evento"])
            nome = encontrado.group(1) if encontrado else log["evento"]
            if termo and termo not in sem_acentos(nome):
                continue
            linhas.append((f"l{log['id']}", (data_hora[:10], data_hora[11:16], nome), []))

        self.tabela.preencher(linhas)
        self.lbl_total.configure(text=f"{len(linhas)} {'entrada' if len(linhas) == 1 else 'entradas'}")

    def ao_mostrar(self):
        self.atualizar()

    def _apagar(self):
        if not self.app.confirmar_com_senha(
            "Apagar arquivo de presenças",
            "Vai apagar TODO o histórico de presenças, incluindo as de hoje.\n"
            "Introduza a sua palavra-passe para confirmar.",
        ):
            return
        acessos.apagar_arquivo_presencas()
        self.atualizar()
        toast(self, "Arquivo de presenças apagado.")


# arquivo de alunos
# ======================================================
class PaginaArquivoAlunos(Pagina):
    titulo = "Arquivo de alunos"
    subtitulo = "Alunos eliminados, que ainda podem ser restaurados"
    so_admin = True

    def __init__(self, app):
        super().__init__(app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        _aviso(self, "Os alunos ficam 60 dias no arquivo e depois são apagados automaticamente. "
                     "Se o aluno pedir o apagamento dos dados (RGPD), use 'Apagar definitivamente'.",
               TEMA["cyan"], "privacidade").grid(row=0, column=0, sticky="ew", pady=(0, 14))

        barra = self.zona()
        barra.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        self.pesquisa = CampoPesquisa(barra, self.atualizar, "Pesquisar por nome...", 280)
        self.pesquisa.pack(side="left")
        botao(barra, "Apagar definitivamente", self._apagar, "perigo", icone_nome="lixo").pack(side="right")
        botao(barra, "Restaurar", self._restaurar, icone_nome="restaurar").pack(side="right", padx=(0, 8))

        cartao = Cartao(self)
        cartao.grid(row=2, column=0, sticky="nsew")
        cartao.grid_columnconfigure(0, weight=1)
        cartao.grid_rowconfigure(0, weight=1)
        self.tabela = Tabela(cartao, [
            ("id", "ID", 60, "center"),
            ("nome", "Nome", 240, "w"),
            ("documento", "Documento", 120, "w"),
            ("plano", "Plano", 100, "w"),
            ("data", "Eliminado em", 120, "center"),
            ("restam", "Apagado em", 120, "center"),
        ], "O arquivo está vazio.")
        self.tabela.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.tabela.ao_duplo_clique(self._restaurar)

    def atualizar(self):
        termo = self.pesquisa.get()
        hoje = datetime.now().date()
        linhas = []
        for aluno in gestao_alunos.listar_alunos_excluidos():
            if termo and termo not in sem_acentos(aluno["nome"]):
                continue
            restam = "—"
            tags = []
            try:
                data = datetime.strptime(aluno.get("data_exclusao", ""), "%d/%m/%Y").date()
                dias = 60 - (hoje - data).days
                restam = f"{dias} dias" if dias != 1 else "1 dia"
                if dias <= 7:
                    tags = ["aviso"]
            except ValueError:
                pass
            linhas.append((str(aluno["id"]), (aluno["id"], aluno["nome"], aluno["documento"], aluno["plano"],
                                              aluno.get("data_exclusao", "—"), restam), tags))
        self.tabela.preencher(linhas)

    def ao_mostrar(self):
        self.atualizar()

    def _selecionado(self):
        iid = self.tabela.selecionado()
        if not iid:
            toast(self, "Selecione primeiro um aluno.", "aviso")
            return None
        return int(iid)

    def _restaurar(self):
        id_aluno = self._selecionado()
        if id_aluno is None:
            return
        try:
            ok = gestao_alunos.restaurar_aluno(id_aluno)
        except Exception as erro:
            mensagem(self.app, "Erro", str(erro), "erro")
            return
        if ok:
            toast(self, "Aluno restaurado.")
            self.atualizar()
        else:
            mensagem(self.app, "Não foi possível restaurar",
                     "Já existe um aluno ativo com o mesmo documento.", "aviso")

    def _apagar(self):
        id_aluno = self._selecionado()
        if id_aluno is None:
            return
        nome = self.tabela.tree.item(str(id_aluno), "values")[1]
        if not confirmar(self.app, "Apagar definitivamente",
                         f"Todos os dados de '{nome}' (incluindo a fotografia) vão ser apagados. "
                         "Esta ação não pode ser desfeita.", perigo=True, texto_botao="Apagar"):
            return
        if gestao_alunos.apagar_definitivamente(id_aluno):
            toast(self, "Dados do aluno apagados.")
            self.atualizar()
