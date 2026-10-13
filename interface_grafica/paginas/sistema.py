import customtkinter as ctk

from interface_grafica.constants import TEMA
from interface_grafica.dialogs import DialogoTermos, FuncionarioFormDialog
from interface_grafica.icones import icone
from interface_grafica.utils import sem_acentos
from interface_grafica.widgets import (
    Cartao, CampoPesquisa, Pagina, Tabela, botao, confirmar, mensagem, opcao, rotulo, toast,
)
from modulos import acessos, funcionarios as gestao_funcionarios, gestao_alunos, privacidade
from projeto_ginasio.db_adapter import add_log, get_logs_por_tipo, limpar_todos_logs

TIPOS_LOG = {
    "Todos": "todos",
    "Administração": "administracao",
    "Presenças": "presenca",
    "Pagamentos": "pagamento",
    "Alunos": "aluno",
    "Funcionários": "funcionario",
    "Geral": "geral",
}
NOMES_TIPO = {v: k for k, v in TIPOS_LOG.items()}


# funcionários
# ======================================================
class PaginaFuncionarios(Pagina):
    titulo = "Funcionários"
    subtitulo = "Contas de acesso e permissões"
    so_admin = True

    def __init__(self, app):
        super().__init__(app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        barra = self.zona()
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.pesquisa = CampoPesquisa(barra, self.atualizar, "Pesquisar funcionário...", 280)
        self.pesquisa.pack(side="left")
        botao(barra, "", self.atualizar, "secundario", icone_nome="atualizar").pack(side="right")
        botao(barra, "Eliminar", self._eliminar, "perigo", icone_nome="lixo").pack(side="right", padx=(0, 8))
        botao(barra, "Editar", self._editar, "secundario", icone_nome="editar").pack(side="right", padx=(0, 8))
        botao(barra, "Novo funcionário", self._novo, icone_nome="mais").pack(side="right", padx=(0, 8))

        cartao = Cartao(self)
        cartao.grid(row=1, column=0, sticky="nsew")
        cartao.grid_columnconfigure(0, weight=1)
        cartao.grid_rowconfigure(0, weight=1)
        self.tabela = Tabela(cartao, [
            ("id", "ID", 60, "center"),
            ("nome", "Nome", 240, "w"),
            ("usuario", "Utilizador", 160, "w"),
            ("tipo", "Cargo", 140, "w"),
            ("termos", "Termos aceites", 200, "w"),
        ])
        self.tabela.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.tabela.ao_duplo_clique(self._editar)

    def atualizar(self):
        termo = self.pesquisa.get()
        aceites = privacidade.aceitacoes()
        linhas = []
        for funcionario in gestao_funcionarios.listar_funcionarios():
            if termo and termo not in sem_acentos(funcionario["nome"] + " " + funcionario["usuario"]):
                continue
            registo = aceites.get(funcionario["usuario"].lower())
            if not registo:
                texto_termos = "Ainda não aceitou"
            elif registo["versao"] != privacidade.VERSAO_TERMOS:
                texto_termos = f"Versão antiga ({registo['versao']})"
            else:
                texto_termos = f"v{registo['versao']} · {registo['data'][:10]}"
            cargo = "Administrador" if funcionario["tipo"] == "Administrador" else "Funcionário"
            linhas.append((str(funcionario["id"]), (funcionario["id"], funcionario["nome"],
                                                    funcionario["usuario"], cargo, texto_termos), []))
        self.tabela.preencher(linhas)

    def ao_mostrar(self):
        self.atualizar()

    def _selecionado(self):
        iid = self.tabela.selecionado()
        if not iid:
            toast(self, "Selecione primeiro um funcionário.", "aviso")
            return None
        for funcionario in gestao_funcionarios.funcionarios:
            if funcionario["id"] == int(iid):
                return funcionario
        return None

    def _novo(self):
        def guardar(nome, usuario, senha, tipo):
            if gestao_funcionarios.criar_funcionario(nome, usuario, senha, tipo):
                toast(self, f"Funcionário '{nome}' criado.")
                self.atualizar()
            else:
                mensagem(self.app, "Não foi possível criar", "Já existe um funcionário com esse utilizador.", "erro")

        FuncionarioFormDialog(self.app, guardar)

    def _editar(self):
        funcionario = self._selecionado()
        if not funcionario:
            return

        def guardar(nome, usuario, senha, tipo):
            if funcionario["usuario"] == self.app.utilizador["usuario"] and tipo != "Administrador":
                mensagem(self.app, "Atenção", "Não pode retirar a si próprio as permissões de administrador.", "aviso")
                return
            if gestao_funcionarios.editar_funcionario(funcionario["id"], nome, usuario, senha, tipo):
                toast(self, "Funcionário atualizado.")
                self.atualizar()
            else:
                mensagem(self.app, "Não foi possível guardar", "Verifique se o utilizador já existe.", "erro")

        FuncionarioFormDialog(self.app, guardar, funcionario)

    def _eliminar(self):
        funcionario = self._selecionado()
        if not funcionario:
            return
        if funcionario["usuario"] == self.app.utilizador["usuario"]:
            mensagem(self.app, "Atenção", "Não pode eliminar a conta com a sessão iniciada.", "aviso")
            return
        if not confirmar(self.app, "Eliminar funcionário", f"Eliminar a conta de '{funcionario['nome']}'?",
                         perigo=True, texto_botao="Eliminar"):
            return
        if gestao_funcionarios.eliminar_funcionario(funcionario["id"]):
            toast(self, "Funcionário eliminado.")
            self.atualizar()


# administração
# ======================================================
class PaginaAdministracao(Pagina):
    titulo = "Administração"
    subtitulo = "Registos do sistema e proteção de dados"
    so_admin = True

    def __init__(self, app):
        super().__init__(app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._criar_privacidade()

        cartao = Cartao(self)
        cartao.grid(row=1, column=0, sticky="nsew")
        cartao.grid_columnconfigure(0, weight=1)
        cartao.grid_rowconfigure(1, weight=1)

        barra = ctk.CTkFrame(cartao, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 6))
        rotulo(barra, "Registos do sistema", 15, "bold").pack(side="left")
        botao(barra, "Apagar todos", self._apagar, "perigo", icone_nome="lixo", height=36).pack(side="right")
        self.tipo = ctk.StringVar(value="Todos")
        opcao(barra, values=list(TIPOS_LOG), variable=self.tipo, width=170, height=36,
              command=lambda _v: self.atualizar()).pack(side="right", padx=8)
        self.pesquisa = CampoPesquisa(barra, self.atualizar, "Pesquisar...", 220)
        self.pesquisa.pack(side="right")

        self.tabela = Tabela(cartao, [
            ("data", "Data", 150, "center"),
            ("tipo", "Tipo", 120, "w"),
            ("evento", "Evento", 480, "w"),
        ], "Sem registos.")
        self.tabela.grid(row=1, column=0, sticky="nsew", padx=12, pady=(4, 12))

    def _criar_privacidade(self):
        cartao = Cartao(self)
        cartao.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        cartao.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(cartao, text="", image=icone("privacidade", TEMA["accent"], 22), width=46, height=46,
                     fg_color=TEMA["accent_suave"], corner_radius=14).grid(row=0, column=0, rowspan=2,
                                                                           padx=(20, 14), pady=18)
        rotulo(cartao, "Privacidade e RGPD", 15, "bold").grid(row=0, column=1, sticky="sw", pady=(18, 0))
        self.lbl_rgpd = rotulo(cartao, "", 12, cor=TEMA["muted"], anchor="w", justify="left")
        self.lbl_rgpd.grid(row=1, column=1, sticky="nw", pady=(0, 18))
        botao(cartao, "Termos e política", lambda: DialogoTermos(self.app, aceitar=False).esperar(),
              "secundario", icone_nome="ficheiro").grid(row=0, column=2, rowspan=2, padx=20)

    def atualizar(self):
        com_face = sum(1 for a in gestao_alunos.alunos if a.get("embedding"))
        self.lbl_rgpd.configure(text=(
            f"Termos v{privacidade.VERSAO_TERMOS}  ·  {com_face} de {len(gestao_alunos.alunos)} alunos com "
            f"consentimento facial  ·  registos guardados {privacidade.DIAS_CONSERVACAO_LOGS // 365} anos  ·  "
            "arquivo de alunos 60 dias"
        ))

        tipo = TIPOS_LOG[self.tipo.get()]
        logs = acessos.todos_logs(2000) if tipo == "todos" else get_logs_por_tipo(tipo, limite=2000)
        termo = self.pesquisa.get()
        linhas = []
        for log in logs:
            if termo and termo not in sem_acentos(log["evento"]):
                continue
            linhas.append((f"l{log['id']}", (log["data"], NOMES_TIPO.get(log["tipo"], log["tipo"]), log["evento"]), []))
        self.tabela.preencher(linhas)

    def ao_mostrar(self):
        self.atualizar()

    def _apagar(self):
        if not self.app.confirmar_com_senha(
            "Apagar registos",
            "Vai apagar TODOS os registos do sistema (incluindo o arquivo de presenças).\n"
            "Introduza a sua palavra-passe para confirmar.",
        ):
            return
        limpar_todos_logs()
        add_log(f"Registos apagados por {self.app.utilizador['usuario']}.", tipo="administracao")
        self.atualizar()
        toast(self, "Registos apagados.")
