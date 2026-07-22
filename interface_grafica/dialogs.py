"""Diálogos modais da interface gráfica."""

from tkinter import messagebox

import customtkinter as ctk

from interface_grafica.constants import PLANOS


class AlunoFormDialog(ctk.CTkToplevel):
    """Janela modal para criar ou editar um aluno."""

    def __init__(self, master, titulo, callback, aluno=None):
        super().__init__(master)
        self.callback = callback
        self.aluno = aluno

        self.title(titulo)
        self.geometry("480x420")
        self.resizable(False, False)
        self.grab_set()
        self.focus_force()

        self.grid_columnconfigure(1, weight=1)

        campos = [
            ("Nome", "nome"),
            ("Telemóvel", "telemovel"),
            ("Documento", "documento"),
        ]
        self.entries = {}

        for i, (label, chave) in enumerate(campos):
            ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=14)).grid(
                row=i, column=0, padx=(20, 10), pady=12, sticky="e"
            )
            entry = ctk.CTkEntry(self, width=280, height=36)
            entry.grid(row=i, column=1, padx=(0, 20), pady=12, sticky="ew")
            self.entries[chave] = entry

        ctk.CTkLabel(self, text="Plano", font=ctk.CTkFont(size=14)).grid(
            row=3, column=0, padx=(20, 10), pady=12, sticky="e"
        )
        self.plano_var = ctk.StringVar(value=PLANOS[1])
        self.plano_menu = ctk.CTkOptionMenu(
            self, values=PLANOS, variable=self.plano_var, width=280, height=36
        )
        self.plano_menu.grid(row=3, column=1, padx=(0, 20), pady=12, sticky="ew")

        if aluno:
            self.entries["nome"].insert(0, aluno["nome"])
            self.entries["telemovel"].insert(0, aluno["telemovel"])
            self.entries["documento"].insert(0, aluno["documento"])
            self.plano_var.set(aluno["plano"])
            ctk.CTkLabel(
                self,
                text="(A foto não será alterada na edição)",
                text_color="gray",
                font=ctk.CTkFont(size=12),
            ).grid(row=4, column=0, columnspan=2, pady=(0, 5))
        else:
            ctk.CTkLabel(
                self,
                text="Ao guardar, a câmara abrirá para tirar a fotografia.",
                text_color="gray",
                font=ctk.CTkFont(size=12),
            ).grid(row=4, column=0, columnspan=2, pady=(0, 5))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ctk.CTkButton(
            btn_frame, text="Guardar", width=120, command=self._guardar
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            width=120,
            fg_color="gray",
            hover_color="#555",
            command=self.destroy,
        ).pack(side="left", padx=8)

        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_y() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _guardar(self):
        nome = self.entries["nome"].get().strip()
        telemovel = self.entries["telemovel"].get().strip()
        documento = self.entries["documento"].get().strip()
        plano = self.plano_var.get()

        if not nome or not telemovel or not documento:
            messagebox.showwarning("Campos obrigatórios", "Preencha todos os campos.")
            return

        self.callback(nome, telemovel, documento, plano)
        self.destroy()

class FuncionarioFormDialog(ctk.CTkToplevel):
    """Janela para criar funcionários."""

    def __init__(self, master, callback, funcionario=None):
        self.funcionario = funcionario
        super().__init__(master)

        self.callback = callback

        if funcionario:
            self.title("Editar Funcionário")
        else:
            self.title("Novo Funcionário")

        self.geometry("480x380")
        self.resizable(False, False)

        self.grab_set()
        self.focus_force()

        self.grid_columnconfigure(1, weight=1)

        campos = [
            ("Nome", "nome"),
            ("Utilizador", "usuario"),
            ("Palavra-passe", "senha"),
        ]

        self.entries = {}

        for i, (label, chave) in enumerate(campos):

            ctk.CTkLabel(
                self,
                text=label,
                font=ctk.CTkFont(size=14)
            ).grid(
                row=i,
                column=0,
                padx=(20,10),
                pady=12,
                sticky="e"
            )

            entry = ctk.CTkEntry(
                self,
                width=280,
                height=36
            )

            entry.grid(
                row=i,
                column=1,
                padx=(0,20),
                pady=12,
                sticky="ew"
            )

            self.entries[chave] = entry

        ctk.CTkLabel(
            self,
            text="Cargo",
            font=ctk.CTkFont(size=14)
        ).grid(
            row=3,
            column=0,
            padx=(20,10),
            pady=12,
            sticky="e"
        )

        self.tipo_var = ctk.StringVar(value="Funcionario")

        self.tipo_menu = ctk.CTkOptionMenu(
            self,
            values=[
                "Funcionario",
                "Administrador"
            ],
            variable=self.tipo_var,
            width=280,
            height=36
        )

        self.tipo_menu.grid(
            row=3,
            column=1,
            padx=(0,20),
            pady=12,
            sticky="ew"
        )
        if funcionario:
            self.entries["nome"].insert(
                0,
                funcionario["nome"]
            )

            self.entries["usuario"].insert(
                0,
                funcionario["usuario"]
            )

            self.entries["senha"].insert(
                0,
                funcionario["senha"]
            )

            self.tipo_var.set(
                funcionario["tipo"]
            )

        btn_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        btn_frame.grid(
            row=4,
            column=0,
            columnspan=2,
            pady=20
        )

        ctk.CTkButton(
            btn_frame,
            text="Guardar",
            width=120,
            command=self._guardar
        ).pack(
            side="left",
            padx=8
        )

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            width=120,
            fg_color="gray",
            hover_color="#555",
            command=self.destroy
        ).pack(
            side="left",
            padx=8
        )

        self.update_idletasks()

        x = master.winfo_x() + (
            master.winfo_width() - self.winfo_width()
        ) // 2

        y = master.winfo_y() + (
            master.winfo_height() - self.winfo_height()
        ) // 2

        self.geometry(f"+{x}+{y}")

    def _guardar(self):

        nome = self.entries["nome"].get().strip()
        usuario = self.entries["usuario"].get().strip()
        senha = self.entries["senha"].get().strip()
        tipo = self.tipo_var.get()

        if not nome or not usuario or not senha:

            messagebox.showwarning(
                "Campos obrigatórios",
                "Preencha todos os campos."
            )

            return

        self.callback(
            nome,
            usuario,
            senha,
            tipo
        )

        self.destroy()