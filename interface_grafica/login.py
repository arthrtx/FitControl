import customtkinter as ctk
from tkinter import messagebox

from modulos.autenticacao import autenticar, e_admin_temporario, admin_temporario_ativo
from interface_grafica.constants import TEMA, alternar_tema, modo_tema
from interface_grafica.termos import TERMOS_TEXTO
from interface_grafica.widgets import btn_primary, btn_secondary, styled_entry, SurfaceCard

LARGURA_PADRAO = 460
ALTURA_MINIMA = 540
ALTURA_CAIXA_TERMOS = 160
ALTURA_CAIXA_MINIMA = 70
TEXTO_AVISO_TERMOS = "⚠ Aceite os Termos de Utilização para poder entrar."


class LoginWindow(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.utilizador_autenticado = None
        self._contador_job = None
        self._bloqueado = False
        self._termos_abertos = False
        self._termos_aceites = False
        self._termos_necessarios = admin_temporario_ativo()
        self._aviso_termos = False
        self._altura_caixa = ALTURA_CAIXA_TERMOS

        ctk.set_appearance_mode(modo_tema())
        ctk.set_default_color_theme("blue")

        self.title("FitControl — Login")
        self.geometry(f"{LARGURA_PADRAO}x660")
        self.minsize(400, ALTURA_MINIMA)
        self.configure(fg_color=TEMA["bg"])

        self._construir()

    def _texto_tema(self):
        if modo_tema() == "dark":
            return "☀️  Modo claro"
        return "🌙  Modo escuro"

    def _alternar_tema(self):
        if self._contador_job:
            try:
                self.after_cancel(self._contador_job)
            except Exception:
                pass
            self._contador_job = None
        self._bloqueado = False

        self.focus_set()
        alternar_tema()
        self.configure(fg_color=TEMA["bg"])
        for filho in self.winfo_children():
            filho.destroy()
        self._construir()

    def _atualizar_entrar(self):
        if not hasattr(self, "btn_login"):
            return
        if self._bloqueado:
            self.btn_login.configure(
                state="disabled",
                fg_color=TEMA["surface_alt"],
                hover_color=TEMA["surface_alt"],
            )
        else:
            self.btn_login.configure(
                state="normal",
                fg_color=TEMA["accent"],
                hover_color=TEMA["accent_hover"],
            )

    def _mostrar_aviso_termos(self):
        self._aviso_termos = True
        if not hasattr(self, "lbl_aviso"):
            return
        self.lbl_aviso.configure(text=TEXTO_AVISO_TERMOS)
        if not self.lbl_aviso.winfo_ismapped():
            self.lbl_aviso.pack(fill="x", pady=(6, 0))
        self._ajustar_altura()

    def _limpar_aviso_termos(self):
        self._aviso_termos = False
        if not hasattr(self, "lbl_aviso"):
            return
        if self.lbl_aviso.winfo_exists() and self.lbl_aviso.winfo_ismapped():
            self.lbl_aviso.configure(text="")
            self.lbl_aviso.pack_forget()
            self._ajustar_altura()

    def _alternar_aceite(self):
        self._termos_aceites = bool(self.chk_termos.get())
        if self._termos_aceites:
            self._limpar_aviso_termos()
        self._atualizar_entrar()

    def _alternar_termos(self):
        if not self._termos_necessarios:
            return
        self._termos_abertos = not self._termos_abertos
        if self._termos_abertos:
            self._altura_caixa = ALTURA_CAIXA_TERMOS
            self.caixa_termos.configure(height=self._altura_caixa)
            self.caixa_termos.grid(
                row=1, column=0, sticky="ew", pady=(8, 0)
            )
            self.btn_termos.configure(text="Ocultar termos  ▲")
        else:
            self.caixa_termos.grid_remove()
            self.btn_termos.configure(text="Ver termos  ▼")
        self._ajustar_altura()

    def _ajustar_altura(self):
        self.update_idletasks()
        limite = max(self.winfo_screenheight() - 100, ALTURA_MINIMA)

        if (
            self._termos_abertos
            and hasattr(self, "caixa_termos")
            and self.winfo_reqheight() > limite
        ):
            excedente = self.winfo_reqheight() - limite
            nova = max(ALTURA_CAIXA_MINIMA, self._altura_caixa - excedente - 8)
            if nova < self._altura_caixa:
                self._altura_caixa = nova
                self.caixa_termos.configure(height=nova)
                self.update_idletasks()

        altura = min(max(self.winfo_reqheight(), ALTURA_MINIMA), limite)
        largura = LARGURA_PADRAO
        if self.winfo_ismapped() and self.winfo_width() >= 100:
            largura = self.winfo_width()
        self.geometry(f"{largura}x{altura}")
        self.minsize(400, altura)

    def _construir(self):
        self._frame_acordos = None
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=18, pady=(14, 0))
        topo.grid_columnconfigure(0, weight=1)

        btn_tema = btn_secondary(
            topo,
            text=self._texto_tema(),
            width=150,
            height=30,
            font=ctk.CTkFont(size=12),
            command=self._alternar_tema,
        )
        btn_tema.grid(row=0, column=0)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill="both", padx=32, pady=(12, 24))

        card = SurfaceCard(container)
        card.pack(expand=True, fill="both")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(expand=True, fill="both", padx=36, pady=28)

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
        self.user = styled_entry(
            inner, placeholder_text="Introduza o utilizador"
        )
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

        if self._termos_necessarios:
            frame_acordos = ctk.CTkFrame(inner, fg_color="transparent")
            frame_acordos.pack(fill="x", pady=(14, 0))
            frame_acordos.grid_columnconfigure(0, weight=1)
            self._frame_acordos = frame_acordos

            linha_termos = ctk.CTkFrame(frame_acordos, fg_color="transparent")
            linha_termos.grid(row=0, column=0, sticky="ew")
            linha_termos.grid_columnconfigure(0, weight=1)

            self.chk_termos = ctk.CTkCheckBox(
                linha_termos,
                text="Li e concordo com os Termos",
                checkbox_width=17,
                checkbox_height=17,
                corner_radius=4,
                border_width=2,
                fg_color=TEMA["accent"],
                hover_color=TEMA["accent_hover"],
                text_color=TEMA["text"],
                font=ctk.CTkFont(size=12),
                command=self._alternar_aceite,
            )
            self.chk_termos.grid(row=0, column=0, sticky="w")
            if self._termos_aceites:
                self.chk_termos.select()
            else:
                self.chk_termos.deselect()

            self.btn_termos = ctk.CTkButton(
                linha_termos,
                text="Ver termos  ▼",
                width=88,
                height=22,
                corner_radius=TEMA["radius_sm"],
                fg_color="transparent",
                hover_color=TEMA["surface_alt"],
                text_color=TEMA["accent"],
                font=ctk.CTkFont(size=11),
                command=self._alternar_termos,
            )
            self.btn_termos.grid(row=0, column=1, sticky="e", padx=(8, 0))

            self.caixa_termos = ctk.CTkTextbox(
                frame_acordos,
                height=self._altura_caixa,
                corner_radius=TEMA["radius_sm"],
                border_width=1,
                border_color=TEMA["border"],
                fg_color=TEMA["input_bg"],
                text_color=TEMA["on_surface"],
                font=ctk.CTkFont(size=11),
                wrap="word",
            )
            self.caixa_termos.insert("1.0", TERMOS_TEXTO)
            self.caixa_termos.configure(state="disabled")

            if self._termos_abertos:
                self.caixa_termos.grid(
                    row=1, column=0, sticky="ew", pady=(8, 0)
                )
                self.btn_termos.configure(text="Ocultar termos  ▲")
            else:
                self.caixa_termos.grid_remove()

            self.lbl_aviso = ctk.CTkLabel(
                inner,
                text="",
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=11),
                text_color=TEMA["danger"],
            )

        self.btn_login = btn_primary(
            inner,
            text="Entrar",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color_disabled=TEMA["muted"],
            command=self.login,
        )
        self.btn_login.pack(fill="x", pady=(16, 0))

        if (
            self._termos_necessarios
            and hasattr(self, "lbl_aviso")
            and self._aviso_termos
        ):
            self.lbl_aviso.configure(text=TEXTO_AVISO_TERMOS)
            self.lbl_aviso.pack(fill="x", pady=(6, 0))

        self.senha.bind("<Return>", lambda _e: self.login())
        self.user.bind("<Return>", lambda _e: self.senha.focus())

        self._atualizar_entrar()
        self._ajustar_altura()

    def _mostrar_bloqueio(self, texto):
        self.lbl_bloqueio.configure(text=texto)
        if not self.lbl_bloqueio.winfo_ismapped():
            ancora = getattr(self, "_frame_acordos", None)
            if ancora is None:
                ancora = self.btn_login
            self.lbl_bloqueio.pack(pady=(4, 0), before=ancora)

    def _esconder_bloqueio(self):
        if self.lbl_bloqueio.winfo_ismapped():
            self.lbl_bloqueio.configure(text="")
            self.lbl_bloqueio.pack_forget()

    def contador(self, segundos):
        if not self.winfo_exists():
            self._contador_job = None
            return

        if segundos <= 0:
            self._esconder_bloqueio()
            self._bloqueado = False
            self._atualizar_entrar()
            self.user.configure(state="normal")
            self.senha.configure(state="normal")
            self._contador_job = None
            return

        self._mostrar_bloqueio(f"🔒 Login bloqueado ({segundos}s)")
        if self._contador_job:
            try:
                self.after_cancel(self._contador_job)
            except Exception:
                pass
        self._contador_job = self.after(1000, lambda: self.contador(segundos - 1))

    def login(self):
        if self._termos_necessarios and not self._termos_aceites:
            self._mostrar_aviso_termos()
            if hasattr(self, "chk_termos"):
                self.chk_termos.focus()
            return

        ok, mensagem, utilizador = autenticar(self.user.get(), self.senha.get())

        if not ok:
            if mensagem == "BLOQUEADO":
                self._bloqueado = True
                self._atualizar_entrar()
                self.user.configure(state="disabled")
                self.senha.configure(state="disabled")
                self.contador(utilizador)
            else:
                messagebox.showerror("Erro", mensagem)
            return

        if e_admin_temporario(utilizador):
            messagebox.showwarning(
                "Administrador Temporário",
                "Está a usar o administrador temporário\n"
                "(usuário: adm / palavra-passe: adm).\n\n"
                "Por segurança, ALTERE OS DADOS desta conta "
                "temporária (menu Funcionários) ou CRIE OUTRA "
                "conta de administrador definitiva e elimine a "
                "conta temporária o quanto antes."
            )

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
