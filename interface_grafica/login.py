import customtkinter as ctk
from tkinter import messagebox

from modulos.autenticacao import autenticar
from interface_grafica.constants import TEMA
from interface_grafica.widgets import btn_primary, styled_entry, SurfaceCard


class LoginWindow(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.utilizador_autenticado = None
        self._contador_job = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("FitControl — Login")
        self.geometry("460x560")
        self.minsize(400, 520)
        self.configure(fg_color=TEMA["bg"])

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill="both", padx=32, pady=32)

        card = SurfaceCard(container)
        card.pack(expand=True, fill="both")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(expand=True, fill="both", padx=36, pady=36)

        ctk.CTkLabel(
            inner,
            text="🏋️",
            font=ctk.CTkFont(size=52),
        ).pack(pady=(8, 4))

        ctk.CTkLabel(
            inner,
            text="FitControl",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEMA["text"],
        ).pack()

        ctk.CTkLabel(
            inner,
            text="Sistema de Gestão de Academia",
            font=ctk.CTkFont(size=12),
            text_color=TEMA["muted"],
        ).pack(pady=(4, 28))

        ctk.CTkLabel(
            inner,
            text="Utilizador",
            font=ctk.CTkFont(size=12),
            text_color=TEMA["muted"],
            anchor="w",
        ).pack(fill="x")
        self.user = styled_entry(inner, placeholder_text="Introduza o utilizador")
        self.user.pack(fill="x", pady=(4, 14))

        ctk.CTkLabel(
            inner,
            text="Palavra-passe",
            font=ctk.CTkFont(size=12),
            text_color=TEMA["muted"],
            anchor="w",
        ).pack(fill="x")
        self.senha = styled_entry(inner, placeholder_text="Introduza a palavra-passe", show="*")
        self.senha.pack(fill="x", pady=(4, 8))

        self.lbl_bloqueio = ctk.CTkLabel(
            inner,
            text="",
            text_color=TEMA["danger"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.lbl_bloqueio.pack(pady=(4, 0))

        self.btn_login = btn_primary(
            inner,
            text="Entrar",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.login,
        )
        self.btn_login.pack(fill="x", pady=(24, 0))

        self.senha.bind("<Return>", lambda _e: self.login())
        self.user.bind("<Return>", lambda _e: self.senha.focus())

    def contador(self, segundos):
        if not self.winfo_exists():
            self._contador_job = None
            return

        if segundos <= 0:
            self.lbl_bloqueio.configure(text="")
            self.btn_login.configure(state="normal")
            self.user.configure(state="normal")
            self.senha.configure(state="normal")
            self._contador_job = None
            return

        self.lbl_bloqueio.configure(text=f"🔒 Login bloqueado ({segundos}s)")
        if self._contador_job:
            try:
                self.after_cancel(self._contador_job)
            except Exception:
                pass
        self._contador_job = self.after(1000, lambda: self.contador(segundos - 1))

    def login(self):
        ok, mensagem, utilizador = autenticar(self.user.get(), self.senha.get())

        if not ok:
            if mensagem == "BLOQUEADO":
                self.btn_login.configure(state="disabled")
                self.user.configure(state="disabled")
                self.senha.configure(state="disabled")
                self.contador(utilizador)
            else:
                messagebox.showerror("Erro", mensagem)
            return

        self.utilizador_autenticado = utilizador
        self.destroy()

    def destroy(self):
        if self._contador_job:
            try:
                self.after_cancel(self._contador_job)
            except Exception:
                pass
            finally:
                self._contador_job = None
        super().destroy()
