from datetime import datetime


from interface_grafica import relatorio_pdf
from interface_grafica.constants import TEMA
from interface_grafica.dialogs import RelatorioDialog
from interface_grafica.utils import abrir_ficheiro, aluno_por_id, euros, nome_aluno, sem_acentos
from interface_grafica.widgets import (
    Cartao, CampoPesquisa, Pagina, SeletorAluno, Tabela, botao, campo, mensagem, rotulo, toast,
)
from modulos import gestao_alunos, pagamentos, relatorios


class PaginaPagamentos(Pagina):
    titulo = "Pagamentos"
    subtitulo = "Registar mensalidades e consultar o histórico"
    so_admin = False

    def __init__(self, app):
        super().__init__(app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # registar
        # ======================================================
        topo = self.zona()
        topo.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        topo.grid_columnconfigure(0, weight=1)

        form = Cartao(topo)
        form.grid(row=0, column=0, sticky="nsew")
        form.grid_columnconfigure(0, weight=1)
        rotulo(form, "Registar pagamento", 15, "bold").grid(row=0, column=0, columnspan=3, sticky="w",
                                                              padx=20, pady=(16, 10))
        self.seletor = SeletorAluno(form, gestao_alunos.listar_alunos, ao_escolher=self._escolheu)
        self.seletor.grid(row=1, column=0, sticky="ew", padx=(20, 10))
        self.valor = campo(form, placeholder_text="Valor (€)", width=140)
        self.valor.grid(row=1, column=1, padx=(0, 10))
        self.valor.bind("<Return>", lambda _e=None: self._registar())
        botao(form, "Registar", self._registar, icone_nome="visto", width=130).grid(row=1, column=2, padx=(0, 20))
        self.lbl_info = rotulo(form, "Escolha um aluno para ver o plano e a situação.", 12, cor=TEMA["muted"])
        self.lbl_info.grid(row=2, column=0, columnspan=3, sticky="w", padx=20, pady=(8, 16))

        if app.admin:
            resumo = Cartao(topo, width=250)
            resumo.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
            resumo.grid_propagate(False)
            rotulo(resumo, "Recebido este mês", 12, cor=TEMA["muted"]).pack(anchor="w", padx=20, pady=(18, 0))
            self.lbl_mes = rotulo(resumo, "0,00 €", 26, "bold", cor=TEMA["accent"])
            self.lbl_mes.pack(anchor="w", padx=20)
            self.lbl_mes_qtd = rotulo(resumo, "", 12, cor=TEMA["subtle"])
            self.lbl_mes_qtd.pack(anchor="w", padx=20)

        # barra
        # ======================================================
        barra = self.zona()
        barra.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        self.pesquisa = CampoPesquisa(barra, self._preencher, "Pesquisar por aluno...", 290)
        self.pesquisa.pack(side="left")
        if app.admin:
            botao(barra, "Apagar pagamento", self._apagar, "perigo", icone_nome="lixo").pack(side="right")
        botao(barra, "Relatório PDF", lambda: RelatorioDialog(self.app, self._gerar_relatorio),
              "secundario", icone_nome="ficheiro").pack(side="right", padx=(0, 8))

        # histórico
        # ======================================================
        cartao = Cartao(self)
        cartao.grid(row=2, column=0, sticky="nsew")
        cartao.grid_columnconfigure(0, weight=1)
        cartao.grid_rowconfigure(0, weight=1)
        self.tabela = Tabela(cartao, [
            ("aluno", "Aluno", 220, "w"),
            ("plano", "Plano", 100, "w"),
            ("valor", "Valor", 100, "e"),
            ("data", "Pagamento", 120, "center"),
            ("vencimento", "Vencimento", 120, "center"),
            ("estado", "Estado", 90, "center"),
        ], "Ainda não há pagamentos registados.")
        self.tabela.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

    def ao_mostrar(self):
        self._preencher()

    def _escolheu(self, id_aluno):
        aluno = aluno_por_id(id_aluno)
        if not aluno:
            return
        estado, vencimento = pagamentos.situacao_mensalidade(id_aluno)
        textos = {
            "paga": f"em dia até {vencimento}",
            "atrasada": f"em atraso desde {vencimento}",
            "sem_pagamento": "ainda sem pagamentos",
        }
        cor = {"paga": TEMA["accent"], "atrasada": TEMA["danger"]}.get(estado, TEMA["warning"])
        self.lbl_info.configure(text=f"Plano {aluno['plano']}  ·  {textos[estado]}", text_color=cor)
        self.valor.focus_set()

    def _preencher(self):
        termo = self.pesquisa.get()
        linhas = []
        mes_atual = datetime.now().strftime("/%m/%Y")
        total_mes, qtd_mes = 0.0, 0
        for pagamento in reversed(pagamentos.pagamentos):
            if pagamento["data_pagamento"].endswith(mes_atual):
                total_mes += float(pagamento["valor"])
                qtd_mes += 1
            nome = nome_aluno(pagamento["id_aluno"])
            if termo and termo not in sem_acentos(nome):
                continue
            linhas.append((f"p{pagamento.get('id')}", (
                nome, pagamento["plano"], euros(pagamento["valor"]),
                pagamento["data_pagamento"], pagamento["data_vencimento"], pagamento["estado"],
            ), []))
        self.tabela.preencher(linhas)

        if hasattr(self, "lbl_mes"):
            self.lbl_mes.configure(text=euros(total_mes))
            self.lbl_mes_qtd.configure(text=f"{qtd_mes} {'pagamento' if qtd_mes == 1 else 'pagamentos'}")

    def _registar(self):
        id_aluno = self.seletor.get()
        if id_aluno is None:
            if not gestao_alunos.alunos:
                mensagem(self.app, "Sem alunos", "Ainda não existem alunos registados.", "aviso")
            else:
                toast(self, "Escolha um aluno da lista.", "aviso")
                self.seletor.entrada.focus_set()
            return

        texto = self.valor.get().strip().replace("€", "").replace(",", ".")
        try:
            valor = float(texto)
        except ValueError:
            toast(self, "Introduza um valor numérico válido.", "aviso")
            self.valor.focus_set()
            return
        if valor <= 0:
            toast(self, "O valor deve ser superior a zero.", "aviso")
            return

        if pagamentos.registar_pagamento(id_aluno, valor):
            toast(self, f"Pagamento de {euros(valor)} registado para {nome_aluno(id_aluno)}.")
            self.valor.delete(0, "end")
            self.seletor.limpar()
            self.lbl_info.configure(text="Escolha um aluno para ver o plano e a situação.", text_color=TEMA["muted"])
            self._preencher()
            self.app._atualizar_sino()
        else:
            aluno = aluno_por_id(id_aluno)
            if aluno and aluno["plano"] == "Diário":
                mensagem(self.app, "Já pago hoje", "Este aluno tem plano diário e já pagou hoje.", "aviso")
            else:
                mensagem(self.app, "Erro", "Não foi possível registar o pagamento.", "erro")

    def _apagar(self):
        iid = self.tabela.selecionado()
        if not iid:
            toast(self, "Selecione primeiro o pagamento na tabela.", "aviso")
            return
        try:
            id_pagamento = int(iid[1:])
        except ValueError:
            return
        valores = self.tabela.tree.item(iid, "values")
        if not self.app.confirmar_com_senha(
            "Apagar pagamento",
            f"{valores[0]}  ·  {valores[2]}  ({valores[3]})\nIntroduza a sua palavra-passe para confirmar.",
        ):
            return
        if pagamentos.eliminar_pagamento(id_pagamento):
            toast(self, "Pagamento apagado.")
            self._preencher()
        else:
            mensagem(self.app, "Erro", "Não foi possível apagar o pagamento.", "erro")

    def _gerar_relatorio(self, ano, mes):
        def gerar():
            return relatorio_pdf.gerar_relatorio(relatorios.dados_relatorio(ano, mes))

        def pronto(caminho):
            toast(self, "Relatório gerado.")
            try:
                abrir_ficheiro(caminho)
            except Exception:
                mensagem(self.app, "Relatório gerado", f"Guardado em:\n{caminho}", "sucesso")

        toast(self, "A gerar o relatório...", "info")
        self.app.em_fundo(gerar, pronto,
                          lambda e: mensagem(self.app, "Erro", f"Não foi possível gerar o relatório:\n{e}", "erro"))
