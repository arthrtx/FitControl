import threading
import time
from datetime import datetime

import customtkinter as ctk

from interface_grafica import face_id
from interface_grafica.camera_ui import VisorCamera, libertar_camera
from interface_grafica.constants import TEMA
from interface_grafica.icones import icone
from interface_grafica.utils import nome_aluno
from interface_grafica.widgets import (
    Cartao, Leds, Pagina, SeletorAluno, Tabela, ativar, botao, etiqueta, mensagem, ponto, rotulo, toast,
)
from modulos import gestao_alunos, presencas

CORES_ESTADO = {
    "ativo": "accent",
    "reconhecido": "accent",
    "desconhecido": "warning",
    "a_iniciar": "cyan",
    "a_parar": "muted",
    "sem_alunos": "warning",
    "erro": "danger",
    "parado": "subtle",
}


class PaginaPresencas(Pagina):
    titulo = "Presenças"
    subtitulo = "Entradas de hoje, com Face ID ou registo manual"
    so_admin = False

    def __init__(self, app):
        super().__init__(app)
        # Transparente já usa self._job para o repaint; o vigilante do Face ID
        # guarda-se noutro atributo para não roubar o repaint da página
        self._job_vigiar = None
        self._contador = None
        self._arranque = 0
        self._quer_iniciar = False
        self._ultimo_estado = None
        self._ultimo_ativo = None
        self.grid_columnconfigure(0, weight=5, uniform="p")
        self.grid_columnconfigure(1, weight=6, uniform="p")
        self.grid_rowconfigure(0, weight=1)

        self._criar_face_id()
        self._criar_lado_direito()

    # Face ID
    # ======================================================
    def _criar_face_id(self):
        cartao = Cartao(self)
        cartao.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        cartao.grid_columnconfigure(0, weight=1)
        cartao.grid_rowconfigure(1, weight=1)

        topo = ctk.CTkFrame(cartao, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 10))
        ctk.CTkLabel(topo, text="", image=icone("rosto", TEMA["accent"], 20), width=38, height=38,
                     fg_color=TEMA["accent_suave"], corner_radius=12).pack(side="left")
        textos = ctk.CTkFrame(topo, fg_color="transparent")
        textos.pack(side="left", padx=12)
        rotulo(textos, "Face ID", 15, "bold").pack(anchor="w")
        rotulo(textos, "Reconhecimento facial na entrada", 12, cor=TEMA["muted"]).pack(anchor="w")

        moldura = ctk.CTkFrame(cartao, fg_color=TEMA["surface_alt"], corner_radius=16)
        moldura.grid(row=1, column=0, sticky="nsew", padx=16)
        self.visor = VisorCamera(moldura, texto_vazio="Face ID desligado\nCarregue em 'Iniciar' para ligar a câmara.")
        self.visor.pack(fill="both", expand=True, padx=6, pady=6)

        estado = ctk.CTkFrame(cartao, fg_color="transparent")
        estado.grid(row=2, column=0, sticky="ew", padx=20, pady=(14, 4))
        estado.grid_columnconfigure(1, weight=1)
        self.ponto = ponto(estado, TEMA["subtle"], 12)
        self.ponto.grid(row=0, column=0, padx=(0, 10))
        self.lbl_estado = rotulo(estado, "Face ID inativo", 14, "bold", anchor="w")
        self.lbl_estado.grid(row=0, column=1, sticky="ew")
        self.lbl_detalhe = rotulo(estado, "", 12, cor=TEMA["muted"], anchor="w", justify="left", wraplength=320)
        self.lbl_detalhe.grid(row=1, column=1, sticky="ew")

        botoes = ctk.CTkFrame(cartao, fg_color="transparent")
        botoes.grid(row=3, column=0, sticky="ew", padx=20, pady=(8, 18))
        botoes.grid_columnconfigure((0, 1), weight=1)
        self.btn_iniciar = botao(botoes, "Iniciar Face ID", self.iniciar_face_id, icone_nome="play")
        self.btn_iniciar.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.btn_parar = botao(botoes, "Parar", self.parar_face_id, "secundario", icone_nome="parar")
        self.btn_parar.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def iniciar_face_id(self):
        modulo = face_id.modulo()
        if modulo is None:
            # o módulo ainda está a carregar em segundo plano: tenta daqui a pouco
            face_id.carregar_em_fundo()
            self._quer_iniciar = True
            self._mostrar_estado("a_iniciar", "A preparar o Face ID", "A carregar o reconhecimento facial...")
            return
        self._quer_iniciar = False
        if modulo.reconhecimento_ativo():
            return
        if modulo._reconhecimento_em_execucao:
            # ainda está a fechar a sessão anterior
            self.after(300, self.iniciar_face_id)
            return
        libertar_camera()
        threading.Thread(target=modulo.iniciar_reconhecimento, daemon=True).start()
        self.visor.ligar(modulo.obter_frame)
        self._arranque = time.time()

    def parar_face_id(self):
        self._quer_iniciar = False
        modulo = face_id.modulo()
        if modulo is not None:
            modulo.parar_reconhecimento()

    def _mostrar_estado(self, estado, titulo, detalhe):
        # só mexe nos widgets quando algo muda (cada configure redesenha o widget)
        chave = (estado, titulo, detalhe)
        if chave == self._ultimo_estado:
            return
        self._ultimo_estado = chave
        cor = TEMA[CORES_ESTADO.get(estado, "subtle")]
        self.ponto.configure(fg_color=cor)
        self.lbl_estado.configure(text=titulo, text_color=cor if estado != "parado" else TEMA["text"])
        self.lbl_detalhe.configure(text=detalhe)

    def _mostrar_botoes(self, ativo):
        if ativo == self._ultimo_ativo:
            return
        self._ultimo_ativo = ativo
        ativar(self.btn_iniciar, not ativo)
        ativar(self.btn_parar, ativo, "secundario")

    def _vigiar(self):
        self._job_vigiar = None
        modulo = face_id.modulo()

        if modulo is None:
            if face_id.erro:
                self._quer_iniciar = False
                self._mostrar_estado("erro", "Face ID indisponível", face_id.erro)
            elif not self._quer_iniciar:
                self._mostrar_estado("parado", "Face ID inativo",
                                     "Carregue em 'Iniciar Face ID' para começar o reconhecimento facial.")
            self._mostrar_botoes(self._quer_iniciar)
            self._job_vigiar = self.after(400, self._vigiar)
            return

        if self._quer_iniciar:
            self.iniciar_face_id()

        estado = modulo.obter_estado_reconhecimento()
        self._mostrar_estado(estado["estado"], estado["titulo"], estado["detalhe"])

        ativo = modulo._reconhecimento_em_execucao
        self._mostrar_botoes(ativo)
        a_arrancar = time.time() - self._arranque < 1.5
        if not ativo and not a_arrancar and self.visor.fonte is not None:
            self.visor.desligar("Face ID desligado\nCarregue em 'Iniciar' para ligar a câmara.")

        contador = modulo.obter_novas_presencas()
        if self._contador is not None and contador != self._contador:
            self._atualizar_lista()
            toast(self, estado["detalhe"] or "Presença registada.")
        self._contador = contador

        self._job_vigiar = self.after(400, self._vigiar)

    # registo manual + lista
    # ======================================================
    def _criar_lado_direito(self):
        lado = self.zona()
        lado.grid(row=0, column=1, sticky="nsew")
        lado.grid_columnconfigure(0, weight=1)
        lado.grid_rowconfigure(1, weight=1)

        manual = Cartao(lado)
        manual.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        manual.grid_columnconfigure(0, weight=1)
        rotulo(manual, "Registo manual", 15, "bold").grid(row=0, column=0, columnspan=2, sticky="w",
                                                          padx=20, pady=(16, 2))
        rotulo(manual, "Para alunos sem Face ID ou quando a câmara não está disponível.", 12,
               cor=TEMA["muted"]).grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 10))
        self.seletor = SeletorAluno(manual, gestao_alunos.listar_alunos)
        self.seletor.grid(row=2, column=0, sticky="ew", padx=(20, 10), pady=(0, 18))
        self.seletor.entrada.bind("<Return>", lambda _e=None: self.after(50, self._registar), add="+")
        botao(manual, "Registar entrada", self._registar, icone_nome="visto").grid(
            row=2, column=1, padx=(0, 20), pady=(0, 18))

        lista = Cartao(lado)
        lista.grid(row=1, column=0, sticky="nsew")
        lista.grid_columnconfigure(0, weight=1)
        lista.grid_rowconfigure(2, weight=1)
        topo = ctk.CTkFrame(lista, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))
        rotulo(topo, "Entradas de hoje", 15, "bold").pack(side="left")
        self.lbl_total = etiqueta(topo, "0", TEMA["accent"])
        self.lbl_total.pack(side="left", padx=10)
        botao(topo, "Arquivo", lambda: self.app.mostrar_pagina("arq_presencas"), "fantasma",
              icone_nome="relogio", height=32).pack(side="right")

        self.tabela = Tabela(lista, [
            ("hora", "Hora", 80, "center"),
            ("aluno", "Aluno", 240, "w"),
            ("id", "ID", 60, "center"),
        ], "Ainda ninguém entrou hoje.")
        self.tabela.grid(row=2, column=0, sticky="nsew", padx=12, pady=(4, 12))

        # LEDs por hora (das 6h às 23h): mostra as horas de maior movimento
        horas = ctk.CTkFrame(lista, fg_color="transparent")
        horas.grid(row=1, column=0, sticky="w", padx=20, pady=(4, 6))
        self.leds_horas = Leds(horas, 18 * 18, 34)
        self.leds_horas.pack(anchor="w")
        escala = ctk.CTkFrame(horas, fg_color="transparent", width=18 * 18, height=14)
        escala.pack(anchor="w")
        for i, hora in enumerate(range(6, 24)):
            if hora % 3 == 0:
                rotulo(escala, f"{hora}h", 9, cor=TEMA["subtle"]).place(x=i * 18 + 9, y=0, anchor="n")

    def _atualizar_lista(self):
        with presencas._presencas_lock:
            lista = list(reversed(presencas.presencas))
        linhas = []
        for n, registo in enumerate(lista):
            linhas.append((f"r{n}", (registo["hora"], nome_aluno(registo["id_aluno"]), registo["id_aluno"]), []))
        self.tabela.preencher(linhas)
        self.lbl_total.configure(text=str(len(lista)))

        por_hora = [0] * 18
        for registo in lista:
            try:
                hora = int(registo["hora"][:2])
            except (ValueError, TypeError):
                continue
            if 6 <= hora <= 23:
                por_hora[hora - 6] += 1
        self.leds_horas.equalizador(por_hora, TEMA["accent"], niveis=4)

    def _registar(self):
        id_aluno = self.seletor.get()
        if id_aluno is None:
            toast(self, "Escolha um aluno da lista.", "aviso")
            return
        if presencas.registar_presenca(id_aluno) == "OK":
            toast(self, f"Entrada registada para {nome_aluno(id_aluno)}.")
            self.seletor.limpar()
            self._atualizar_lista()
        else:
            mensagem(self.app, "Erro", "Não foi possível registar a presença.", "erro")

    # ciclo da página
    # ======================================================
    def ao_mostrar(self):
        # a lista diária muda de dia à meia-noite
        hoje = datetime.now().strftime("%d/%m/%Y")
        if any(p["data"] != hoje for p in presencas.presencas):
            presencas.carregar_presencas()
        self._atualizar_lista()
        self._contador = None
        self._vigiar()

    def ao_esconder(self):
        if self._job_vigiar:
            try:
                self.after_cancel(self._job_vigiar)
            except Exception:
                pass
            self._job_vigiar = None
        self.parar_face_id()
        self.visor.desligar()
