import customtkinter as ctk
from tkinter import messagebox

from modulos.autenticacao import autenticar
class LoginWindow(ctk.CTk):

    def __init__(self):

        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Login")

        self.geometry("430x500")

        self.resizable(False, False)
 
        frame = ctk.CTkFrame(
            self,
            corner_radius=15
        )

        frame.pack(
            expand=True,
            padx=30,
            pady=30,
            fill="both"
        )

        ctk.CTkLabel(

            frame,

            text="💪",

            font=ctk.CTkFont(size=60)

        ).pack(
            anchor="center",
            pady=(25, 10)
        )

        ctk.CTkLabel(

            frame,

            text="FitControl",

            font=ctk.CTkFont(
                size=24,
                weight="bold"
            )

        ).pack()

        self.user = ctk.CTkEntry(

            frame,

            placeholder_text="usuario",

            width=280

        )

        self.user.pack(
            pady=(35,10)
        )

        self.senha = ctk.CTkEntry(

            frame,

            placeholder_text="senha",

            show="*",

            width=280

        )

        self.senha.pack(
            pady=10
        )

        ctk.CTkButton(

            frame,

            text="Entrar",

            width=280,

            height=40,

            command=self.login

        ).pack(
            pady=30
        )

    def login(self):

        ok, mensagem, utilizador = autenticar(

            self.user.get(),

            self.senha.get()

        )

        if not ok:

            messagebox.showerror(

                "Erro",

                mensagem

            )

            return

        self.destroy()

        from interface_grafica.app import AcademiaApp

        app = AcademiaApp(utilizador)

        app.mainloop()

