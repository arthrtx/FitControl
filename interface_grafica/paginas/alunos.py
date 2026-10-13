import os
from datetime import datetime

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps

from interface_grafica.constants import TEMA
from interface_grafica.dialogs import AlunoFormDialog
from interface_grafica.utils import abrir_ficheiro, aluno_por_id, iniciais, sem_acentos, tem_foto
from interface_grafica.widgets import (
    Cartao, CampoPesquisa, Leds, Pagina, Tabela, botao, confirmar, etiqueta, fonte, mensagem,
    rotulo, segmentos, toast,
)
from modulos import gestao_alunos, pagamentos, privacidade

ESTADOS = {
    "paga": ("Em dia", "accent"),
    "atrasada": ("Em atraso", "danger"),
    "sem_pagamento": ("Sem pagamento", "warning"),
}
FILTROS = ["Todos", "Em dia", "Em atraso", "Sem pagamento"]
CORES_PLANO = {"Diário": "accent", "Mensal": "violet", "Trimestral": "amber", "Anual": "magenta"}


_fotos = {}


def foto_redonda(caminho, lado=144, raio=26):
    # guarda as fotos já preparadas (mudar de aluno na tabela fica instantâneo)
    chave = (caminho, os.path.getmtime(caminho), lado)
    if chave in _fotos:
        return _fotos[chave]
    if len(_fotos) > 60:
        _fotos.clear()
    _fotos[chave] = _preparar_foto(caminho, lado, raio)
    return _fotos[chave]


def _preparar_foto(caminho, lado, raio):
    imagem = Image.open(caminho).convert("RGB")
    imagem = ImageOps.fit(imagem, (lado * 2, lado * 2), Image.LANCZOS)
    mascara = Image.new("L", imagem.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, lado * 2 - 1, lado * 2 - 1), radius=raio * 2, fill=255)
    imagem.putalpha(mascara)
    return ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(lado, lado))


class PaginaAlunos(Pagina):
    titulo = "Alunos"
    subtitulo = "Registar, editar e consultar os alunos da academia"
    so_admin = False

    def __init__(self, app):
        super().__init__(app)
        self._situacoes = {}
        self._foto = None
        self._estreito = False
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # barra de ferramentas
        barra = self.zona()
        barra.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        self.pesquisa = CampoPesquisa(barra, self.atualizar, "Pesquisar por nome ou documento...", 250)
        self.pesquisa.pack(side="left")

        botao(barra, "", self.atualizar, "secundario", icone_nome="atualizar").pack(side="right")
        if app.admin:
            botao(barra, "Eliminar", self._eliminar, "perigo", icone_nome="lixo").pack(side="right", padx=(0, 8))
        botao(barra, "Editar", self._editar, "secundario", icone_nome="editar").pack(side="right", padx=(0, 8))
        botao(barra, "Novo aluno", self.novo_aluno, icone_nome="mais").pack(side="right", padx=(0, 8))

        # tabela
        cartao = Cartao(self)
        cartao.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        cartao.grid_columnconfigure(0, weight=1)
        cartao.grid_rowconfigure(1, weight=1)
        cabecalho = ctk.CTkFrame(cartao, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 0))
        self.lbl_contagem = rotulo(cabecalho, "", 12, cor=TEMA["muted"])
        self.lbl_contagem.pack(side="left")
        self.filtro = segmentos(cabecalho, FILTROS, lambda _v: self.atualizar(), height=30)
        self.filtro.set("Todos")
        self.filtro.pack(side="right")
        self.tabela = Tabela(cartao, [
            ("id", "ID", 50, "center"),
            ("nome", "Nome", 200, "w"),
            ("telemovel", "Telemóvel", 110, "w"),
            ("documento", "Documento", 110, "w"),
            ("plano", "Plano", 90, "w"),
            ("estado", "Mensalidade", 145, "w"),
            ("face", "Face ID", 70, "center"),
        ], "Ainda não há alunos. Carregue em 'Novo aluno' para começar.")
        self.tabela.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))
        self.tabela.ao_selecionar(self._mostrar_detalhes)
        self.tabela.ao_duplo_clique(self._editar)

        self._criar_detalhes()
        self.bind("<Configure>", self._ajustar, add="+")

    def _ajustar(self, _evento=None):
        # em janelas estreitas o painel de detalhes sai para a tabela caber
        estreito = self.winfo_width() < 900 * self._get_widget_scaling()
        if estreito == self._estreito:
            return
        self._estreito = estreito
        if estreito:
            self.painel.grid_remove()
            self.tabela.master.grid_configure(padx=0)
        else:
            self.painel.grid()
            self.tabela.master.grid_configure(padx=(0, 14))

    # painel de detalhes
    # ======================================================
    def _criar_detalhes(self):
        painel = Cartao(self, width=300)
        painel.grid(row=1, column=1, sticky="nsew")
        painel.grid_propagate(False)
        painel.grid_columnconfigure(0, weight=1)
        self.painel = painel

        self.lbl_foto = ctk.CTkLabel(painel, text="", width=144, height=144, corner_radius=26,
                                     fg_color=TEMA["surface_alt"], text_color=TEMA["accent"],
                                     font=fonte(40, "bold"))
        self.lbl_foto.grid(row=0, column=0, pady=(24, 14))
        self.lbl_nome = rotulo(painel, "", 18, "bold", wraplength=250)
        self.lbl_nome.grid(row=1, column=0, padx=20)

        self.etiquetas = ctk.CTkFrame(painel, fg_color="transparent")
        self.etiquetas.grid(row=2, column=0, pady=(8, 14))

        info = ctk.CTkFrame(painel, fg_color=TEMA["surface_alt"], corner_radius=14)
        info.grid(row=3, column=0, sticky="ew", padx=18)
        info.grid_columnconfigure(1, weight=1)
        self.campos = {}
        for i, (chave, texto) in enumerate((("id", "ID"), ("telemovel", "Telemóvel"),
                                           ("documento", "Documento"), ("vencimento", "Vencimento"),
                                           ("face", "Face ID"))):
            rotulo(info, texto, 12, cor=TEMA["muted"]).grid(row=i, column=0, sticky="w", padx=14,
                                                            pady=(10 if i == 0 else 4, 10 if i == 4 else 4))
            valor = rotulo(info, "—", 12, "bold")
            valor.grid(row=i, column=1, sticky="e", padx=14)
            self.campos[chave] = valor

        # LEDs: meses dos últimos 6 que ficaram cobertos por um pagamento
        meses = ctk.CTkFrame(painel, fg_color="transparent")
        meses.grid(row=4, column=0, sticky="ew", padx=18, pady=(14, 0))
        rotulo(meses, "Mensalidades · últimos 6 meses", 11, cor=TEMA["muted"]).pack(anchor="w")
        self.leds_meses = Leds(meses, 252, 18)
        self.leds_meses.pack(anchor="w", pady=(6, 2))
        nomes = ctk.CTkFrame(meses, fg_color="transparent", width=252, height=16)
        nomes.pack(anchor="w")
        nomes.pack_propagate(False)
        self.lbl_meses = []
        for i in range(6):
            lbl = rotulo(nomes, "", 9, cor=TEMA["subtle"], width=42)
            lbl.place(x=i * 42, y=0)
            self.lbl_meses.append(lbl)

        acoes = ctk.CTkFrame(painel, fg_color="transparent")
        acoes.grid(row=5, column=0, sticky="ew", padx=18, pady=14)
        acoes.grid_columnconfigure(0, weight=1)
        self.btn_exportar = botao(acoes, "Exportar dados (RGPD)", self._exportar, "secundario",
                                  icone_nome="download", height=36, font=fonte(12, "bold"))
        self.btn_exportar.grid(row=0, column=0, sticky="ew")

        self.lbl_vazio = rotulo(painel, "Selecione um aluno na tabela\npara ver os detalhes.", 13,
                                cor=TEMA["subtle"], justify="center")
        self._limpar_detalhes()

    def _limpar_detalhes(self):
        for widget in self.painel.winfo_children():
            widget.grid_remove()
        self.lbl_vazio.grid(row=0, column=0, pady=120)

    def _mostrar_detalhes(self):
        iid = self.tabela.selecionado()
        aluno = aluno_por_id(int(iid)) if iid else None
        if not aluno:
            self._limpar_detalhes()
            return

        self.lbl_vazio.grid_remove()
        for widget in self.painel.winfo_children():
            if widget is not self.lbl_vazio:
                widget.grid()

        foto = None
        if tem_foto(aluno):
            try:
                foto = foto_redonda(aluno["foto"])
            except Exception:
                foto = None
        if foto:
            self.lbl_foto.configure(image=foto, text="", fg_color="transparent")
        else:
            # o CTkLabel não larga a imagem antiga com image=None; se ela for
            # apagada da memória dá o erro 'pyimage... doesn't exist'
            self.lbl_foto._label.configure(image="")
            self.lbl_foto.configure(image=None, text=iniciais(aluno["nome"]), fg_color=TEMA["accent_suave"])
        # só se troca a referência depois de o rótulo já usar a imagem nova
        self._foto = foto

        self.lbl_nome.configure(text=aluno["nome"])
        for filho in self.etiquetas.winfo_children():
            filho.destroy()
        estado, vencimento = self._situacoes.get(aluno["id"], ("sem_pagamento", ""))
        texto, cor = ESTADOS[estado]
        etiqueta(self.etiquetas, aluno["plano"], TEMA[CORES_PLANO.get(aluno["plano"], "accent")]).pack(side="left", padx=3)
        etiqueta(self.etiquetas, texto, TEMA[cor]).pack(side="left", padx=3)

        self._mostrar_meses(aluno)

        self.campos["id"].configure(text=f"#{aluno['id']}")
        self.campos["telemovel"].configure(text=aluno["telemovel"])
        self.campos["documento"].configure(text=aluno["documento"])
        self.campos["vencimento"].configure(text=vencimento or "—")
        if aluno.get("embedding"):
            self.campos["face"].configure(text="Ativo", text_color=TEMA["accent"])
        elif tem_foto(aluno):
            self.campos["face"].configure(text="Sem rosto na foto", text_color=TEMA["warning"])
        else:
            self.campos["face"].configure(text="Sem consentimento", text_color=TEMA["muted"])

    def _mostrar_meses(self, aluno):
        nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        hoje = datetime.now()
        meses = []
        mes, ano = hoje.month, hoje.year
        for _ in range(6):
            meses.append((ano, mes))
            mes -= 1
            if mes == 0:
                mes, ano = 12, ano - 1
        meses.reverse()

        periodos = []
        for pagamento in pagamentos.pagamentos:
            if pagamento["id_aluno"] != aluno["id"]:
                continue
            try:
                inicio = datetime.strptime(pagamento["data_pagamento"], "%d/%m/%Y")
                fim = datetime.strptime(pagamento["data_vencimento"], "%d/%m/%Y")
            except (ValueError, KeyError):
                continue
            periodos.append(((inicio.year, inicio.month), (fim.year, fim.month)))

        cores = []
        for chave in meses:
            coberto = any(inicio <= chave <= fim for inicio, fim in periodos)
            if coberto:
                cores.append(TEMA["accent"])
            elif chave == meses[-1]:
                cores.append(TEMA["danger"] if periodos else None)
            else:
                cores.append(None)
        self.leds_meses.definir(cores)
        for lbl, (_ano, mes) in zip(self.lbl_meses, meses):
            lbl.configure(text=nomes[mes - 1])

    # lista
    # ======================================================
    def atualizar(self):
        self._situacoes = pagamentos.situacoes_mensalidade()
        termo = self.pesquisa.get()
        filtro = self.filtro.get()
        linhas = []
        for aluno in gestao_alunos.listar_alunos():
            if termo and termo not in sem_acentos(aluno["nome"]) and termo not in sem_acentos(aluno["documento"]):
                continue
            estado, _venc = self._situacoes.get(aluno["id"], ("sem_pagamento", ""))
            texto, _cor = ESTADOS[estado]
            simbolo = {"paga": "●", "atrasada": "▲", "sem_pagamento": "○"}[estado]
            if filtro != "Todos" and filtro != texto:
                continue
            tags = []
            linhas.append((str(aluno["id"]), (
                aluno["id"], aluno["nome"], aluno["telemovel"], aluno["documento"], aluno["plano"],
                f"{simbolo}  {texto}", "Sim" if aluno.get("embedding") else "—",
            ), tags))

        self.tabela.preencher(linhas)
        total = len(gestao_alunos.alunos)
        self.lbl_contagem.configure(text=f"{len(linhas)} de {total} alunos")
        self._mostrar_detalhes()

    def ao_mostrar(self):
        self.atualizar()

    def _selecionado(self):
        iid = self.tabela.selecionado()
        if not iid:
            toast(self, "Selecione primeiro um aluno na tabela.", "aviso")
            return None
        return aluno_por_id(int(iid))

    # ações
    # ======================================================
    def _depois_de_guardar(self, resultado, nome, foto, id_aluno, mensagem_ok):
        if foto and os.path.exists(foto):
            # a foto temporária não foi usada (erro de validação)
            try:
                os.remove(foto)
            except OSError:
                pass
        if resultado is True:
            self.atualizar()
            if id_aluno is not None:
                if self.tabela.tree.exists(str(id_aluno)):
                    self.tabela.tree.selection_set(str(id_aluno))
                    self.tabela.tree.see(str(id_aluno))
            aluno = aluno_por_id(id_aluno) if id_aluno is not None else None
            if foto and aluno and not aluno.get("embedding"):
                mensagem(self, "Rosto não detetado",
                         "O aluno foi guardado, mas não foi possível detetar o rosto na foto, "
                         "por isso o Face ID não o vai reconhecer.\n\n"
                         "Edite o aluno e tire outra foto com boa luz e de frente para a câmara.", "aviso")
            else:
                toast(self, mensagem_ok)
        elif isinstance(resultado, str):
            mensagem(self, "Dados inválidos", resultado.replace("Erro: ", ""), "erro")
        else:
            mensagem(self, "Erro", f"Não foi possível guardar '{nome}'.", "erro")

    def novo_aluno(self):
        def guardar(nome, telemovel, documento, plano, foto, _remover):
            if foto:
                toast(self, "A guardar o aluno e a calcular o modelo facial...", "info", 6000)
            id_previsto = gestao_alunos.gerar_id()
            self.app.em_fundo(
                lambda: gestao_alunos.criar_aluno(nome, telemovel, documento, plano, foto=foto),
                lambda r: self._depois_de_guardar(r, nome, foto, id_previsto, f"Aluno '{nome}' registado."),
            )

        AlunoFormDialog(self.app, "Novo aluno", guardar)

    def _editar(self):
        aluno = self._selecionado()
        if not aluno:
            return
        id_aluno = aluno["id"]

        def guardar(nome, telemovel, documento, plano, foto, remover):
            if remover and not confirmar(self.app, "Retirar consentimento",
                                         "A fotografia e o modelo facial deste aluno vão ser apagados. "
                                         "Passa a registar a entrada de forma manual.", perigo=True,
                                         texto_botao="Apagar foto"):
                return
            if foto:
                toast(self, "A guardar e a calcular o modelo facial...", "info", 6000)
            self.app.em_fundo(
                lambda: gestao_alunos.editar_aluno(id_aluno, nome, telemovel, documento, plano,
                                                   nova_foto=foto, remover_foto=remover),
                lambda r: self._depois_de_guardar(r, nome, foto, id_aluno, f"Aluno '{nome}' atualizado."),
            )

        AlunoFormDialog(self.app, "Editar aluno", guardar, aluno=aluno)

    def _eliminar(self):
        aluno = self._selecionado()
        if not aluno:
            return
        if not confirmar(self.app, "Eliminar aluno",
                         f"Mover '{aluno['nome']}' para o arquivo? Pode ser restaurado durante 60 dias; "
                         "depois disso os dados são apagados definitivamente.",
                         perigo=True, texto_botao="Eliminar"):
            return
        try:
            ok = gestao_alunos.eliminar_aluno(aluno["id"])
        except Exception as erro:
            mensagem(self.app, "Erro", f"Não foi possível eliminar o aluno.\n\n{erro}", "erro")
            return
        if ok:
            toast(self, f"'{aluno['nome']}' movido para o arquivo.")
            self.atualizar()
        else:
            mensagem(self.app, "Erro", "Não foi possível eliminar o aluno.", "erro")

    def _exportar(self):
        aluno = self._selecionado()
        if not aluno:
            return
        caminho = privacidade.exportar_dados_aluno(aluno["id"], self.app.utilizador["usuario"])
        if not caminho:
            mensagem(self.app, "Erro", "Não foi possível exportar os dados.", "erro")
            return
        toast(self, "Dados exportados. A abrir a pasta...")
        try:
            abrir_ficheiro(os.path.dirname(caminho))
        except Exception:
            mensagem(self.app, "Dados exportados", f"Ficheiro guardado em:\n{caminho}", "sucesso")
