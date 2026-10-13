import threading

import customtkinter as ctk

from interface_grafica.camera_ui import LeitorCamera, VisorCamera, libertar_camera
from interface_grafica.constants import TEMA
from interface_grafica.widgets import (
    Cartao, Pagina, botao, campo, etiqueta, mensagem, opcao, rotulo, segmentos, toast,
)
from projeto_ginasio import Camara

RESOLUCOES = {"640×480": (640, 480), "1280×720": (1280, 720), "1920×1080": (1920, 1080)}


class PaginaCamara(Pagina):
    titulo = "Câmara"
    subtitulo = "Escolher e testar a câmara usada no Face ID e nas fotografias"
    so_admin = False

    def __init__(self, app):
        super().__init__(app)
        self.leitor = None
        self.grid_columnconfigure(0, weight=4, uniform="c")
        self.grid_columnconfigure(1, weight=6, uniform="c")
        self.grid_rowconfigure(0, weight=1)

        config = Camara.carregar_config_camera()

        # configuração
        # ======================================================
        cartao = Cartao(self)
        cartao.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        cartao.grid_columnconfigure(0, weight=1)
        rotulo(cartao, "Configuração", 15, "bold").grid(row=0, column=0, sticky="w", padx=22, pady=(18, 2))
        rotulo(cartao, "Fica guardada e é usada em toda a aplicação.", 12, cor=TEMA["muted"]).grid(
            row=1, column=0, sticky="w", padx=22, pady=(0, 16))

        rotulo(cartao, "Câmara", 12, cor=TEMA["muted"]).grid(row=2, column=0, sticky="w", padx=22)
        linha = ctk.CTkFrame(cartao, fg_color="transparent")
        linha.grid(row=3, column=0, sticky="ew", padx=22, pady=(4, 14))
        linha.grid_columnconfigure(0, weight=1)
        self.camera = ctk.StringVar(value=f"Câmara {config['indice']}")
        self.menu_camera = opcao(linha, values=[self.camera.get()], variable=self.camera)
        self.menu_camera.grid(row=0, column=0, sticky="ew")
        self.btn_detetar = botao(linha, "Detetar", self._detetar, "secundario", icone_nome="pesquisa")
        self.btn_detetar.grid(row=0, column=1, padx=(8, 0))

        rotulo(cartao, "Resolução", 12, cor=TEMA["muted"]).grid(row=4, column=0, sticky="w", padx=22)
        atual = f"{config['largura']}×{config['altura']}"
        self.resolucao = segmentos(cartao, list(RESOLUCOES) + ["Outra"], self._trocou_resolucao)
        self.resolucao.grid(row=5, column=0, sticky="ew", padx=22, pady=(4, 10))
        self.resolucao.set(atual if atual in RESOLUCOES else "Outra")

        self.outra = ctk.CTkFrame(cartao, fg_color="transparent")
        self.outra.grid(row=6, column=0, sticky="ew", padx=22)
        self.largura = campo(self.outra, width=110, placeholder_text="Largura")
        self.largura.pack(side="left")
        rotulo(self.outra, "×", 14, cor=TEMA["muted"]).pack(side="left", padx=8)
        self.altura = campo(self.outra, width=110, placeholder_text="Altura")
        self.altura.pack(side="left")
        self.largura.insert(0, str(config["largura"]))
        self.altura.insert(0, str(config["altura"]))
        self._trocou_resolucao(self.resolucao.get())

        rotulo(cartao, "Resoluções mais baixas deixam o Face ID mais rápido em computadores fracos.",
               11, cor=TEMA["subtle"], wraplength=300, justify="left").grid(row=7, column=0, sticky="w",
                                                                           padx=22, pady=(12, 0))

        cartao.grid_rowconfigure(8, weight=1)
        botao(cartao, "Guardar configuração", self._guardar, icone_nome="visto").grid(
            row=9, column=0, sticky="ew", padx=22, pady=22)

        # pré-visualização
        # ======================================================
        ver = Cartao(self)
        ver.grid(row=0, column=1, sticky="nsew")
        ver.grid_columnconfigure(0, weight=1)
        ver.grid_rowconfigure(1, weight=1)
        topo = ctk.CTkFrame(ver, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 10))
        rotulo(topo, "Pré-visualização", 15, "bold").pack(side="left")
        self.lbl_estado = etiqueta(topo, "Desligada", TEMA["subtle"])
        self.lbl_estado.pack(side="left", padx=10)

        moldura = ctk.CTkFrame(ver, fg_color=TEMA["surface_alt"], corner_radius=16)
        moldura.grid(row=1, column=0, sticky="nsew", padx=16)
        self.visor = VisorCamera(moldura, texto_vazio="Carregue em 'Testar câmara' para ver a imagem.")
        self.visor.pack(fill="both", expand=True, padx=6, pady=6)

        botoes = ctk.CTkFrame(ver, fg_color="transparent")
        botoes.grid(row=2, column=0, sticky="ew", padx=22, pady=18)
        self.btn_testar = botao(botoes, "Testar câmara", self._testar, icone_nome="play")
        self.btn_testar.pack(side="left")
        botao(botoes, "Gravar vídeo", self._gravar, "secundario", icone_nome="camara").pack(side="left", padx=8)
        rotulo(botoes, "Gravação: S pausa · R retoma · ESC termina", 11, cor=TEMA["subtle"]).pack(side="right")

    # configuração
    # ======================================================
    def _indice(self):
        try:
            return int(self.camera.get().replace("Câmara", "").strip())
        except ValueError:
            return 0

    def _trocou_resolucao(self, valor):
        if valor == "Outra":
            self.outra.grid()
        else:
            self.outra.grid_remove()

    def _detetar(self):
        self._parar_teste()
        libertar_camera()
        self.btn_detetar.configure(state="disabled", text="A procurar...")

        def detetar():
            try:
                encontradas = Camara.listar_cameras() or []
            except Exception:
                encontradas = []
            self.after(0, lambda: self._detetadas(encontradas))

        threading.Thread(target=detetar, daemon=True).start()

    def _detetadas(self, encontradas):
        if not self.winfo_exists():
            return
        self.btn_detetar.configure(state="normal", text="Detetar")
        if not encontradas:
            mensagem(self.app, "Sem câmaras", "Não foi encontrada nenhuma câmara ligada a este computador.", "aviso")
            return
        valores = [f"Câmara {i}" for i in encontradas]
        self.menu_camera.configure(values=valores)
        if self.camera.get() not in valores:
            self.camera.set(valores[0])
        toast(self, f"{len(encontradas)} {'câmara encontrada' if len(encontradas) == 1 else 'câmaras encontradas'}.", "info")

    def _guardar(self):
        escolha = self.resolucao.get()
        if escolha in RESOLUCOES:
            largura, altura = RESOLUCOES[escolha]
        else:
            try:
                largura, altura = int(self.largura.get()), int(self.altura.get())
            except ValueError:
                toast(self, "Introduza valores numéricos para a resolução.", "aviso")
                return
        if largura < 320 or altura < 240 or largura > 3840 or altura > 2160:
            toast(self, "A resolução tem de estar entre 320×240 e 3840×2160.", "aviso")
            return
        Camara.guardar_config_camera(indice=self._indice(), largura=largura, altura=altura)
        toast(self, "Configuração da câmara guardada.")
        if self.leitor and self.leitor.a_correr:
            self._parar_teste()
            self._testar()

    # teste / gravação
    # ======================================================
    def _testar(self):
        if self.leitor and self.leitor.a_correr:
            self._parar_teste()
            return
        self.leitor = LeitorCamera(indice=self._indice(), detetar=True)
        self.leitor.iniciar()
        self.visor.ligar(self.leitor.obter)
        self.btn_testar.configure(text="Parar teste")
        self.lbl_estado.configure(text="Ligada", text_color=TEMA["accent"])
        self.after(1500, self._verificar_erro)

    def _verificar_erro(self):
        if self.leitor and self.leitor.erro and self.winfo_exists():
            self._parar_teste()
            self.visor.desligar(self.leitor.erro if self.leitor else "Erro na câmara.")

    def _parar_teste(self):
        if self.leitor:
            self.leitor.parar()
        self.visor.desligar("Carregue em 'Testar câmara' para ver a imagem.")
        if self.btn_testar.winfo_exists():
            self.btn_testar.configure(text="Testar câmara")
            self.lbl_estado.configure(text="Desligada", text_color=TEMA["subtle"])

    def _gravar(self):
        self._parar_teste()
        libertar_camera()
        toast(self, "A gravação abre numa janela à parte.", "info")
        threading.Thread(target=Camara.gravarVideo, kwargs={"indice_camera": self._indice()}, daemon=True).start()

    def ao_esconder(self):
        self._parar_teste()
