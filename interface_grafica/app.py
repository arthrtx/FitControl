"""
Janela principal da interface gráfica — Sistema de Gestão de Academia.
"""
print("APP INICIOU")
import threading
from tkinter import messagebox, ttk

import customtkinter as ctk

from interface_grafica.constants import CORES
from interface_grafica.dialogs import AlunoFormDialog, FuncionarioFormDialog
from interface_grafica.utils import aluno_por_id, nome_aluno, setup_paths

setup_paths()

from projeto_ginasio.main import inicializar
from projeto_ginasio.Camara import gravarVideo, ligarCam
from modulos import( estatistica, gestao_alunos, pagamentos, presencas, funcionarios as gestao_funcionarios)


class AcademiaApp(ctk.CTk):
    """Janela principal da aplicação."""

    def __init__(self, utilizador):
        self.utilizador = utilizador
        self.admin = self.utilizador["tipo"] == "Administrador"
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Gestão de Academia")
        self.geometry("1100x700")
        self.minsize(900, 600)

        inicializar()

        self._pagina_atual = None
        self._botoes_nav = {}

        self._criar_layout()
        self._configurar_treeview()
        self._mostrar_pagina("dashboard")

    def _criar_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=CORES["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        ctk.CTkLabel(
            self.sidebar,
            text="🏋️ Academia",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(25, 10), sticky="w")

        ctk.CTkLabel(
            self.sidebar,
            text=self.utilizador["nome"],
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=1, column=0, padx=20, sticky="w")

        ctk.CTkLabel(
            self.sidebar,
            text=self.utilizador["tipo"],
            text_color="gray",
            font=ctk.CTkFont(size=12),
        ).grid(row=2, column=0, padx=20, pady=(0, 20), sticky="w")
       
        nav_items = [
            ("dashboard", "📊 Dashboard"),
            ("alunos", "👥 Alunos"),
        ]

        if self.admin:
            nav_items.append(("funcionarios", "👨‍💼 Funcionários"))
            nav_items.append(("excluidos", "🗂️ Arquivo"))

        nav_items.extend([
            ("pagamentos", "💳 Pagamentos"),
            ("presencas", "✅ Presenças"),
            ("camera", "📷 Câmara"),
        ])

        for i, (chave, texto) in enumerate(nav_items, start=3):
            btn = ctk.CTkButton(
                self.sidebar,
                text=texto,
                anchor="w",
                height=40,
                fg_color="transparent",
                hover_color=CORES["sidebar_hover"],
                command=lambda c=chave: self._mostrar_pagina(c),
            )
            btn.grid(row=i, column=0, padx=12, pady=4, sticky="ew")
            self._botoes_nav[chave] = btn

        ctk.CTkLabel(
            self.sidebar,
            text="Sistema de Gestão v1.0",
            text_color="gray",
            font=ctk.CTkFont(size=11),
        ).grid(row=9, column=0, padx=20, pady=15, sticky="sw")

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.paginas = {
            "dashboard": self._criar_dashboard(),
            "alunos": self._criar_alunos(),
            "pagamentos": self._criar_pagamentos(),
            "presencas": self._criar_presencas(),
            "funcionarios": self._criar_funcionarios(),
            "camera": self._criar_camera(),
        }

        if self.admin:
            self.paginas["excluidos"] = self._criar_excluidos()

    def _configurar_treeview(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Academia.Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            rowheight=28,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Academia.Treeview.Heading",
            background="#1a1a2e",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Academia.Treeview",
            background=[("selected", CORES["sidebar_active"])],
            foreground=[("selected", "white")],
        )

    def _mostrar_pagina(self, nome):
        if self._pagina_atual:
            self.paginas[self._pagina_atual].grid_forget()

        for chave, btn in self._botoes_nav.items():
            if chave == nome:
                btn.configure(fg_color=CORES["sidebar_active"])
            else:
                btn.configure(fg_color="transparent")

        if nome == "excluidos" and not self.admin:
            return
        self.paginas[nome].grid(row=0, column=0, sticky="nsew")
        self._pagina_atual = nome

        if nome == "dashboard":
            self._atualizar_dashboard()
        elif nome == "alunos":
            self._atualizar_lista_alunos()
        elif nome == "excluidos":
            self._atualizar_lista_excluidos()
        elif nome == "pagamentos":
            self._atualizar_pagamentos()
        elif nome == "presencas":
            self._atualizar_presencas()
        elif nome == "funcionarios":
            self._atualizar_funcionarios()

    def _criar_dashboard(self):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 15))
        ctk.CTkLabel(
            header, text="Dashboard", font=ctk.CTkFont(size=28, weight="bold")
        ).pack(side="left")
        ctk.CTkButton(
            header, text="Atualizar", width=100, command=self._atualizar_dashboard
        ).pack(side="right")

        self.cards = {}
        if self.admin:
            card_defs = [
                ("total_alunos", "Total Alunos", CORES["accent"]),
                ("funcionarios_registados", "Funcionários", "#3498db"),
                ("receita_total", "Receita Total (€)", "#27ae60"),
                ("receita_mes", "Receita do Mês (€)", "#8e44ad"),
                ("mensalidades_validas", "Mensalidades OK", CORES["success"]),
                ("mensalidades_atrasadas", "Em Atraso", CORES["danger"]),
                ("presencas_hoje", "Presenças Hoje", CORES["warning"]),
            ]

        else:

            card_defs = [
                ("total_alunos", "Total Alunos", CORES["accent"]),
                ("mensalidades_validas", "Mensalidades OK", CORES["success"]),
                ("mensalidades_atrasadas", "Em Atraso", CORES["danger"]),
                ("presencas_hoje", "Presenças Hoje", CORES["warning"]),
            ]

        for i, (chave, titulo, cor) in enumerate(card_defs):

            if self.admin:
                # 4 cards na primeira linha e 3 na segunda
                linha = 1 if i < 4 else 2
                coluna = i if i < 4 else i - 4
            else:
                # Funcionário: todos na primeira linha
                linha = 1
                coluna = i

            card = ctk.CTkFrame(frame, fg_color=CORES["card"], corner_radius=12)

            card.grid(
                row=linha,
                column=coluna,
                padx=8,
                pady=8,
                sticky="nsew",
            )

            ctk.CTkLabel(
                card,
                text=titulo,
                font=ctk.CTkFont(size=13)
            ).pack(padx=15, pady=(15, 5), anchor="w")

            valor = ctk.CTkLabel(
                card,
                text="—",
                font=ctk.CTkFont(size=36, weight="bold"),
                text_color=cor
            )

            valor.pack(padx=15, pady=(0, 15), anchor="w")

            self.cards[chave] = valor

        planos_frame = ctk.CTkFrame(frame, fg_color=CORES["card"], corner_radius=12)
        planos_frame.grid(row=3, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(
            planos_frame, text="Alunos por Plano", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10), anchor="w")
        self.planos_labels = {}
        for plano in ["plano_diario", "plano_mensal", "plano_trimestral", "plano_anual"]:
            row = ctk.CTkFrame(planos_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=4)
            nome = plano.replace("plano_", "").capitalize()
            ctk.CTkLabel(row, text=nome, width=120, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row, text="0", font=ctk.CTkFont(weight="bold"))
            lbl.pack(side="right")
            self.planos_labels[plano] = lbl

        resumo_frame = ctk.CTkFrame(frame, fg_color=CORES["card"], corner_radius=12)
        resumo_frame.grid(row=3, column=2, columnspan=2, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(
            resumo_frame, text="Resumo Geral", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10), anchor="w")
        self.resumo_labels = {}
        for chave, titulo in [
            ("total_presencas", "Total de presenças"),
            ("presencas_hoje", "Presenças hoje"),
            ("funcionario", "Funcionário autenticado"),
            ("cargo", "Cargo"),
        ]:
            row = ctk.CTkFrame(resumo_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=4)
            ctk.CTkLabel(row, text=titulo, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row, text="0", font=ctk.CTkFont(weight="bold"))
            lbl.pack(side="right")
            self.resumo_labels[chave] = lbl

        return frame

    def _atualizar_dashboard(self):
        stats = estatistica.estatisticas()
        for chave, lbl in self.cards.items():
            lbl.configure(text=str(stats.get(chave, 0)))
        for chave, lbl in self.planos_labels.items():
            lbl.configure(text=str(stats.get(chave, 0)))
        for chave, lbl in self.resumo_labels.items():

            if chave == "funcionario":
                lbl.configure(text=self.utilizador["nome"])

            elif chave == "cargo":
                lbl.configure(text=self.utilizador["tipo"])

            else:
                lbl.configure(text=str(stats.get(chave, 0)))

    def _criar_alunos(self):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(
            header, text="Gestão de Alunos", font=ctk.CTkFont(size=28, weight="bold")
        ).pack(side="left")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="+ Novo Aluno", command=self._novo_aluno).pack(
            side="left", padx=4
        )

        ctk.CTkButton(btn_frame, text="Editar", command=self._editar_aluno).pack(
            side="left", padx=4
        )
        if self.admin:
            ctk.CTkButton(
                btn_frame,
                text="Eliminar",
                fg_color=CORES["danger"],
                hover_color="#c0392b",
                command=self._eliminar_aluno,
            ).pack(side="left", padx=4)
                
        ctk.CTkButton(btn_frame, text="Atualizar", command=self._atualizar_lista_alunos).pack(
            side="left", padx=4
        )

        table_frame = ctk.CTkFrame(frame)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        cols = ("id", "nome", "telemovel", "documento", "plano", "mensalidade")
        self.tree_alunos = ttk.Treeview(
            table_frame, columns=cols, show="headings", style="Academia.Treeview"
        )
        headings = {
            "id": "ID",
            "nome": "Nome",
            "telemovel": "Telemóvel",
            "documento": "Documento",
            "plano": "Plano",
            "mensalidade": "Mensalidade",
        }
        widths = {
            "id": 50,
            "nome": 200,
            "telemovel": 120,
            "documento": 130,
            "plano": 100,
            "mensalidade": 110,
        }
        for col in cols:
            self.tree_alunos.heading(col, text=headings[col])
            self.tree_alunos.column(
                col, width=widths[col], anchor="center" if col == "id" else "w"
            )

        scroll = ctk.CTkScrollbar(table_frame, command=self.tree_alunos.yview)
        self.tree_alunos.configure(yscrollcommand=scroll.set)
        self.tree_alunos.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        scroll.grid(row=0, column=1, sticky="ns", pady=10, padx=(0, 10))

        return frame
    
    def _criar_funcionarios(self):

        frame = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # Cabeçalho
        header = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0,10)
        )

        ctk.CTkLabel(
            header,
            text="Gestão de Funcionários",
            font=ctk.CTkFont(
                size=28,
                weight="bold"
            )
        ).pack(side="left")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text="+ Novo Funcionário",
            command=self._novo_funcionario
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame,
            text="Editar",
            command=self._editar_funcionario
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame,
            text="Eliminar",
            fg_color=CORES["danger"],
            hover_color="#c0392b",
            command=self._eliminar_funcionario
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame,
            text="Atualizar",
            command=self._atualizar_funcionarios
        ).pack(side="left", padx=4)

        # Tabela

        table_frame = ctk.CTkFrame(frame)

        table_frame.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        cols = (
            "id",
            "nome",
            "usuario",
            "tipo"
        )

        self.tree_funcionarios = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            style="Academia.Treeview"
        )

        headings = {
            "id": "ID",
            "nome": "Nome",
            "usuario": "Utilizador",
            "tipo": "Cargo",
        }

        widths = {
            "id": 60,
            "nome": 250,
            "usuario": 220,
            "tipo": 150,
        }

        for col in cols:

            self.tree_funcionarios.heading(
                col,
                text=headings[col]
            )

            self.tree_funcionarios.column(
                col,
                width=widths[col],
                anchor="center" if col == "id" else "w"
            )

        scroll = ctk.CTkScrollbar(
            table_frame,
            command=self.tree_funcionarios.yview
        )

        self.tree_funcionarios.configure(
            yscrollcommand=scroll.set
        )

        self.tree_funcionarios.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(10,0),
            pady=10
        )

        scroll.grid(
            row=0,
            column=1,
            sticky="ns",
            padx=(0,10),
            pady=10
        )

        return frame

    def _funcionario_selecionado(self):

        selecao = self.tree_funcionarios.selection()

        if not selecao:
            messagebox.showinfo(
                "Seleção",
                "Selecione um funcionário."
            )
            return None

        id_funcionario = int(selecao[0])

        for funcionario in gestao_funcionarios.listar_funcionarios():

            if funcionario["id"] == id_funcionario:
                return funcionario

            return None

    def _novo_funcionario(self):

        def callback(nome, usuario, senha, tipo):

            ok = gestao_funcionarios.criar_funcionario(
                nome,
                usuario,
                senha,
                tipo
            )

            if ok:

                messagebox.showinfo(
                    "Sucesso",
                    f"Funcionário '{nome}' criado com sucesso."
                )

                self._atualizar_funcionarios()

            else:

                messagebox.showerror(
                    "Erro",
                    "Não foi possível criar o funcionário.\n"
                    "Verifique se o utilizador já existe."
                )

        FuncionarioFormDialog(
            self,
            callback
    )
    def _editar_funcionario(self):

        funcionario = self._funcionario_selecionado()

        if funcionario is None:
            return

        def callback(nome, usuario, senha, tipo):

            ok = gestao_funcionarios.editar_funcionario(
                funcionario["id"],
                nome,
                usuario,
                senha,
                tipo
            )

            if ok:

                messagebox.showinfo(
                    "Sucesso",
                    "Funcionário atualizado com sucesso."
                )

                self._atualizar_funcionarios()

            else:

                messagebox.showerror(
                    "Erro",
                    "Não foi possível atualizar o funcionário."
                )

        FuncionarioFormDialog(
            self,
            callback,
            funcionario
        )

    def _eliminar_funcionario(self):

        funcionario = self._funcionario_selecionado()

        if funcionario is None:
            return

        if funcionario["usuario"] == self.utilizador["usuario"]:
            messagebox.showwarning(
                "Aviso",
                "Não pode eliminar o utilizador com a sessão iniciada."
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar",
            f"Eliminar o funcionário '{funcionario['nome']}'?"
        )

        if not confirmar:
            return

        if gestao_funcionarios.eliminar_funcionario(funcionario["id"]):

            messagebox.showinfo(
                "Sucesso",
                "Funcionário eliminado com sucesso."
            )

            self._atualizar_funcionarios()

        else:

            messagebox.showerror(
                "Erro",
                "Não foi possível eliminar o funcionário."
            )

    def _atualizar_lista_alunos(self):
        for item in self.tree_alunos.get_children():
            self.tree_alunos.delete(item)

        for aluno in gestao_alunos.listar_alunos():
            valida = pagamentos.mensalidade_valida(aluno["id"])
            estado = "✓ Válida" if valida else "✗ Expirada"
            self.tree_alunos.insert(
                "",
                "end",
                iid=str(aluno["id"]),
                values=(
                    aluno["id"],
                    aluno["nome"],
                    aluno["telemovel"],
                    aluno["documento"],
                    aluno["plano"],
                    estado,
                ),
            )

    def _atualizar_funcionarios(self):

        # Limpa a tabela
        for item in self.tree_funcionarios.get_children():
            self.tree_funcionarios.delete(item)

        # Adiciona todos os funcionários
        for funcionario in gestao_funcionarios.listar_funcionarios():

            self.tree_funcionarios.insert(
                "",
                "end",
                iid=str(funcionario["id"]),
                values=(
                    funcionario["id"],
                    funcionario["nome"],
                    funcionario["usuario"],
                    funcionario["tipo"],
                ),
            )    

    def _aluno_selecionado(self):
        selecao = self.tree_alunos.selection()
        if not selecao:
            messagebox.showinfo("Seleção", "Selecione um aluno na lista.")
            return None
        return int(selecao[0])

    def _novo_aluno(self):
        def callback(nome, telemovel, documento, plano):
            self.withdraw()
            try:
                ok = gestao_alunos.criar_aluno(nome, telemovel, documento, plano)
            except Exception as erro:
                self.deiconify()
                messagebox.showerror("Erro", str(erro))
                return
            self.deiconify()
            if ok:
                messagebox.showinfo("Sucesso", f"Aluno '{nome}' registado com sucesso.")
                self._atualizar_lista_alunos()
            else:
                messagebox.showerror(
                    "Erro",
                    "Não foi possível registar o aluno.\n"
                    "Verifique se o documento já existe ou se a foto foi cancelada.",
                )

        AlunoFormDialog(self, "Novo Aluno", callback)

    def _editar_aluno(self):
        id_aluno = self._aluno_selecionado()
        if id_aluno is None:
            return
        aluno = aluno_por_id(id_aluno)
        if not aluno:
            return

        def callback(nome, telemovel, documento, plano):
            ok = gestao_alunos.editar_aluno(id_aluno, nome, telemovel, documento, plano)
            if ok:
                messagebox.showinfo("Sucesso", f"Aluno '{nome}' atualizado.")
                self._atualizar_lista_alunos()
            else:
                messagebox.showerror("Erro", "Documento já utilizado por outro aluno.")

        AlunoFormDialog(self, "Editar Aluno", callback, aluno=aluno)

    def _eliminar_aluno(self):
        if not self.admin:
            messagebox.showerror(
                "Permissão",
                "Apenas administradores podem eliminar alunos."
            )
            return
        id_aluno = self._aluno_selecionado()
        if id_aluno is None:
            return
        aluno = aluno_por_id(id_aluno)
        if not aluno:
            return

        if not messagebox.askyesno(
            "Confirmar",
            f"Mover '{aluno['nome']}' para o arquivo de exclusão?",
        ):
            return

        if gestao_alunos.eliminar_aluno(id_aluno):
            messagebox.showinfo("Sucesso", "Aluno movido para o arquivo.")
            self._atualizar_lista_alunos()
        else:
            messagebox.showerror("Erro", "Não foi possível eliminar o aluno.")

    def _criar_excluidos(self):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(
            header,
            text="Arquivo de Alunos Excluídos",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header, text="Restaurar", command=self._restaurar_aluno
        ).pack(side="right", padx=4)
        ctk.CTkButton(
            header, text="Atualizar", command=self._atualizar_lista_excluidos
        ).pack(side="right", padx=4)

        table_frame = ctk.CTkFrame(frame)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        cols = ("id", "nome", "documento", "plano", "data_exclusao")
        self.tree_excluidos = ttk.Treeview(
            table_frame, columns=cols, show="headings", style="Academia.Treeview"
        )
        headings = {
            "id": "ID",
            "nome": "Nome",
            "documento": "Documento",
            "plano": "Plano",
            "data_exclusao": "Data Exclusão",
        }
        for col in cols:
            self.tree_excluidos.heading(col, text=headings[col])
            self.tree_excluidos.column(
                col, width=150, anchor="center" if col == "id" else "w"
            )

        scroll = ctk.CTkScrollbar(table_frame, command=self.tree_excluidos.yview)
        self.tree_excluidos.configure(yscrollcommand=scroll.set)
        self.tree_excluidos.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        scroll.grid(row=0, column=1, sticky="ns", pady=10, padx=(0, 10))

        ctk.CTkLabel(
            frame,
            text="Alunos no arquivo são eliminados definitivamente após 60 dias.",
            text_color="gray",
        ).grid(row=2, column=0, pady=5)

        return frame

    def _atualizar_lista_excluidos(self):
        for item in self.tree_excluidos.get_children():
            self.tree_excluidos.delete(item)

        for aluno in gestao_alunos.listar_alunos_excluidos():
            self.tree_excluidos.insert(
                "",
                "end",
                iid=str(aluno["id"]),
                values=(
                    aluno["id"],
                    aluno["nome"],
                    aluno["documento"],
                    aluno["plano"],
                    aluno.get("data_exclusao", "—"),
                ),
            )

    def _restaurar_aluno(self):
        if not self.admin:
            messagebox.showerror(
                "Permissão",
                "Apenas administradores podem restaurar alunos."
            )
            return
        selecao = self.tree_excluidos.selection()
        if not selecao:
            messagebox.showinfo("Seleção", "Selecione um aluno para restaurar.")
            return

        id_aluno = int(selecao[0])
        if gestao_alunos.restaurar_aluno(id_aluno):
            messagebox.showinfo("Sucesso", "Aluno restaurado com sucesso.")
            self._atualizar_lista_excluidos()
        else:
            messagebox.showerror("Erro", "Não foi possível restaurar o aluno.")

    def _criar_pagamentos(self):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            frame, text="Pagamentos", font=ctk.CTkFont(size=28, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 15))

        form = ctk.CTkFrame(frame, fg_color=CORES["card"], corner_radius=12)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Aluno:").grid(row=0, column=0, padx=15, pady=12, sticky="e")
        self.pag_aluno_var = ctk.StringVar()
        self.pag_aluno_menu = ctk.CTkOptionMenu(
            form, variable=self.pag_aluno_var, values=["—"], width=300
        )
        self.pag_aluno_menu.grid(row=0, column=1, padx=10, pady=12, sticky="w")

        ctk.CTkLabel(form, text="Valor (€):").grid(
            row=0, column=2, padx=10, pady=12, sticky="e"
        )
        self.pag_valor_entry = ctk.CTkEntry(form, width=120, placeholder_text="0.00")
        self.pag_valor_entry.grid(row=0, column=3, padx=10, pady=12, sticky="w")

        ctk.CTkButton(
            form, text="Registar Pagamento", command=self._registar_pagamento
        ).grid(row=0, column=4, padx=15, pady=12)

        table_frame = ctk.CTkFrame(frame)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        cols = ("aluno", "plano", "valor", "data_pagamento", "data_vencimento", "estado")
        self.tree_pagamentos = ttk.Treeview(
            table_frame, columns=cols, show="headings", style="Academia.Treeview"
        )
        headings = {
            "aluno": "Aluno",
            "plano": "Plano",
            "valor": "Valor (€)",
            "data_pagamento": "Data Pagamento",
            "data_vencimento": "Vencimento",
            "estado": "Estado",
        }
        for col in cols:
            self.tree_pagamentos.heading(col, text=headings[col])
            self.tree_pagamentos.column(col, width=140, anchor="w")

        scroll = ctk.CTkScrollbar(table_frame, command=self.tree_pagamentos.yview)
        self.tree_pagamentos.configure(yscrollcommand=scroll.set)
        self.tree_pagamentos.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        scroll.grid(row=0, column=1, sticky="ns", pady=10, padx=(0, 10))

        return frame

    def _atualizar_pagamentos(self):
        nomes = []
        self._pag_map = {}
        for aluno in gestao_alunos.listar_alunos():
            texto = f"{aluno['id']} — {aluno['nome']}"
            nomes.append(texto)
            self._pag_map[texto] = aluno["id"]

        if nomes:
            self.pag_aluno_menu.configure(values=nomes)
            self.pag_aluno_var.set(nomes[0])
        else:
            self.pag_aluno_menu.configure(values=["—"])
            self.pag_aluno_var.set("—")

        for item in self.tree_pagamentos.get_children():
            self.tree_pagamentos.delete(item)

        for pag in reversed(pagamentos.pagamentos):
            self.tree_pagamentos.insert(
                "",
                "end",
                values=(
                    nome_aluno(pag["id_aluno"]),
                    pag["plano"],
                    pag["valor"],
                    pag["data_pagamento"],
                    pag["data_vencimento"],
                    pag["estado"],
                ),
            )

    def _registar_pagamento(self):
        selecionado = self.pag_aluno_var.get()
        if selecionado == "—" or selecionado not in self._pag_map:
            messagebox.showwarning("Aviso", "Não existem alunos registados.")
            return

        valor_texto = self.pag_valor_entry.get().strip().replace(",", ".")
        try:
            valor = float(valor_texto)
        except ValueError:
            messagebox.showwarning("Valor inválido", "Introduza um valor numérico válido.")
            return

        if valor <= 0:
            messagebox.showwarning("Valor inválido", "O valor deve ser superior a zero.")
            return

        id_aluno = self._pag_map[selecionado]
        if pagamentos.registar_pagamento(id_aluno, valor):
            messagebox.showinfo("Sucesso", "Pagamento registado com sucesso.")
            self.pag_valor_entry.delete(0, "end")
            self._atualizar_pagamentos()
        else:
            messagebox.showerror("Erro", "Não foi possível registar o pagamento.")

    def _criar_presencas(self):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            frame, text="Presenças", font=ctk.CTkFont(size=28, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 15))

        form = ctk.CTkFrame(frame, fg_color=CORES["card"], corner_radius=12)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(form, text="Aluno:").pack(side="left", padx=(15, 5), pady=12)
        self.pres_aluno_var = ctk.StringVar()
        self.pres_aluno_menu = ctk.CTkOptionMenu(
            form, variable=self.pres_aluno_var, values=["—"], width=300
        )
        self.pres_aluno_menu.pack(side="left", padx=5, pady=12)

        ctk.CTkButton(
            form, text="Registar Entrada", command=self._registar_presenca
        ).pack(side="left", padx=15, pady=12)
        ctk.CTkButton(
            form, text="Atualizar", command=self._atualizar_presencas
        ).pack(side="right", padx=15, pady=12)

        table_frame = ctk.CTkFrame(frame)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        cols = ("aluno", "data", "hora")
        self.tree_presencas = ttk.Treeview(
            table_frame, columns=cols, show="headings", style="Academia.Treeview"
        )
        headings = {"aluno": "Aluno", "data": "Data", "hora": "Hora"}
        for col in cols:
            self.tree_presencas.heading(col, text=headings[col])
            self.tree_presencas.column(col, width=250, anchor="w")

        scroll = ctk.CTkScrollbar(table_frame, command=self.tree_presencas.yview)
        self.tree_presencas.configure(yscrollcommand=scroll.set)
        self.tree_presencas.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        scroll.grid(row=0, column=1, sticky="ns", pady=10, padx=(0, 10))

        return frame

    def _atualizar_presencas(self):
        nomes = []
        self._pres_map = {}
        for aluno in gestao_alunos.listar_alunos():
            texto = f"{aluno['id']} — {aluno['nome']}"
            nomes.append(texto)
            self._pres_map[texto] = aluno["id"]

        if nomes:
            self.pres_aluno_menu.configure(values=nomes)
            self.pres_aluno_var.set(nomes[0])
        else:
            self.pres_aluno_menu.configure(values=["—"])
            self.pres_aluno_var.set("—")

        for item in self.tree_presencas.get_children():
            self.tree_presencas.delete(item)

        for pres in reversed(presencas.presencas):
            self.tree_presencas.insert(
                "",
                "end",
                values=(
                    nome_aluno(pres["id_aluno"]),
                    pres["data"],
                    pres["hora"],
                ),
            )

    def _registar_presenca(self):
        selecionado = self.pres_aluno_var.get()
        if selecionado == "—" or selecionado not in self._pres_map:
            messagebox.showwarning("Aviso", "Não existem alunos registados.")
            return

        id_aluno = self._pres_map[selecionado]
        if presencas.registar_presenca(id_aluno):
            messagebox.showinfo("Sucesso", f"Entrada registada para {nome_aluno(id_aluno)}.")
            self._atualizar_presencas()
        else:
            messagebox.showerror("Erro", "Não foi possível registar a presença.")

    def _criar_camera(self):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame, text="Câmara", font=ctk.CTkFont(size=28, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 20))

        info = ctk.CTkFrame(frame, fg_color=CORES["card"], corner_radius=12)
        info.grid(row=1, column=0, sticky="ew", pady=10)
        ctk.CTkLabel(
            info,
            text="Controlo da Webcam",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=20, pady=(20, 10), anchor="w")
        ctk.CTkLabel(
            info,
            text="Utilize os botões abaixo para abrir a câmara ou gravar vídeo.\n"
            "As funções abrem uma janela OpenCV separada.\n\n"
            "Atalhos na janela da câmara:\n"
            "  • Modo foto: B (preto e branco), C (cor), P (capturar), Q (sair)\n"
            "  • Modo vídeo: R (iniciar gravação), S (parar), ESC (sair)",
            justify="left",
            font=ctk.CTkFont(size=13),
        ).pack(padx=20, pady=(0, 20), anchor="w")

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="📷 Abrir Câmara",
            width=200,
            height=45,
            font=ctk.CTkFont(size=15),
            command=lambda: self._executar_camera(ligarCam),
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="🎬 Gravar Vídeo",
            width=200,
            height=45,
            font=ctk.CTkFont(size=15),
            command=lambda: self._executar_camera(gravarVideo),
        ).pack(side="left", padx=10)

        return frame

    def _executar_camera(self, funcao):
        threading.Thread(target=funcao, daemon=True).start()

if __name__ == "__main__":
    app = AcademiaApp()
    app.mainloop()
  
