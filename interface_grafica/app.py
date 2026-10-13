"""Janela principal do FitControl."""

import threading
import tkinter as tk
from datetime import datetime

import customtkinter as ctk

from interface_grafica.camera_ui import libertar_camera
from interface_grafica.constants import TEMA, VERSAO, alternar_tema, escuro, modo_tema
from interface_grafica.dialogs import NotificacoesDialog
from interface_grafica.fundo import PainelFundo, Transparente
from interface_grafica.icones import brilho, icone, logo_ctk
from interface_grafica.janela import (
    aplicar_tema_barra, cancelar_pendentes, centralizar, congelar, descongelar, limpar_rastreadores_ctk,
    preparar_janela,
)
from interface_grafica.utils import iniciais, ler_preferencia, guardar_preferencia, setup_paths
from interface_grafica.widgets import AlternadorTema, confirmar, estilo_tabela, fechar_listas, fonte, mensagem, rotulo

setup_paths()

from interface_grafica import face_id, paginas
from modulos import notificacoes
from modulos.autenticacao import e_admin_temporario, terminar_sessao
from projeto_ginasio.main import inicializar

DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

# (secção, [(chave, texto, ícone, só administrador)])
MENU = [
    ("Geral", [
        ("dashboard", "Dashboard", "casa", False),
        ("alunos", "Alunos", "alunos", False),
        ("pagamentos", "Pagamentos", "cartao", False),
        ("presencas", "Presenças", "visto", False),
    ]),
    ("Registos", [
        ("arq_presencas", "Arquivo de presenças", "relogio", False),
        ("excluidos", "Arquivo de alunos", "arquivo", True),
    ]),
    ("Sistema", [
        ("funcionarios", "Funcionários", "funcionarios", True),
        ("administracao", "Administração", "escudo", True),
        ("camera", "Câmara", "camara", False),
    ]),
]


# item do menu lateral
# ======================================================
class ItemMenu(ctk.CTkFrame):
    def __init__(self, master, texto, icone_nome, comando, recolhido=False, perigo=False, altura=44):
        super().__init__(master, fg_color="transparent", corner_radius=12, height=altura,
                         border_width=1, border_color=TEMA["sidebar"])
        self.icone_nome = icone_nome
        self.comando = comando
        self.ativo = False
        self._hover = False
        self.perigo = perigo
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.lbl_icone = ctk.CTkLabel(self, text="", width=24)
        self.lbl_icone.grid(row=0, column=0, padx=(14 if not recolhido else 0, 10), sticky="w" if not recolhido else "")
        self.lbl_texto = ctk.CTkLabel(self, text=texto, font=fonte(13, "bold"), anchor="w")
        if recolhido:
            self.grid_columnconfigure(0, weight=1)
            self.lbl_icone.grid_configure(padx=0)
        else:
            self.lbl_texto.grid(row=0, column=1, sticky="ew")
        self.lbl_brilho = ctk.CTkLabel(self, text="", image=brilho(26, altura - 4, TEMA["magenta"], TEMA["surface_alt"]))

        for widget in (self, self.lbl_icone, self.lbl_texto, self.lbl_brilho):
            widget.bind("<Enter>", self._entrar)
            widget.bind("<Leave>", self._sair)
            widget.bind("<Button-1>", lambda _e=None: self.comando())
            widget.configure(cursor="hand2")
        self._pintar(False)

    def definir_ativo(self, ativo):
        self.ativo = ativo
        self._pintar(False)

    def _entrar(self, _e):
        if not self.ativo and not self._hover:
            self._pintar(True)

    def _sair(self, _e):
        # ao passar do fundo do item para o ícone/texto o Tk manda um "Leave";
        # ignora-se para o item não piscar
        try:
            x, y = self.winfo_pointerxy()
            por_baixo = self.winfo_containing(x, y)
        except (KeyError, tk.TclError):
            por_baixo = None
        if por_baixo is not None and str(por_baixo).startswith(str(self)):
            return
        self._pintar(False)

    def _pintar(self, hover):
        self._hover = hover
        if self.ativo:
            self.configure(fg_color=TEMA["surface_alt"], border_color=TEMA["border"])
            cor_texto, cor_icone = TEMA["text"], TEMA["text"]
            self.lbl_brilho.place(relx=1.0, rely=0.5, x=-1, anchor="e")
        else:
            self.configure(fg_color=TEMA["surface_alt"] if hover else "transparent",
                           border_color=TEMA["surface_alt"] if hover else TEMA["sidebar"])
            cor_texto = TEMA["text"] if hover else TEMA["muted"]
            if self.perigo and hover:
                cor_texto = TEMA["danger"]
            cor_icone = cor_texto
            self.lbl_brilho.place_forget()
        self.lbl_texto.configure(text_color=cor_texto)
        self.lbl_icone.configure(image=icone(self.icone_nome, cor_icone, 18))


# janela
# ======================================================
class AcademiaApp(ctk.CTk):

    def __init__(self, utilizador):
        super().__init__()
        self.utilizador = utilizador
        self.admin = utilizador["tipo"] == "Administrador"
        self.reabrir_login = False

        ctk.set_appearance_mode(modo_tema())
        self.title("FitControl — Gestão de Academia")
        centralizar(self, 1400, 880, margem=60)
        self.minsize(1040, 640)
        preparar_janela(self)

        inicializar()

        self.paginas = {}
        self._pagina_atual = None
        self._itens_menu = {}
        self._relogio_job = None
        self._sino_job = None
        self._recolhido = bool(ler_preferencia("menu_recolhido", False))
        self._a_mudar_tema = False
        self._face_job = None
        self._job_aquecimento = None
        self.protocol("WM_DELETE_WINDOW", self._fechar_aplicacao)

        self._construir()
        self.mostrar_pagina("dashboard")
        self._atualizar_sino()

        # cria as restantes páginas em ocioso: a primeira visita fica
        # instantânea em vez de travar a construir widgets
        self._aquecer_paginas()

        # o Face ID demora a carregar: vai-se adiantando em segundo plano
        self._face_job = self.after(3000, face_id.carregar_em_fundo)

    # construção
    # ======================================================
    def _construir(self):
        estilo_tabela()
        self.configure(fg_color=TEMA["sidebar"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._itens_menu = {}

        self._criar_menu()

        # painel com o degradê; as páginas e o topo mostram-no por trás
        painel = PainelFundo(self, TEMA["sidebar"])
        painel.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)
        self.fundo = painel.fundo
        self.conteudo = painel

        self._criar_topo(painel)

        self._agendar_relogio()

    def _criar_menu(self):
        largura = 84 if self._recolhido else 252
        menu = ctk.CTkFrame(self, fg_color=TEMA["sidebar"], corner_radius=0, width=largura)
        menu.grid(row=0, column=0, sticky="nsw")
        menu.grid_propagate(False)
        menu.grid_columnconfigure(0, weight=1)
        self.menu = menu
        px = 14 if self._recolhido else 18
        # em ecrãs baixos (portáteis) o menu fica mais compacto para caber tudo
        compacto = self.winfo_screenheight() < 900
        altura_item = 38 if compacto else 44

        # logótipo + recolher
        topo = ctk.CTkFrame(menu, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", padx=px, pady=(18, 12) if compacto else (22, 18))
        ctk.CTkLabel(topo, text="", image=logo_ctk(30, TEMA["accent"], TEMA["violet"])).pack(side="left")
        if not self._recolhido:
            rotulo(topo, "FitControl", 18, "bold").pack(side="left", padx=10)
        ctk.CTkButton(topo, text="", width=30, height=30, corner_radius=8, fg_color="transparent",
                      hover_color=TEMA["surface_alt"],
                      image=icone("menu_dir" if self._recolhido else "menu_esq", TEMA["muted"], 18),
                      command=self._recolher).pack(side="right" if not self._recolhido else "left",
                                                   padx=(0, 0) if not self._recolhido else (6, 0))

        # utilizador
        cartao = ctk.CTkFrame(menu, fg_color=TEMA["surface_alt"], corner_radius=14, border_width=1,
                              border_color=TEMA["border"])
        cartao.grid(row=1, column=0, sticky="ew", padx=px, pady=(0, 8 if compacto else 18))
        ctk.CTkLabel(cartao, text=iniciais(self.utilizador["nome"]), width=36, height=36, corner_radius=10,
                     fg_color=TEMA["accent_suave"], text_color=TEMA["accent"],
                     font=fonte(13, "bold")).pack(side="left", padx=8 if self._recolhido else (10, 10),
                                                  pady=6 if compacto else 10)
        if not self._recolhido:
            textos = ctk.CTkFrame(cartao, fg_color="transparent")
            textos.pack(side="left", fill="x", expand=True, pady=8)
            nome = self.utilizador["nome"]
            rotulo(textos, nome if len(nome) <= 20 else nome[:19] + "…", 13, "bold", anchor="w").pack(anchor="w")
            if e_admin_temporario(self.utilizador):
                rotulo(textos, "Conta temporária", 11, cor=TEMA["warning"], anchor="w").pack(anchor="w")
            else:
                rotulo(textos, "Administrador" if self.admin else "Funcionário", 11,
                       cor=TEMA["muted"], anchor="w").pack(anchor="w")

        linha = 2
        for seccao, itens in MENU:
            visiveis = [i for i in itens if self.admin or not i[3]]
            if not visiveis:
                continue
            if not self._recolhido:
                rotulo(menu, seccao.upper(), 10, "bold", cor=TEMA["subtle"], anchor="w",
                       height=18 if compacto else 28).grid(
                    row=linha, column=0, sticky="w", padx=px + 6, pady=(6, 2) if compacto else (10, 4))
            else:
                ctk.CTkFrame(menu, height=1, fg_color=TEMA["border"]).grid(
                    row=linha, column=0, sticky="ew", padx=22, pady=10)
            linha += 1
            for chave, texto, nome_icone, _admin in visiveis:
                item = ItemMenu(menu, texto, nome_icone, lambda c=chave: self.mostrar_pagina(c),
                                self._recolhido, altura=altura_item)
                item.grid(row=linha, column=0, sticky="ew", padx=px, pady=1 if compacto else 2)
                self._itens_menu[chave] = item
                linha += 1

        menu.grid_rowconfigure(linha, weight=1)
        sair = ItemMenu(menu, "Terminar sessão", "sair", self.logout, self._recolhido, perigo=True,
                        altura=altura_item)
        sair.grid(row=linha + 1, column=0, sticky="ew", padx=px, pady=(0, 4))
        rotulo(menu, f"v{VERSAO}" if self._recolhido else f"FitControl v{VERSAO}", 10,
               cor=TEMA["subtle"]).grid(row=linha + 2, column=0, pady=(0, 10 if compacto else 16))

    def _criar_topo(self, painel):
        topo = Transparente(painel, self.fundo, height=70)
        topo.place(x=26, y=20, relwidth=1, width=-52)
        self.topo = topo
        topo.create_text(0, 4, anchor="nw", text="", fill=TEMA["text"], font=("Segoe UI", 21, "bold"), tags="titulo")
        topo.create_text(0, 42, anchor="nw", text="", fill=TEMA["muted"], font=("Segoe UI", 10), tags="subtitulo")
        topo.create_text(0, 35, anchor="e", text="", fill=TEMA["muted"], font=("Segoe UI", 10, "bold"), tags="relogio")
        topo.bind("<Configure>", self._posicionar_topo, add="+")

        self.alternador = AlternadorTema(topo, self.alternar_tema, escuro())
        self.alternador.place(relx=1.0, x=-60, y=35, anchor="e")

        self.btn_sino = ctk.CTkButton(topo, text="", image=icone("sino", TEMA["text"], 18), width=42, height=42,
                                      corner_radius=21, fg_color=TEMA["surface_alt"], hover_color=TEMA["surface_hover"],
                                      border_width=1, border_color=TEMA["border"], command=self._abrir_notificacoes)
        self.btn_sino.place(relx=1.0, x=-2, y=35, anchor="e")
        self.lbl_badge = ctk.CTkLabel(topo, text="", width=18, height=18, corner_radius=9,
                                      fg_color=TEMA["magenta"], text_color="#ffffff", font=fonte(10, "bold"))

    def _posicionar_topo(self, _e=None):
        # o relógio fica à esquerda do botão do tema
        largura = self.topo.winfo_width()
        x = largura - 60 - self.alternador.winfo_reqwidth() - 16
        self.topo.coords("relogio", x, 35)

    def _titulo(self, titulo, subtitulo):
        self.topo.itemconfigure("titulo", text=titulo)
        self.topo.itemconfigure("subtitulo", text=subtitulo)

    # páginas
    # ======================================================
    def mostrar_pagina(self, nome):
        classe = paginas.PAGINAS.get(nome)
        if classe is None or (classe.so_admin and not self.admin):
            return
        if nome == self._pagina_atual:
            return

        fechar_listas()
        anterior = self.paginas.get(self._pagina_atual)
        if anterior is not None:
            try:
                anterior.ao_esconder()
            except Exception as erro:
                print(f"Erro ao sair da página: {erro}")
            anterior.place_forget()

        try:
            if nome not in self.paginas:
                self.paginas[nome] = classe(self)
            pagina = self.paginas[nome]
            pagina.place(x=26, y=98, relwidth=1, width=-52, relheight=1, height=-120)
            self._pagina_atual = nome
            self._titulo(pagina.titulo, pagina.subtitulo)
            for chave, item in self._itens_menu.items():
                item.definir_ativo(chave == nome)
            pagina.ao_mostrar()
        except Exception as erro:
            import traceback
            traceback.print_exc()
            mensagem(self, "Erro", f"Não foi possível abrir esta página.\n\n{erro}", "erro")

    def _recolher(self):
        self._recolhido = not self._recolhido
        guardar_preferencia("menu_recolhido", self._recolhido)
        self.menu.destroy()
        self._criar_menu()
        if self._pagina_atual in self._itens_menu:
            self._itens_menu[self._pagina_atual].definir_ativo(True)

    def _aquecer_paginas(self):
        """Cria as páginas em tempos mortos (uma de cada vez).

        Sem isto a primeira visita a cada página demorava ~0,4 s a
        construir os widgets, o que se sentia como lag ao navegar."""
        if self._job_aquecimento:
            try:
                self.after_cancel(self._job_aquecimento)
            except Exception:
                pass
            self._job_aquecimento = None
        pendentes = [nome for nome, classe in paginas.PAGINAS.items()
                     if nome not in self.paginas and (self.admin or not classe.so_admin)]
        self._agenda_aquecimento(pendentes)

    def _agenda_aquecimento(self, pendentes, atraso=400):
        if not pendentes:
            self._job_aquecimento = None
            return
        nome, resto = pendentes[0], pendentes[1:]

        def passo():
            self._job_aquecimento = None
            if nome not in self.paginas:
                try:
                    self.paginas[nome] = paginas.PAGINAS[nome](self)
                except Exception as erro:
                    print(f"Erro ao aquecer a página '{nome}': {erro}")
            self._agenda_aquecimento(resto, atraso)

        self._job_aquecimento = self.after(atraso, passo)

    def alternar_tema(self):
        if self._a_mudar_tema:
            return
        self._a_mudar_tema = True
        pagina = self._pagina_atual or "dashboard"
        cobertura = congelar(self)
        self._parar_tudo()

        # primeiro destrói-se tudo e só depois se muda o tema: assim o
        # customtkinter não perde tempo a repintar widgets que vão sair
        for filho in self.winfo_children():
            if filho is not cobertura:
                filho.destroy()
        # os callbacks dos widgets mortos saem logo das listas globais do
        # customtkinter, para as trocas de tema não ficarem cada vez mais lentas
        limpar_rastreadores_ctk()
        self.paginas = {}
        self._pagina_atual = None
        alternar_tema()

        self._construir()
        self.mostrar_pagina(pagina)
        self._aquecer_paginas()
        self._atualizar_sino()
        aplicar_tema_barra(self)
        descongelar(self, cobertura)
        self._face_job = self.after(3000, face_id.carregar_em_fundo)
        self.after(150, lambda: setattr(self, "_a_mudar_tema", False))

    # relógio e notificações
    # ======================================================
    def _agendar_relogio(self):
        agora = datetime.now()
        texto = f"{DIAS[agora.weekday()]}, {agora.day} {MESES[agora.month - 1]}  ·  {agora.strftime('%H:%M:%S')}"
        if self.topo.winfo_exists():
            self.topo.itemconfigure("relogio", text=texto)
        self._relogio_job = self.after(1000, self._agendar_relogio)

    def _atualizar_sino(self):
        if self._sino_job:
            self.after_cancel(self._sino_job)
        try:
            notificacoes.verificar()
            total = notificacoes.por_ler()
        except Exception as erro:
            print(f"Erro nas notificações: {erro}")
            total = 0
        if self.lbl_badge.winfo_exists():
            if total:
                self.lbl_badge.configure(text=str(total) if total < 100 else "99+")
                self.lbl_badge.place(relx=1.0, x=0, y=10, anchor="ne")
                self.lbl_badge.lift()
            else:
                self.lbl_badge.place_forget()
        self._sino_job = self.after(60000, self._atualizar_sino)

    def _abrir_notificacoes(self):
        notificacoes.verificar()
        NotificacoesDialog(self, ao_fechar=self._atualizar_sino)

    # confirmação por palavra-passe (operações irreversíveis)
    # ======================================================
    def confirmar_com_senha(self, titulo, texto):
        from modulos import funcionarios as gestao_funcionarios
        from interface_grafica.widgets import pedir_senha

        senha = pedir_senha(self, titulo, texto)
        if senha is None:
            return False

        guardada = self.utilizador.get("senha")
        for funcionario in gestao_funcionarios.funcionarios:
            if funcionario["id"] == self.utilizador["id"]:
                guardada = funcionario["senha"]
                break

        if not gestao_funcionarios.senha_correta(guardada, senha):
            mensagem(self, "Palavra-passe incorreta", "A operação foi cancelada.", "erro")
            return False
        return True

    # tarefas em segundo plano
    # ======================================================
    def em_fundo(self, funcao, ao_terminar, ao_erro=None):
        """Corre funcao() num thread e chama ao_terminar(resultado) no
        thread da interface, sem congelar a janela."""
        estado = {}

        def trabalho():
            try:
                estado["resultado"] = funcao()
            except Exception as erro:
                estado["erro"] = erro

        thread = threading.Thread(target=trabalho, daemon=True)
        thread.start()

        def verificar():
            if thread.is_alive():
                self.after(80, verificar)
            elif "erro" in estado:
                if ao_erro:
                    ao_erro(estado["erro"])
                else:
                    mensagem(self, "Erro", str(estado["erro"]), "erro")
            else:
                ao_terminar(estado.get("resultado"))

        self.after(80, verificar)

    # sair
    # ======================================================
    def destroy(self):
        cancelar_pendentes(self)
        super().destroy()

    def _parar_tudo(self):
        for job in (self._relogio_job, self._sino_job, self._face_job, self._job_aquecimento):
            if job:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
        self._relogio_job = self._sino_job = self._face_job = self._job_aquecimento = None
        pagina = self.paginas.get(self._pagina_atual)
        if pagina is not None:
            try:
                pagina.ao_esconder()
            except Exception:
                pass
        libertar_camera()

    def logout(self):
        if not confirmar(self, "Terminar sessão", "Tem a certeza de que pretende terminar a sessão?",
                         texto_botao="Terminar sessão"):
            return
        terminar_sessao()
        self.reabrir_login = True
        self._parar_tudo()
        self.destroy()

    def _fechar_aplicacao(self):
        self.reabrir_login = False
        terminar_sessao()
        self._parar_tudo()
        self.destroy()


if __name__ == "__main__":
    from interface_grafica.main import main

    main()
