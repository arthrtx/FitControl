"""Diálogos modais da interface gráfica."""

from tkinter import messagebox

import customtkinter as ctk

from interface_grafica.constants import PLANOS, TEMA
from interface_grafica.widgets import (
    btn_danger,
    btn_primary,
    btn_secondary,
    centre_toplevel,
    styled_entry,
    styled_option,
    SurfaceCard,
)


class _FormDialogBase(ctk.CTkToplevel):
    def _setup_window(self, master, titulo, largura, altura):
        self.title(titulo)
        self.geometry(f"{largura}x{altura}")
        self.resizable(False, False)
        self.configure(fg_color=TEMA["bg"])
        self.grab_set()
        self.focus_force()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        card = SurfaceCard(self)
        card.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        card.grid_columnconfigure(1, weight=1)
        return card

    def _campo(self, card, linha, rotulo, widget):
        ctk.CTkLabel(
            card,
            text=rotulo,
            font=ctk.CTkFont(size=13),
            text_color=TEMA["muted"],
        ).grid(row=linha, column=0, padx=(16, 10), pady=10, sticky="e")
        widget.grid(row=linha, column=1, padx=(0, 16), pady=10, sticky="ew")

    def _botoes(self, card, linha, guardar_cmd):
        barra = ctk.CTkFrame(card, fg_color="transparent")
        barra.grid(row=linha, column=0, columnspan=2, pady=(8, 16))
        btn_primary(barra, text="Guardar", width=120, command=guardar_cmd).pack(
            side="left", padx=6
        )
        btn_secondary(barra, text="Cancelar", width=120, command=self.destroy).pack(
            side="left", padx=6
        )


class AlunoFormDialog(_FormDialogBase):
    """Janela modal para criar ou editar um aluno."""

    def __init__(self, master, titulo, callback, aluno=None):
        super().__init__(master)
        self.callback = callback
        self.aluno = aluno

        card = self._setup_window(master, titulo, 500, 460)

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEMA["text"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 8))

        self.entries = {}
        for i, (rotulo, chave) in enumerate(
            [("Nome", "nome"), ("Telemóvel", "telemovel"), ("Documento", "documento")], start=1
        ):
            entry = styled_entry(card)
            self._campo(card, i, rotulo, entry)
            self.entries[chave] = entry

        self.plano_var = ctk.StringVar(value=PLANOS[1])
        self.plano_menu = styled_option(card, values=PLANOS, variable=self.plano_var)
        self._campo(card, 4, "Plano", self.plano_menu)

        if aluno:
            self.entries["nome"].insert(0, aluno["nome"])
            self.entries["telemovel"].insert(0, aluno["telemovel"])
            self.entries["documento"].insert(0, aluno["documento"])
            self.plano_var.set(aluno["plano"])
            aviso = "A foto não será alterada na edição."
        else:
            aviso = "Ao guardar, a câmara abrirá para tirar a fotografia."

        ctk.CTkLabel(
            card,
            text=aviso,
            text_color=TEMA["muted"],
            font=ctk.CTkFont(size=11),
        ).grid(row=5, column=0, columnspan=2, padx=16, pady=(0, 4))

        self._botoes(card, 6, self._guardar)
        centre_toplevel(self, master)

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


class FuncionarioFormDialog(_FormDialogBase):
    """Janela para criar ou editar funcionários."""

    def __init__(self, master, callback, funcionario=None):
        super().__init__(master)
        self.callback = callback
        self.funcionario = funcionario

        titulo = "Editar Funcionário" if funcionario else "Novo Funcionário"
        card = self._setup_window(master, titulo, 500, 420)

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEMA["text"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 8))

        self.entries = {}
        for i, (rotulo, chave) in enumerate(
            [("Nome", "nome"), ("Utilizador", "usuario"), ("Palavra-passe", "senha")], start=1
        ):
            entry = styled_entry(card)
            self._campo(card, i, rotulo, entry)
            self.entries[chave] = entry

        self.tipo_var = ctk.StringVar(value="Funcionario")
        self.tipo_menu = styled_option(
            card,
            values=["Funcionario", "Administrador"],
            variable=self.tipo_var,
        )
        self._campo(card, 4, "Cargo", self.tipo_menu)

        if funcionario:
            self.entries["nome"].insert(0, funcionario["nome"])
            self.entries["usuario"].insert(0, funcionario["usuario"])
            self.entries["senha"].insert(0, funcionario["senha"])
            self.tipo_var.set(funcionario["tipo"])

        self._botoes(card, 5, self._guardar)
        centre_toplevel(self, master)

    def _guardar(self):
        nome = self.entries["nome"].get().strip()
        usuario = self.entries["usuario"].get().strip()
        senha = self.entries["senha"].get().strip()
        tipo = self.tipo_var.get()

        if not nome or not usuario or not senha:
            messagebox.showwarning("Campos obrigatórios", "Preencha todos os campos.")
            return

        self.callback(nome, usuario, senha, tipo)
        self.destroy()
