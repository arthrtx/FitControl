import tkinter as tk

import customtkinter as ctk
from PIL import ImageTk

from interface_grafica.arte import fluido
from interface_grafica.constants import TEMA, VERSAO, alternar_tema, escuro, modo_tema
from interface_grafica.dialogs import DialogoTermos
from interface_grafica.icones import icone, logo_ctk
from interface_grafica.janela import (
    aplicar_tema_barra, cancelar_pendentes, centralizar, congelar, descongelar, limpar_rastreadores_ctk,
    preparar_janela,
)
from interface_grafica.widgets import AlternadorTema, ativar, botao, campo, fonte, mensagem, rotulo
from modulos import privacidade
from modulos.autenticacao import autenticar, e_admin_temporario


class LoginWindow(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.utilizador_autenticado = None
        self._contador_job = None
        self._arte_job = None
        self._arte = None
        self._senha_visivel = False

        ctk.set_appearance_mode(modo_tema())
        self.title("FitControl")
        centralizar(self, 860, 540)
        self.minsize(760, 500)
        preparar_janela(self)

        self._construir()

    # tema
    # ======================================================
    def _alternar_tema(self):
        utilizador = self.user.get()
        cobertura = congelar(self)
        self._cancelar_contador()
        if self._arte_job:
            try:
                self.after_cancel(self._arte_job)
            except Exception:
                pass
            self._arte_job = None
        for filho in self.winfo_children():
            if filho is not cobertura:
                filho.destroy()
        # deixa o customtkinter sem callbacks dos widgets que acabaram de sair
        limpar_rastreadores_ctk()
        alternar_tema()
        self._construir()
        self.user.insert(0, utilizador)
        aplicar_tema_barra(self)
        descongelar(self, cobertura)

    # construção
    # ======================================================
    def _construir(self):
        self.configure(fg_color=TEMA["bg"])
        self.grid_columnconfigure(0, weight=11, uniform="c")
        self.grid_columnconfigure(1, weight=9, uniform="c")
        self.grid_rowconfigure(0, weight=1)

        # painel da esquerda com a arte
        self.painel = tk.Canvas(self, highlightthickness=0, bd=0, bg=TEMA["bg"])
        self.painel.grid(row=0, column=0, sticky="nsew", padx=(18, 0), pady=18)
        self.painel.bind("<Configure>", self._agendar_arte)

        # formulário
        lado = ctk.CTkFrame(self, fg_color="transparent")
        lado.grid(row=0, column=1, sticky="nsew", padx=30, pady=16)
        lado.grid_columnconfigure(0, weight=1)
        lado.grid_rowconfigure(1, weight=1)

        topo = ctk.CTkFrame(lado, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew")
        AlternadorTema(topo, self._alternar_tema, escuro()).pack(side="right")

        form = ctk.CTkFrame(lado, fg_color="transparent")
        form.grid(row=1, column=0, sticky="ew")
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(form, text="", image=logo_ctk(40, TEMA["accent"], TEMA["violet"])).grid(row=0, column=0, sticky="w")
        rotulo(form, "Bem-vindo de volta", 24, "bold").grid(row=1, column=0, sticky="w", pady=(14, 0))
        rotulo(form, "Inicie sessão para gerir a sua academia.", 13, cor=TEMA["muted"]).grid(
            row=2, column=0, sticky="w", pady=(2, 20))

        rotulo(form, "Utilizador", 12, cor=TEMA["muted"]).grid(row=3, column=0, sticky="w")
        self.user = campo(form, placeholder_text="O seu nome de utilizador", height=42)
        self.user.grid(row=4, column=0, sticky="ew", pady=(5, 14))

        rotulo(form, "Palavra-passe", 12, cor=TEMA["muted"]).grid(row=5, column=0, sticky="w")
        caixa_senha = ctk.CTkFrame(form, fg_color="transparent")
        caixa_senha.grid(row=6, column=0, sticky="ew", pady=(5, 6))
        caixa_senha.grid_columnconfigure(0, weight=1)
        self.senha = campo(caixa_senha, placeholder_text="••••••••", show="•", height=42)
        self.senha.grid(row=0, column=0, sticky="ew")
        self.btn_ver = ctk.CTkButton(caixa_senha, text="", image=icone("olho", TEMA["muted"], 18), width=34,
                                     height=34, fg_color=TEMA["input_bg"], hover_color=TEMA["surface_alt"],
                                     corner_radius=8, command=self._ver_senha)
        self.btn_ver.place(relx=1.0, rely=0.5, x=-8, anchor="e")

        self.lbl_erro = rotulo(form, "", 12, cor=TEMA["danger"], anchor="w", justify="left")
        self.lbl_erro.grid(row=7, column=0, sticky="ew", pady=(2, 8))

        self.btn_login = botao(form, "Entrar", self.login, height=44, font=fonte(14, "bold"))
        self.btn_login.grid(row=8, column=0, sticky="ew")

        rodape = ctk.CTkFrame(form, fg_color="transparent")
        rodape.grid(row=9, column=0, sticky="w", pady=(18, 0))
        rotulo(rodape, "Ao entrar aceita os", 12, cor=TEMA["subtle"]).pack(side="left")
        link = rotulo(rodape, " Termos e a Política de Privacidade", 12, "bold", cor=TEMA["accent"], cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda _e=None: DialogoTermos(self, aceitar=False).esperar())

        rotulo(lado, f"FitControl v{VERSAO}  ·  Dados guardados neste computador", 11,
               cor=TEMA["subtle"]).grid(row=2, column=0, sticky="w")

        self.user.bind("<Return>", lambda _e=None: self.senha.focus())
        self.senha.bind("<Return>", lambda _e=None: self.login())
        self.after(120, self.user.focus_set)

    def _ver_senha(self):
        self._senha_visivel = not self._senha_visivel
        self.senha.configure(show="" if self._senha_visivel else "•")
        self.btn_ver.configure(image=icone("olho_fechado" if self._senha_visivel else "olho", TEMA["muted"], 18))

    # arte do painel
    # ======================================================
    def _agendar_arte(self, _e=None):
        if self._arte_job:
            self.after_cancel(self._arte_job)
        self._arte_job = self.after(80, self._desenhar_arte)

    def _desenhar_arte(self):
        self._arte_job = None
        w, h = self.painel.winfo_width(), self.painel.winfo_height()
        if w < 50 or h < 50:
            return
        if escuro():
            cores = ["#ff3d8b", "#3ee59a", "#8f7cff", "#1f6fff", "#ff7a3d"]
            base, texto, suave = "#0d0d12", "#ffffff", "#d7d7e0"
        else:
            cores = ["#ff9cc6", "#8ef0c3", "#b7a9ff", "#9fd3ff", "#ffd29c"]
            base, texto, suave = "#f6f6f9", "#121217", "#3c3c46"
        self._arte = ImageTk.PhotoImage(fluido(w, h, cores, base, semente=11, raio=28))
        c = self.painel
        c.delete("all")
        c.create_image(0, 0, image=self._arte, anchor="nw")
        c.create_text(32, 36, text="FitControl", anchor="nw", fill=texto, font=("Segoe UI", 16, "bold"))
        c.create_text(32, h - 104, text="Gestão da academia,\nsem complicações.", anchor="sw",
                      fill=texto, font=("Segoe UI", 23, "bold"))
        c.create_text(32, h - 92, anchor="nw", width=w - 64, fill=suave, font=("Segoe UI", 11),
                      text="Alunos, pagamentos, presenças e reconhecimento facial num só lugar.")

    # bloqueio
    # ======================================================
    def _cancelar_contador(self):
        if self._contador_job:
            try:
                self.after_cancel(self._contador_job)
            except Exception:
                pass
            self._contador_job = None

    def contador(self, segundos):
        if not self.winfo_exists():
            return
        if segundos <= 0:
            self.lbl_erro.configure(text="")
            self.btn_login.configure(text="Entrar")
            ativar(self.btn_login, True)
            self.user.configure(state="normal")
            self.senha.configure(state="normal")
            self._contador_job = None
            return
        self.lbl_erro.configure(text="Demasiadas tentativas falhadas.")
        self.btn_login.configure(text=f"Bloqueado ({segundos}s)")
        ativar(self.btn_login, False)
        self._contador_job = self.after(1000, lambda: self.contador(segundos - 1))

    # login
    # ======================================================
    def login(self):
        if str(self.btn_login.cget("state")) == "disabled":
            return

        ok, texto, utilizador = autenticar(self.user.get(), self.senha.get())

        if not ok:
            if texto == "BLOQUEADO":
                self.user.configure(state="disabled")
                self.senha.configure(state="disabled")
                self.contador(utilizador)
            else:
                texto = texto.replace("\n", "  ·  ")
                self.lbl_erro.configure(text=texto[:1].upper() + texto[1:])
                self.senha.delete(0, "end")
                self.senha.focus_set()
            return

        # os termos têm de estar aceites na versão atual
        if not privacidade.termos_aceites(utilizador["usuario"]):
            if not DialogoTermos(self, aceitar=True).esperar():
                privacidade.recusar_termos(utilizador["usuario"])
                self.lbl_erro.configure(text="É preciso aceitar os termos para usar o FitControl.")
                return
            privacidade.aceitar_termos(utilizador["usuario"])

        if e_admin_temporario(utilizador):
            mensagem(
                self, "Conta temporária",
                "Está a usar o administrador temporário (adm / adm).\n\n"
                "Por segurança, altere já os dados desta conta no menu Funcionários "
                "ou crie outra conta de administrador e elimine esta.",
                "aviso",
            )

        self.utilizador_autenticado = utilizador
        self.destroy()

    def destroy(self):
        self._cancelar_contador()
        if self._arte_job:
            self.after_cancel(self._arte_job)
        cancelar_pendentes(self)
        super().destroy()
