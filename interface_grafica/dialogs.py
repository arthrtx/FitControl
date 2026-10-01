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
from modulos import notificacoes
from modulos import relatorios


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

        card = self._setup_window(master, titulo, 550, 550)

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEMA["text"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 8))

        # Regras de validação colocadas dentro de cada campo (placeholder com
        # opacidade baixa, que desaparece assim que o utilizador escreve).
        placeholders = {
            "nome": "Mínimo 2 palavras (nome e apelido)",
            "telemovel": "9 dígitos (ex.: 912345678)",
            "documento": "Máximo 12 caracteres",
        }
        self.entries = {}
        for i, (rotulo, chave) in enumerate(
            [("Nome", "nome"), ("Telemóvel", "telemovel"), ("Documento", "documento")], start=1
        ):
            entry = styled_entry(
                card,
                placeholder_text=placeholders.get(chave, ""),
                placeholder_text_color=TEMA["muted"],
            )
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
            aviso = "Por omissão mantém-se a foto atual. Marque a opção abaixo para a substituir: abre-se uma janela da câmara, pressione P para tirar a foto ou Q para cancelar."
            self.nova_foto_var = ctk.BooleanVar(value=False)
            linha_foto = ctk.CTkFrame(card, fg_color="transparent")
            linha_foto.grid(row=6, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
            linha_foto.grid_columnconfigure(0, weight=1)
            ctk.CTkCheckBox(
                linha_foto,
                text="📷  Tirar nova foto ao guardar",
                variable=self.nova_foto_var,
                font=ctk.CTkFont(size=13),
                text_color=TEMA["text"],
                fg_color=TEMA["accent"],
                hover_color=TEMA["accent_hover"],
            ).grid(row=0, column=0)
            linha_botoes = 7
        else:
            aviso = "Ao guardar, abre-se uma janela da câmara: centre o rosto e pressione P para tirar a foto (ou Q para cancelar)."
            linha_botoes = 6

        ctk.CTkLabel(
            card,
            text=aviso,
            text_color=TEMA["muted"],
            font=ctk.CTkFont(size=11),
            wraplength=490,
            justify="left",
        ).grid(row=5, column=0, columnspan=2, padx=16, pady=(0, 4))

        self._botoes(card, linha_botoes, self._guardar)
        centre_toplevel(self, master)

    def _guardar(self):
        nome = self.entries["nome"].get().strip()
        telemovel = self.entries["telemovel"].get().strip()
        documento = self.entries["documento"].get().strip()
        plano = self.plano_var.get()

        # Validação do nome
        if not nome:
            messagebox.showwarning("Nome inválido", "O nome não pode estar vazio.")
            return
        if len(nome.split()) < 2:
            messagebox.showwarning("Nome inválido", "O nome deve conter pelo menos 2 palavras (nome e sobrenome).")
            return

        # Validação do telemóvel
        if not telemovel:
            messagebox.showwarning("Telemóvel inválido", "O telemóvel não pode estar vazio.")
            return
        if not telemovel.isdigit():
            messagebox.showwarning("Telemóvel inválido", "O telemóvel deve conter apenas dígitos numéricos.")
            return
        if len(telemovel) != 9:
            messagebox.showwarning("Telemóvel inválido", "O telemóvel deve ter exatamente 9 dígitos.")
            return

        # Validação do documento
        if not documento:
            messagebox.showwarning("Documento inválido", "O documento não pode estar vazio.")
            return
        if len(documento) > 12:
            messagebox.showwarning("Documento inválido", "O documento não pode ter mais de 12 caracteres.")
            return

        # Validação do plano
        planos_validos = ["Diário", "Mensal", "Trimestral", "Anual"]
        if plano not in planos_validos:
            messagebox.showwarning("Plano inválido", f"O plano deve ser um dos seguintes: {', '.join(planos_validos)}.")
            return

        self.callback(
            nome,
            telemovel,
            documento,
            plano,
            self.nova_foto_var.get() if hasattr(self, "nova_foto_var") else False,
        )
        self.destroy()


class FuncionarioFormDialog(_FormDialogBase):
    """Janela para criar ou editar funcionários."""

    def __init__(self, master, callback, funcionario=None):
        super().__init__(master)
        self.callback = callback
        self.funcionario = funcionario

        titulo = "Editar Funcionário" if funcionario else "Novo Funcionário"
        card = self._setup_window(master, titulo, 500, 384)

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEMA["text"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 8))

        self.entries = {}
        for i, (rotulo, chave) in enumerate(
            [
                ("Nome", "nome"),
                ("Utilizador", "usuario"),
                ("Palavra-passe", "senha"),
            ],
            start=1,
        ):
            entry = styled_entry(
                card,
                placeholder_text="",
                placeholder_text_color=TEMA["muted"],
            )
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


class NotificacoesDialog(ctk.CTkToplevel):
    def __init__(self, master, ao_fechar=None):
        super().__init__(master)
        self.ao_fechar = ao_fechar

        self.title("Notificações")
        self.geometry("560x480")
        self.resizable(False, False)
        self.configure(fg_color=TEMA["bg"])
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._fechar)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        topo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            topo,
            text="Notificações",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEMA["text"],
        ).grid(row=0, column=0, sticky="w")

        self.lbl_total = ctk.CTkLabel(
            topo,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=TEMA["muted"],
        )
        self.lbl_total.grid(row=1, column=0, sticky="w", pady=(2, 0))

        btn_secondary(
            topo,
            text="Marcar todas",
            width=130,
            height=30,
            font=ctk.CTkFont(size=12),
            command=self._marcar_todas,
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

        self.lista = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lista.grid(row=1, column=0, sticky="nsew", padx=20)
        self.lista.grid_columnconfigure(0, weight=1)

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        btn_secondary(
            barra, text="Limpar lidas", width=130, command=self._limpar_lidas
        ).pack(side="left")
        btn_primary(barra, text="Fechar", width=130, command=self._fechar).pack(
            side="right"
        )

        self._renderizar()
        centre_toplevel(self, master)

    def _renderizar(self):
        for filho in self.lista.winfo_children():
            filho.destroy()

        registos = notificacoes.listar()
        pendentes = notificacoes.por_ler()

        if pendentes:
            self.lbl_total.configure(text=f"{pendentes} por ler")
        else:
            self.lbl_total.configure(text="Não há nada por ler.")

        if not registos:
            ctk.CTkLabel(
                self.lista,
                text="Sem notificações de momento.",
                font=ctk.CTkFont(size=13),
                text_color=TEMA["muted"],
            ).grid(row=0, column=0, pady=28)
            return

        for indice, registo in enumerate(registos):
            self._linha(registo).grid(
                row=indice, column=0, sticky="ew", pady=(0, 6)
            )

    def _linha(self, registo):
        lida = bool(registo["lida"])
        cor_ponto = TEMA["danger"] if not lida else TEMA["muted"]
        cor_borda = TEMA["danger"] if not lida else TEMA["border"]

        linha = ctk.CTkFrame(
            self.lista,
            fg_color=TEMA["surface"] if not lida else TEMA["surface_alt"],
            corner_radius=TEMA["radius_sm"],
            border_width=1,
            border_color=cor_borda,
        )
        linha.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            linha,
            text="●",
            font=ctk.CTkFont(size=13),
            text_color=cor_ponto,
            width=16,
        ).grid(row=0, column=0, rowspan=2, padx=(12, 4), pady=12, sticky="n")

        ctk.CTkLabel(
            linha,
            text=registo["titulo"],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEMA["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(11, 0))

        ctk.CTkLabel(
            linha,
            text=registo["mensagem"],
            font=ctk.CTkFont(size=12),
            text_color=TEMA["muted"],
            anchor="w",
            justify="left",
            wraplength=340,
        ).grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(2, 11))

        ctk.CTkLabel(
            linha,
            text=registo["data"],
            font=ctk.CTkFont(size=10),
            text_color=TEMA["muted"],
        ).grid(row=0, column=2, rowspan=2, padx=(0, 12), sticky="e")

        if not lida:
            for filho in [linha] + list(linha.winfo_children()):
                filho.bind(
                    "<Button-1>",
                    lambda _evento, r=registo: self._marcar_lida(r),
                )

        return linha

    def _marcar_lida(self, registo):
        notificacoes.marcar_lida(registo["id"])
        self._renderizar()

    def _marcar_todas(self):
        notificacoes.marcar_todas_lidas()
        self._renderizar()

    def _limpar_lidas(self):
        notificacoes.limpar_lidas()
        self._renderizar()

    def _fechar(self):
        if self.ao_fechar:
            self.ao_fechar()
        self.destroy()


class RelatorioDialog(ctk.CTkToplevel):
    def __init__(self, master, ao_gerar):
        super().__init__(master)
        self.ao_gerar = ao_gerar
        self.opcoes = relatorios.meses_disponiveis()

        self.title("Relatório PDF")
        self.geometry("420x250")
        self.resizable(False, False)
        self.configure(fg_color=TEMA["bg"])
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        card = SurfaceCard(self)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Relatório PDF",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEMA["text"],
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 2))

        ctk.CTkLabel(
            card,
            text="O relatório junta os pagamentos do mês, as mensalidades em atraso e os alunos sem pagamento.",
            font=ctk.CTkFont(size=12),
            text_color=TEMA["muted"],
            wraplength=360,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

        self.mes_var = ctk.StringVar(value=self.opcoes[0]["rotulo"])
        styled_option(
            card,
            values=[opcao["rotulo"] for opcao in self.opcoes],
            variable=self.mes_var,
        ).grid(row=2, column=0, sticky="ew", padx=16)

        barra = ctk.CTkFrame(card, fg_color="transparent")
        barra.grid(row=3, column=0, sticky="ew", padx=16, pady=(18, 16))
        btn_primary(barra, text="Gerar", width=110, command=self._gerar).pack(
            side="right", padx=6
        )
        btn_secondary(barra, text="Cancelar", width=110, command=self.destroy).pack(
            side="right", padx=6
        )

        centre_toplevel(self, master)

    def _gerar(self):
        rotulo = self.mes_var.get()
        for opcao in self.opcoes:
            if opcao["rotulo"] == rotulo:
                self.ao_gerar(opcao["ano"], opcao["mes"])
                break
        self.destroy()
