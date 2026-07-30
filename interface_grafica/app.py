"""
Janela principal da interface gráfica — Sistema de Gestão de Academia.
"""
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

import customtkinter as ctk
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image

from projeto_ginasio.config import ARQUIVO_LOG, PASTA_ARQUIVOS
from projeto_ginasio.dados import pagamentos as pagamentos_db, presencas as presencas_db
from interface_grafica.constants import CORES, TEMA
from interface_grafica.dialogs import AlunoFormDialog, FuncionarioFormDialog
from interface_grafica.utils import aluno_por_id, nome_aluno, setup_paths
from interface_grafica.widgets import (
    PageFrame,
    PageHeader,
    SurfaceCard,
    TablePanel,
    btn_danger,
    btn_primary,
    btn_secondary,
    styled_entry,
    styled_option,
)

setup_paths()

from projeto_ginasio.main import inicializar
from projeto_ginasio.Camara import gravarVideo, ligarCam
from modulos import estatistica, gestao_alunos, pagamentos, presencas, funcionarios as gestao_funcionarios


class DashboardData:
    @staticmethod
    def presencas_30_dias():
        hoje = datetime.now().date()
        dias = [hoje - timedelta(days=i) for i in range(29, -1, -1)]
        contagem = {dia: 0 for dia in dias}
        for registo in presencas_db:
            try:
                data = datetime.strptime(registo["data"], "%d/%m/%Y").date()
            except (ValueError, KeyError):
                continue
            if data in contagem:
                contagem[data] += 1
        labels = [dia.strftime("%d/%m") for dia in dias]
        return labels, [contagem[dia] for dia in dias]

    @staticmethod
    def receita_mensal():
        agora = datetime.now()
        mes, ano = agora.month, agora.year
        chaves = []
        for _ in range(12):
            chaves.append((mes, ano))
            mes -= 1
            if mes == 0:
                mes, ano = 12, ano - 1
        chaves.reverse()
        totais = defaultdict(float)
        for pagamento in pagamentos_db:
            try:
                data = datetime.strptime(pagamento["data_pagamento"], "%d/%m/%Y")
                totais[(data.month, data.year)] += float(pagamento.get("valor", 0))
            except (ValueError, TypeError, KeyError):
                continue
        labels = [f"{m:02d}/{a % 100:02d}" for m, a in chaves]
        return labels, [totais[chave] for chave in chaves]


def _ease_out_cubic(t):
    return 1 - (1 - min(max(t, 0), 1)) ** 3


class MetricCard(ctk.CTkFrame):
    def __init__(self, master, icon, title, color):
        super().__init__(
            master,
            fg_color=TEMA["surface"],
            corner_radius=16,
            border_width=1,
            border_color=TEMA["border"],
        )
        self._target = 0.0
        self._display = 0.0
        self._currency = False
        self._job = None
        self.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(top, text=icon, font=ctk.CTkFont(size=18)).pack(side="left")
        ctk.CTkLabel(
            top,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=TEMA["muted"],
        ).pack(side="left", padx=(8, 0))

        self.valor = ctk.CTkLabel(
            self,
            text="—",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=color,
            anchor="w",
        )
        self.valor.pack(fill="x", padx=16, pady=(0, 14))

    def set_value(self, value, currency=False, animate=True):
        self._currency = currency
        self._target = float(value)
        if not animate:
            self.stop_animation()
            self._display = self._target
            self._render()
            return
        self.stop_animation()
        self._tick()

    def _tick(self):
        if not self.winfo_exists() or not self.valor.winfo_exists():
            self._job = None
            return

        diff = self._target - self._display
        if abs(diff) < 0.05:
            self._display = self._target
            self._render()
            self._job = None
            return
        self._display += diff * 0.22
        self._render()
        self._job = self.after(16, self._tick)

    def _render(self):
        if not self.winfo_exists() or not self.valor.winfo_exists():
            return
        if self._currency:
            texto = f"{self._display:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            texto = str(int(round(self._display)))
        self.valor.configure(text=texto)

    def stop_animation(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            finally:
                self._job = None

    def destroy(self):
        self.stop_animation()
        super().destroy()


class ChartPanel(ctk.CTkFrame):
    def __init__(self, master, title):
        super().__init__(
            master,
            fg_color=TEMA["surface"],
            corner_radius=16,
            border_width=1,
            border_color=TEMA["border"],
        )
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._anim = None

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEMA["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 0))

        self.fig = Figure(facecolor=TEMA["surface"], tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=TEMA["surface"], highlightthickness=0)
        widget.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        if event.widget is not self or event.width < 80 or event.height < 80:
            return
        dpi = self.fig.get_dpi()
        altura = max(event.height - 44, 60)
        largura = max(event.width - 12, 60)
        self.fig.set_size_inches(largura / dpi, altura / dpi, forward=True)
        self.fig.subplots_adjust(left=0.12, right=0.96, top=0.88, bottom=0.18)
        self.canvas.draw_idle()

    def stop_animation(self):
        if self._anim:
            event_source = getattr(self._anim, "event_source", None)
            if event_source is not None:
                try:
                    event_source.stop()
                except Exception:
                    pass
            self._anim = None

    def set_animation(self, anim):
        self.stop_animation()
        self._anim = anim


class DashboardCharts:
    @staticmethod
    def _style_axes(ax):
        ax.set_facecolor(TEMA["surface"])
        ax.figure.patch.set_facecolor(TEMA["surface"])
        ax.tick_params(colors=TEMA["muted"], labelsize=8, length=0)
        ax.title.set_color(TEMA["text"])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(True, axis="y", color=TEMA["border"], alpha=0.55, linewidth=0.6)
        ax.set_axisbelow(True)

    @classmethod
    def barras_planos(cls, panel, labels, valores):
        panel.ax.clear()
        cls._style_axes(panel.ax)
        maximo = max(valores) if valores and max(valores) > 0 else 1
        cores = TEMA["chart"][: len(labels)]
        panel.ax.bar(
            labels,
            valores,
            color=cores,
            width=0.58,
            edgecolor="none",
            zorder=3,
        )
        panel.ax.set_ylim(0, maximo * 1.18)
        panel.ax.set_ylabel("Alunos", color=TEMA["muted"], fontsize=8)
        panel.canvas.draw_idle()
        panel.set_animation(None)

    @classmethod
    def linha_presencas(cls, panel, labels, valores):
        panel.ax.clear()
        cls._style_axes(panel.ax)
        x = list(range(len(valores)))
        maximo = max(valores) if valores and max(valores) > 0 else 1
        panel.ax.plot(x, valores, color=TEMA["cyan"], linewidth=2.4, zorder=4)
        panel.ax.fill_between(x, valores, color=TEMA["cyan"], alpha=0.12)
        panel.ax.set_xlim(-0.5, len(valores) - 0.5)
        panel.ax.set_ylim(0, maximo * 1.15)
        panel.ax.set_ylabel("Entradas", color=TEMA["muted"], fontsize=8)
        passo = max(1, len(labels) // 6)
        panel.ax.set_xticks(x[::passo])
        panel.ax.set_xticklabels(
            [labels[i] for i in range(0, len(labels), passo)], rotation=35, ha="right"
        )
        panel.canvas.draw_idle()
        panel.set_animation(None)

    @classmethod
    def donut_pagamentos(cls, panel, ok, atraso):
        panel.ax.clear()
        panel.ax.set_facecolor(TEMA["surface"])
        panel.fig.patch.set_facecolor(TEMA["surface"])
        total = ok + atraso
        if total <= 0:
            panel.ax.text(
                0.5, 0.5, "Sem dados", ha="center", va="center",
                color=TEMA["muted"], fontsize=11, transform=panel.ax.transAxes,
            )
            panel.ax.axis("off")
            panel.canvas.draw_idle()
            panel.set_animation(None)
            return

        cores = [TEMA["success"], TEMA["danger"]]
        rotulos = ["Pagas", "Em atraso"]
        wedges, _ = panel.ax.pie(
            [ok, atraso],
            colors=cores,
            startangle=90,
            wedgeprops=dict(width=0.52, edgecolor=TEMA["surface"], linewidth=2),
        )
        panel.ax.text(
            0, 0, str(int(total)), ha="center", va="center",
            fontsize=16, fontweight="bold", color=TEMA["text"],
        )
        panel.ax.legend(
            wedges, rotulos, loc="center left", bbox_to_anchor=(1.02, 0.5),
            frameon=False, labelcolor=TEMA["muted"], fontsize=8,
        )
        panel.ax.axis("equal")
        panel.canvas.draw_idle()
        panel.set_animation(None)

    @classmethod
    def receita_mensal(cls, panel, labels, valores):
        panel.ax.clear()
        cls._style_axes(panel.ax)
        maximo = max(valores) if valores and max(valores) > 0 else 1
        x = list(range(len(valores)))
        panel.ax.bar(
            x, valores, color=TEMA["accent"],
            width=0.62, edgecolor="none", alpha=0.92, zorder=3,
        )
        panel.ax.plot(x, valores, color=TEMA["cyan"], linewidth=2, marker="o", markersize=3, zorder=4)
        panel.ax.set_xlim(-0.6, len(valores) - 0.4)
        panel.ax.set_ylim(0, maximo * 1.18)
        panel.ax.set_ylabel("€", color=TEMA["muted"], fontsize=8)
        passo = max(1, len(labels) // 6)
        panel.ax.set_xticks(x[::passo])
        panel.ax.set_xticklabels([labels[i] for i in range(0, len(labels), passo)], rotation=35, ha="right")
        panel.canvas.draw_idle()
        panel.set_animation(None)

class AcademiaApp(ctk.CTk):
    """Janela principal da aplicação."""

    def __init__(self, utilizador):
        self.utilizador = utilizador
        self.admin = self.utilizador["tipo"] == "Administrador"
        self.reabrir_login = False
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("FitControl — Gestão de Academia")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=TEMA["bg"])

        inicializar()

        self._pagina_atual = None
        self._botoes_nav = {}
        self._dashboard_job = None
        self._dashboard_clock_job = None
        self._dashboard_refresh_ms = 12000
        self._face_id_thread = None
        self._face_id_start_job = None
        self._face_id_status_job = None
        self.cards = {}
        self._chart_panels = []
        self.protocol("WM_DELETE_WINDOW", self._fechar_aplicacao)

        self._criar_layout()
        self._configurar_treeview()
        self._mostrar_pagina("dashboard")

    def iniciar_face_id(self):
        if self._pagina_atual != "presencas":
            return

        try:
            from projeto_ginasio.reconhecimento.reconhecimento import (
                iniciar_reconhecimento,
                reconhecimento_ativo,
            )

            if reconhecimento_ativo():
                return

            if self._face_id_thread and self._face_id_thread.is_alive():
                self._cancelar_arranque_face_id()
                self._face_id_start_job = self.after(300, self.iniciar_face_id)
                return

            self._face_id_thread = threading.Thread(
                target=iniciar_reconhecimento,
                daemon=True
            )
            self._face_id_thread.start()

            print("Face ID iniciado.")

        except Exception as erro:
            print(f"Erro ao iniciar Face ID: {erro}")

    def parar_face_id(self):
        self._cancelar_arranque_face_id()
        try:
            from projeto_ginasio.reconhecimento.reconhecimento import parar_reconhecimento

            parar_reconhecimento()
        except Exception as erro:
            print(f"Erro ao parar Face ID: {erro}")

    def _cancelar_arranque_face_id(self):
        if self._face_id_start_job:
            try:
                self.after_cancel(self._face_id_start_job)
            except Exception:
                pass
            finally:
                self._face_id_start_job = None

    def _agendar_estado_face_id(self):
        self._cancelar_estado_face_id()
        self._face_id_status_job = self.after(
            400, self._atualizar_estado_face_id
        )

    def _cancelar_estado_face_id(self):
        if self._face_id_status_job:
            self.after_cancel(self._face_id_status_job)
            self._face_id_status_job = None

    def _agendar_relogio_dashboard(self):
        self._cancelar_relogio_dashboard()
        self._dashboard_clock_job = self.after(
            1000, self._atualizar_relogio_dashboard
        )

    def _cancelar_relogio_dashboard(self):
        if self._dashboard_clock_job:
            self.after_cancel(self._dashboard_clock_job)
            self._dashboard_clock_job = None

    def _atualizar_relogio_dashboard(self):
        if self._pagina_atual != "dashboard" or not hasattr(self, "_dashboard_clock"):
            self._cancelar_relogio_dashboard()
            return

        self._dashboard_clock.configure(
            text=datetime.now().strftime("%H:%M:%S")
        )
        self._agendar_relogio_dashboard()

    def _parar_animacoes_dashboard(self):
        for card in self.cards.values():
            card.stop_animation()
        for painel in self._chart_panels:
            painel.stop_animation()

    def _atualizar_estado_face_id(self):
        if self._pagina_atual != "presencas":
            self._cancelar_estado_face_id()
            return

        try:
            from projeto_ginasio.reconhecimento.reconhecimento import obter_estado_reconhecimento

            estado = obter_estado_reconhecimento()
        except Exception as erro:
            estado = {
                "estado": "erro",
                "titulo": "Erro no Face ID",
                "detalhe": str(erro),
            }

        mapa_cores = {
            "ativo": TEMA["success"],
            "desconhecido": TEMA["warning"],
            "a_iniciar": TEMA["accent"],
            "sem_alunos": TEMA["warning"],
            "erro": TEMA["danger"],
            "parado": TEMA["muted"],
        }
        cor = mapa_cores.get(estado.get("estado"), TEMA["muted"])
        titulo = estado.get("titulo", "Face ID")
        detalhe = estado.get("detalhe", "")

        self.pres_face_estado_badge.configure(text="●", text_color=cor)
        self.pres_face_estado_titulo.configure(text=titulo, text_color=cor)
        self.pres_face_estado_detalhe.configure(text=detalhe)

        self._agendar_estado_face_id()

    def _fechar_aplicacao(self):
        self.reabrir_login = False
        self._encerrar_recursos()
        self.destroy()

    def _encerrar_recursos(self):
        self._cancelar_atualizacao_dashboard()
        self._cancelar_relogio_dashboard()
        self._cancelar_estado_face_id()
        self._parar_animacoes_dashboard()
        self.parar_face_id()

    def _criar_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=0,
            fg_color=TEMA["sidebar"],
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(11, weight=1)

        ctk.CTkLabel(
            self.sidebar,
            text="🏋️ FitControl",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEMA["text"],
        ).grid(row=0, column=0, padx=20, pady=(28, 6), sticky="w")

        ctk.CTkLabel(
            self.sidebar,
            text=self.utilizador["nome"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEMA["text"],
        ).grid(row=1, column=0, padx=20, sticky="w")

        ctk.CTkLabel(
            self.sidebar,
            text=self.utilizador["tipo"],
            text_color=TEMA["muted"],
            font=ctk.CTkFont(size=11),
        ).grid(row=2, column=0, padx=20, pady=(0, 22), sticky="w")
       
        nav_items = [
            ("dashboard", "📊 Dashboard"),
            ("alunos", "👥 Alunos"),
        ]

        if self.admin:
            nav_items.append(("funcionarios", "👨‍💼 Funcionários"))
            nav_items.append(("excluidos", "🗂️ Arquivo de Alunos"))
            nav_items.append(("administracao", "⚙ Administração"))

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
                height=38,
                corner_radius=TEMA["radius_sm"],
                fg_color="transparent",
                text_color=TEMA["muted"],
                hover_color=TEMA["sidebar_hover"],
                command=lambda c=chave: self._mostrar_pagina(c),
            )
            btn.grid(row=i, column=0, padx=12, pady=4, sticky="ew")
            self._botoes_nav[chave] = btn

        ctk.CTkButton(
            self.sidebar,
            text="🚪 Logout",
            anchor="w",
            height=38,
            corner_radius=TEMA["radius_sm"],
            fg_color="transparent",
            text_color=TEMA["muted"],
            hover_color=TEMA["sidebar_hover"],
            command=self.logout,
        ).grid(row=12, column=0, padx=12, pady=(10, 5), sticky="sew")

        ctk.CTkLabel(
            self.sidebar,
            text="Sistema de Gestão v4.0",
            text_color=TEMA["muted"],
            font=ctk.CTkFont(size=10),
        ).grid(row=13, column=0, padx=20, pady=(0, 15), sticky="sw")

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=TEMA["bg"])
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
            "administracao": self._criar_administracao(),
        }

        if self.admin:
            self.paginas["excluidos"] = self._criar_excluidos()

    def logout(self):
        confirmar = messagebox.askyesno(
            "Logout",
            "Tem a certeza de que pretende terminar sessão?"
        )

        if not confirmar:
            return

        self.reabrir_login = True
        self._encerrar_recursos()
        self.destroy()

    def _configurar_treeview(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Academia.Treeview",
            background=TEMA["table_bg"],
            foreground=TEMA["text"],
            fieldbackground=TEMA["table_bg"],
            rowheight=32,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.configure(
            "Academia.Treeview.Heading",
            background=TEMA["table_head"],
            foreground=TEMA["muted"],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Academia.Treeview",
            background=[("selected", TEMA["table_select"])],
            foreground=[("selected", "white")],
        )
        style.map(
            "Academia.Treeview.Heading",
            background=[("active", TEMA["surface_alt"])],
        )

    def _mostrar_pagina(self, nome):
        pagina_anterior = self._pagina_atual
        frame_anterior = self.paginas.get(pagina_anterior) if pagina_anterior else None

        try:
            if pagina_anterior == "dashboard" and nome != "dashboard":
                self._cancelar_relogio_dashboard()
                self._parar_animacoes_dashboard()

            if pagina_anterior == "presencas" and nome != "presencas":
                self._cancelar_estado_face_id()
                self.parar_face_id()

            if self._pagina_atual:
                self.paginas[self._pagina_atual].grid_forget()

            for chave, btn in self._botoes_nav.items():
                if chave == nome:
                    btn.configure(
                        fg_color=TEMA["sidebar_active"],
                        text_color=TEMA["sidebar_active_text"],
                    )
                else:
                    btn.configure(fg_color="transparent", text_color=TEMA["muted"])

            if nome == "excluidos" and not self.admin:
                return

            pagina = self.paginas[nome]
            pagina.grid(row=0, column=0, sticky="nsew")
            self._pagina_atual = nome

            if nome == "dashboard":
                self._atualizar_dashboard()
                self._agendar_atualizacao_dashboard()
                self._atualizar_relogio_dashboard()
            else:
                self._cancelar_atualizacao_dashboard()
                self._cancelar_relogio_dashboard()

            if nome == "alunos":
                self._atualizar_lista_alunos()
            elif nome == "excluidos":
                self._atualizar_lista_excluidos()
            elif nome == "pagamentos":
                self._atualizar_pagamentos()
            elif nome == "presencas":
                self._atualizar_presencas()
                self.iniciar_face_id()
                self._agendar_estado_face_id()
            elif nome == "funcionarios":
                self._atualizar_funcionarios()
            elif nome == "administracao":
                self._carregar_historico()
                self._carregar_arquivos_historico()
        except Exception as erro:
            self._cancelar_atualizacao_dashboard()
            self._cancelar_relogio_dashboard()
            self._cancelar_estado_face_id()
            for chave, btn in self._botoes_nav.items():
                if chave == pagina_anterior:
                    btn.configure(
                        fg_color=TEMA["sidebar_active"],
                        text_color=TEMA["sidebar_active_text"],
                    )
                else:
                    btn.configure(fg_color="transparent", text_color=TEMA["muted"])
            if frame_anterior is not None:
                frame_anterior.grid(row=0, column=0, sticky="nsew")
                self._pagina_atual = pagina_anterior
            messagebox.showerror("Erro", f"Não foi possível abrir o módulo: {erro}")

    def _criar_dashboard(self):
        frame = ctk.CTkFrame(self.content, fg_color=TEMA["bg"])
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        titulo = ctk.CTkFrame(header, fg_color="transparent")
        titulo.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            titulo,
            text="Dashboard",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=TEMA["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            titulo,
            text="Visão geral em tempo real da academia",
            font=ctk.CTkFont(size=12),
            text_color=TEMA["muted"],
        ).pack(anchor="w", pady=(2, 0))

        acoes = ctk.CTkFrame(header, fg_color="transparent")
        acoes.grid(row=0, column=1, sticky="e")
        self._dashboard_clock = ctk.CTkLabel(
            acoes,
            text=datetime.now().strftime("%H:%M:%S"),
            font=ctk.CTkFont(family="Consolas", size=24, weight="bold"),
            text_color=TEMA["accent"],
        )
        self._dashboard_clock.pack(side="left", padx=(0, 6))

        metrics = ctk.CTkFrame(frame, fg_color="transparent")
        metrics.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1)

        if self.admin:
            card_defs = [
                ("total_alunos", "👥", "Total de alunos", TEMA["accent"]),
                ("funcionarios_registados", "👨‍💼", "Funcionários", TEMA["cyan"]),
                ("receita_total", "💰", "Receita total", TEMA["success"]),
                ("receita_mes", "📈", "Receita do mês", "#a78bfa"),
                ("mensalidades_validas", "✓", "Mensalidades pagas", TEMA["success"]),
                ("mensalidades_atrasadas", "!", "Mensalidades em atraso", TEMA["danger"]),
                ("presencas_hoje", "📅", "Presenças hoje", TEMA["warning"]),
            ]
        else:
            card_defs = [
                ("total_alunos", "👥", "Total de alunos", TEMA["accent"]),
                ("mensalidades_validas", "✓", "Mensalidades pagas", TEMA["success"]),
                ("mensalidades_atrasadas", "!", "Mensalidades em atraso", TEMA["danger"]),
                ("presencas_hoje", "📅", "Presenças hoje", TEMA["warning"]),
            ]

        self.cards = {}
        for i, (chave, icon, titulo, cor) in enumerate(card_defs):
            linha = 0 if i < 4 else 1
            coluna = i if i < 4 else i - 4
            card = MetricCard(metrics, icon, titulo, cor)
            card.grid(row=linha, column=coluna, padx=6, pady=6, sticky="nsew")
            self.cards[chave] = card

        charts = ctk.CTkFrame(frame, fg_color="transparent")
        charts.grid(row=2, column=0, sticky="nsew")
        charts.grid_columnconfigure((0, 1), weight=1)
        charts.grid_rowconfigure((0, 1), weight=1)

        titulos = [
            "Alunos por plano",
            "Presenças — últimos 30 dias",
            "Pagamentos OK vs em atraso",
            "Receita mensal",
        ]
        self._chart_panels = []
        for i, titulo_grafico in enumerate(titulos):
            painel = ChartPanel(charts, titulo_grafico)
            painel.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky="nsew")
            self._chart_panels.append(painel)

        return frame

    def _agendar_atualizacao_dashboard(self):
        self._cancelar_atualizacao_dashboard()
        self._dashboard_job = self.after(
            self._dashboard_refresh_ms, self._auto_atualizar_dashboard
        )

    def _cancelar_atualizacao_dashboard(self):
        if self._dashboard_job:
            self.after_cancel(self._dashboard_job)
            self._dashboard_job = None

    def _auto_atualizar_dashboard(self):
        if self._pagina_atual == "dashboard":
            self._atualizar_dashboard()
        self._agendar_atualizacao_dashboard()

    def _atualizar_dashboard(self):
        stats = estatistica.estatisticas()
        moeda = {
            "receita_total", "receita_mes",
        }
        for chave, card in self.cards.items():
            card.set_value(
                stats.get(chave, 0),
                currency=chave in moeda,
                animate=True,
            )
        self._atualizar_graficos(stats)

    def _atualizar_graficos(self, stats):
        for painel in self._chart_panels:
            painel.stop_animation()

        planos = ["Diário", "Mensal", "Trimestral", "Anual"]
        valores_planos = [
            stats.get("plano_diario", 0),
            stats.get("plano_mensal", 0),
            stats.get("plano_trimestral", 0),
            stats.get("plano_anual", 0),
        ]
        labels_pres, valores_pres = DashboardData.presencas_30_dias()
        labels_rec, valores_rec = DashboardData.receita_mensal()

        DashboardCharts.barras_planos(self._chart_panels[0], planos, valores_planos)
        DashboardCharts.linha_presencas(self._chart_panels[1], labels_pres, valores_pres)
        DashboardCharts.donut_pagamentos(
            self._chart_panels[2],
            stats.get("mensalidades_validas", 0),
            stats.get("mensalidades_atrasadas", 0),
        )
        DashboardCharts.receita_mensal(self._chart_panels[3], labels_rec, valores_rec)

    def _criar_alunos(self):
        frame = PageFrame(self.content)
        frame.grid_columnconfigure(0, weight=3)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        header = PageHeader(frame, "Gestão de Alunos", "Registar, editar e consultar alunos")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        btn_primary(header.actions, text="+ Novo Aluno", command=self._novo_aluno).pack(
            side="left", padx=4
        )
        btn_secondary(header.actions, text="Editar", command=self._editar_aluno).pack(
            side="left", padx=4
        )
        if self.admin:
            btn_danger(header.actions, text="Eliminar", command=self._eliminar_aluno).pack(
                side="left", padx=4
            )
        btn_secondary(header.actions, text="Atualizar", command=self._atualizar_lista_alunos).pack(
            side="left", padx=4
        )

        table_frame = TablePanel(frame)
        table_frame.grid(row=1, column=0, sticky="nsew")

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
        self.tree_alunos.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=12)
        scroll.grid(row=0, column=1, sticky="ns", pady=12, padx=(0, 12))
        self.tree_alunos.bind("<<TreeviewSelect>>", self._ao_selecionar_aluno)

        sidebar = SurfaceCard(frame)
        sidebar.grid(row=1, column=1, sticky="nsew", padx=(12, 0))
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="Aluno selecionado",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEMA["text"],
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 2))
        ctk.CTkLabel(
            sidebar,
            text="Veja os dados principais e a fotografia do registo ativo.",
            font=ctk.CTkFont(size=11),
            text_color=TEMA["muted"],
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        self.aluno_foto_label = ctk.CTkLabel(
            sidebar,
            text="Sem foto",
            width=180,
            height=180,
            corner_radius=14,
            fg_color=TEMA["surface_alt"],
            text_color=TEMA["muted"],
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.aluno_foto_label.grid(row=2, column=0, padx=16, pady=(0, 14))

        self._aluno_info_widgets = {}
        campos = [
            ("nome", "Nome"),
            ("id", "ID"),
            ("telemovel", "Telemóvel"),
            ("documento", "Documento"),
            ("plano", "Plano"),
            ("mensalidade", "Mensalidade"),
        ]

        for indice, (chave, rotulo) in enumerate(campos, start=3):
            bloco = ctk.CTkFrame(sidebar, fg_color="transparent")
            bloco.grid(row=indice, column=0, sticky="ew", padx=16, pady=(0, 10))
            bloco.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                bloco,
                text=rotulo,
                font=ctk.CTkFont(size=11),
                text_color=TEMA["muted"],
            ).grid(row=0, column=0, sticky="w")

            valor = ctk.CTkLabel(
                bloco,
                text="—",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=TEMA["text"],
                anchor="w",
                justify="left",
            )
            valor.grid(row=1, column=0, sticky="w", pady=(2, 0))
            self._aluno_info_widgets[chave] = valor

        self._aluno_ctk_image = None
        self._limpar_detalhes_aluno()

        return frame

    def _criar_funcionarios(self):
        frame = PageFrame(self.content)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        header = PageHeader(frame, "Gestão de Funcionários", "Utilizadores e permissões do sistema")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        btn_primary(header.actions, text="+ Novo Funcionário", command=self._novo_funcionario).pack(
            side="left", padx=4
        )
        btn_secondary(header.actions, text="Editar", command=self._editar_funcionario).pack(
            side="left", padx=4
        )
        btn_danger(header.actions, text="Eliminar", command=self._eliminar_funcionario).pack(
            side="left", padx=4
        )
        btn_secondary(header.actions, text="Atualizar", command=self._atualizar_funcionarios).pack(
            side="left", padx=4
        )

        table_frame = TablePanel(frame)
        table_frame.grid(row=1, column=0, sticky="nsew")

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
            padx=(12, 0),
            pady=12,
        )

        scroll.grid(
            row=0,
            column=1,
            sticky="ns",
            padx=(0, 12),
            pady=12,
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

        valores = self.tree_funcionarios.item(selecao[0], "values")
        if not valores:
            return None

        id_funcionario = int(valores[0])

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
        selecao_atual = self.tree_alunos.selection()
        aluno_selecionado = None
        if selecao_atual:
            valores = self.tree_alunos.item(selecao_atual[0], "values")
            if valores:
                aluno_selecionado = str(valores[0])

        for item in self.tree_alunos.get_children():
            self.tree_alunos.delete(item)

        item_para_reselecionar = None
        for indice, aluno in enumerate(gestao_alunos.listar_alunos()):
            valida = pagamentos.mensalidade_valida(aluno["id"])
            estado = "✓ Válida" if valida else "✗ Expirada"
            iid = f"aluno_{indice}"
            self.tree_alunos.insert(
                "",
                "end",
                iid=iid,
                values=(
                    aluno["id"],
                    aluno["nome"],
                    aluno["telemovel"],
                    aluno["documento"],
                    aluno["plano"],
                    estado,
                ),
            )
            if aluno_selecionado is not None and str(aluno["id"]) == aluno_selecionado:
                item_para_reselecionar = iid

        if item_para_reselecionar and self.tree_alunos.exists(item_para_reselecionar):
            self.tree_alunos.selection_set(item_para_reselecionar)
            self.tree_alunos.focus(item_para_reselecionar)
            self._atualizar_detalhes_aluno(int(aluno_selecionado))
        else:
            self._limpar_detalhes_aluno()

    def _atualizar_funcionarios(self):

        # Limpa a tabela
        for item in self.tree_funcionarios.get_children():
            self.tree_funcionarios.delete(item)

        # Adiciona todos os funcionários
        for indice, funcionario in enumerate(gestao_funcionarios.listar_funcionarios()):

            self.tree_funcionarios.insert(
                "",
                "end",
                iid=f"funcionario_{indice}",
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
        valores = self.tree_alunos.item(selecao[0], "values")
        if not valores:
            return None
        return int(valores[0])

    def _ao_selecionar_aluno(self, _event=None):
        selecao = self.tree_alunos.selection()
        if not selecao:
            self._limpar_detalhes_aluno()
            return
        valores = self.tree_alunos.item(selecao[0], "values")
        if not valores:
            self._limpar_detalhes_aluno()
            return
        self._atualizar_detalhes_aluno(int(valores[0]))

    def _limpar_detalhes_aluno(self):
        self._aluno_ctk_image = None
        if hasattr(self, "aluno_foto_label"):
            self.aluno_foto_label.configure(
                image=None,
                text="Selecione um aluno",
            )
        if hasattr(self, "_aluno_info_widgets"):
            for widget in self._aluno_info_widgets.values():
                widget.configure(text="—")

    def _atualizar_detalhes_aluno(self, id_aluno):
        aluno = aluno_por_id(id_aluno)
        if not aluno:
            self._limpar_detalhes_aluno()
            return

        mensalidade = "✓ Válida" if pagamentos.mensalidade_valida(aluno["id"]) else "✗ Expirada"
        detalhes = {
            "nome": aluno.get("nome", "—"),
            "id": str(aluno.get("id", "—")),
            "telemovel": aluno.get("telemovel", "—"),
            "documento": aluno.get("documento", "—"),
            "plano": aluno.get("plano", "—"),
            "mensalidade": mensalidade,
        }

        for chave, valor in detalhes.items():
            self._aluno_info_widgets[chave].configure(text=valor)

        caminho_foto = aluno.get("foto", "")
        if caminho_foto and caminho_foto != "sem_foto" and os.path.exists(caminho_foto):
            try:
                imagem = Image.open(caminho_foto)
                self._aluno_ctk_image = ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(180, 180))
                self.aluno_foto_label.configure(image=self._aluno_ctk_image, text="")
                return
            except Exception:
                pass

        self._aluno_ctk_image = None
        self.aluno_foto_label.configure(image=None, text="Sem foto")

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
        frame = PageFrame(self.content)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        header = PageHeader(frame, "Arquivo de Exclusão", "Alunos removidos — restauração disponível")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        btn_primary(header.actions, text="Restaurar", command=self._restaurar_aluno).pack(
            side="right", padx=4
        )
        btn_secondary(header.actions, text="Atualizar", command=self._atualizar_lista_excluidos).pack(
            side="right", padx=4
        )

        table_frame = TablePanel(frame)
        table_frame.grid(row=1, column=0, sticky="nsew")

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
        self.tree_excluidos.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=12)
        scroll.grid(row=0, column=1, sticky="ns", pady=12, padx=(0, 12))

        ctk.CTkLabel(
            frame,
            text="Alunos no arquivo são eliminados definitivamente após 60 dias.",
            text_color=TEMA["muted"],
            font=ctk.CTkFont(size=11),
        ).grid(row=2, column=0, pady=(8, 0))

        return frame

    def _atualizar_lista_excluidos(self):
        for item in self.tree_excluidos.get_children():
            self.tree_excluidos.delete(item)

        for indice, aluno in enumerate(gestao_alunos.listar_alunos_excluidos()):
            self.tree_excluidos.insert(
                "",
                "end",
                iid=f"excluido_{indice}",
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

        valores = self.tree_excluidos.item(selecao[0], "values")
        if not valores:
            messagebox.showerror("Erro", "Não foi possível identificar o aluno selecionado.")
            return

        id_aluno = int(valores[0])
        if gestao_alunos.restaurar_aluno(id_aluno):
            messagebox.showinfo("Sucesso", "Aluno restaurado com sucesso.")
            self._atualizar_lista_excluidos()
        else:
            messagebox.showerror("Erro", "Não foi possível restaurar o aluno.")

    def _criar_pagamentos(self):
        frame = PageFrame(self.content)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        header = PageHeader(frame, "Pagamentos", "Registar mensalidades e consultar histórico")
        header.actions.grid_remove()
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        form = SurfaceCard(frame)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Aluno", text_color=TEMA["muted"]).grid(
            row=0, column=0, padx=16, pady=14, sticky="e"
        )
        self.pag_aluno_var = ctk.StringVar()
        self.pag_aluno_menu = styled_option(
            form, variable=self.pag_aluno_var, values=["—"], width=280
        )
        self.pag_aluno_menu.grid(row=0, column=1, padx=10, pady=14, sticky="w")

        ctk.CTkLabel(form, text="Valor (€)", text_color=TEMA["muted"]).grid(
            row=0, column=2, padx=10, pady=14, sticky="e"
        )
        self.pag_valor_entry = styled_entry(form, width=120, placeholder_text="0.00")
        self.pag_valor_entry.grid(row=0, column=3, padx=10, pady=14, sticky="w")

        btn_primary(form, text="Registar Pagamento", command=self._registar_pagamento).grid(
            row=0, column=4, padx=16, pady=14
        )

        table_frame = TablePanel(frame)
        table_frame.grid(row=2, column=0, sticky="nsew")

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
        frame = PageFrame(self.content)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        header = PageHeader(frame, "Presenças", "Registar entradas e consultar o histórico diário")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        form = SurfaceCard(frame)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Aluno", text_color=TEMA["muted"]).grid(
            row=0, column=0, padx=16, pady=14, sticky="e"
        )
        self.pres_aluno_var = ctk.StringVar()
        self.pres_aluno_menu = styled_option(
            form, variable=self.pres_aluno_var, values=["—"], width=300
        )
        self.pres_aluno_menu.grid(row=0, column=1, padx=10, pady=14, sticky="w")

        btn_primary(
            form, text="Registar Entrada", command=self._registar_presenca
        ).grid(row=0, column=2, padx=10, pady=14)
        btn_secondary(
            form, text="Atualizar", command=self._atualizar_presencas
        ).grid(row=0, column=3, padx=(0, 16), pady=14)

        estado_card = SurfaceCard(frame)
        estado_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        estado_card.grid_columnconfigure(1, weight=1)

        self.pres_face_estado_badge = ctk.CTkLabel(
            estado_card,
            text="●",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEMA["muted"],
            width=24,
        )
        self.pres_face_estado_badge.grid(row=0, column=0, rowspan=2, padx=(18, 10), pady=16, sticky="n")

        self.pres_face_estado_titulo = ctk.CTkLabel(
            estado_card,
            text="Face ID inativo",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEMA["muted"],
            anchor="w",
        )
        self.pres_face_estado_titulo.grid(row=0, column=1, padx=(0, 18), pady=(14, 2), sticky="ew")

        self.pres_face_estado_detalhe = ctk.CTkLabel(
            estado_card,
            text="Abra a página Presenças para iniciar o reconhecimento facial.",
            font=ctk.CTkFont(size=12),
            text_color=TEMA["muted"],
            justify="left",
            anchor="w",
        )
        self.pres_face_estado_detalhe.grid(row=1, column=1, padx=(0, 18), pady=(0, 14), sticky="ew")

        table_frame = TablePanel(frame)
        table_frame.grid(row=3, column=0, sticky="nsew")

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
        frame = PageFrame(self.content)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        header = PageHeader(frame, "Câmara", "Abrir a webcam ou iniciar gravação sem sair da aplicação")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        info = SurfaceCard(frame)
        info.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        info.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            info,
            text="Controlo da Webcam",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEMA["text"],
        ).pack(padx=20, pady=(18, 8), anchor="w")
        ctk.CTkLabel(
            info,
            text="Utilize os botões abaixo para abrir a câmara ou gravar vídeo.\n"
            "As funções abrem uma janela OpenCV separada.\n\n"
            "Atalhos na janela da câmara:\n"
            "  • Modo foto: B (preto e branco), C (cor), P (capturar), Q (sair)\n"
            "  • Modo vídeo: R (iniciar gravação), S (parar), ESC (sair)",
            justify="left",
            font=ctk.CTkFont(size=13),
            text_color=TEMA["muted"],
        ).pack(padx=20, pady=(0, 18), anchor="w")

        btn_frame = SurfaceCard(frame)
        btn_frame.grid(row=2, column=0, sticky="w", pady=(0, 10))

        btn_primary(
            btn_frame,
            text="📷 Abrir Câmara",
            width=200,
            font=ctk.CTkFont(size=15),
            command=lambda: self._executar_camera(ligarCam),
        ).pack(side="left", padx=10)

        btn_secondary(
            btn_frame,
            text="🎬 Gravar Vídeo",
            width=200,
            font=ctk.CTkFont(size=15),
            command=lambda: self._executar_camera(gravarVideo),
        ).pack(side="left", padx=10)

        return frame

    def _executar_camera(self, funcao):
        threading.Thread(target=funcao, daemon=True).start()

    def _criar_administracao(self):
        frame = PageFrame(self.content)
        frame.grid_columnconfigure((0, 1), weight=1)
        frame.grid_rowconfigure(2, weight=1)

        header = PageHeader(
            frame,
            "Administração",
            "Consultar o histórico do sistema e gerir arquivos arquivados",
        )
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        btn_secondary(
            header.actions,
            text="🔄 Atualizar",
            width=130,
            command=self._carregar_historico,
        ).pack(side="left", padx=4)
        btn_primary(
            header.actions,
            text="📦 Arquivar",
            width=130,
            command=self._arquivar_historico,
        ).pack(side="left", padx=4)
        btn_secondary(
            header.actions,
            text="📂 Arquivo de Alunos",
            width=130,
            command=self._abrir_historico,
        ).pack(side="left", padx=4)

        resumo = SurfaceCard(frame)
        resumo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        resumo.grid_columnconfigure(0, weight=1)
        resumo.grid_columnconfigure(1, weight=0)

        info = ctk.CTkFrame(resumo, fg_color="transparent")
        info.grid(row=0, column=0, sticky="w", padx=18, pady=16)

        ctk.CTkLabel(
            info,
            text="Histórico do sistema",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEMA["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            info,
            text=(
                "Veja os registos atuais, abra históricos arquivados e mantenha a área "
                "organizada sem alterar os dados operacionais."
            ),
            font=ctk.CTkFont(size=12),
            text_color=TEMA["muted"],
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        acoes_secundarias = ctk.CTkFrame(resumo, fg_color="transparent")
        acoes_secundarias.grid(row=0, column=1, sticky="e", padx=18, pady=16)

        btn_secondary(
            acoes_secundarias,
            text="↻ Recarregar Lista",
            width=150,
            command=self._carregar_arquivos_historico,
        ).pack(side="left", padx=4)
        btn_danger(
            acoes_secundarias,
            text="🗑️ Excluir",
            width=120,
            command=self._excluir_historico,
        ).pack(side="left", padx=4)

        painel_historico = SurfaceCard(frame)
        painel_historico.grid(row=2, column=0, sticky="nsew", padx=(0, 6))
        painel_historico.grid_columnconfigure(0, weight=1)
        painel_historico.grid_rowconfigure(1, weight=1)

        topo_historico = ctk.CTkFrame(painel_historico, fg_color="transparent")
        topo_historico.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        topo_historico.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            topo_historico,
            text="📜 Histórico atual",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEMA["text"],
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            topo_historico,
            text="Registos recentes do sistema em tempo real.",
            font=ctk.CTkFont(size=11),
            text_color=TEMA["muted"],
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.txt_historico = ctk.CTkTextbox(
            painel_historico,
            corner_radius=12,
            border_width=1,
            border_color=TEMA["border"],
            fg_color=TEMA["input_bg"],
            font=("Consolas", 11),
        )
        self.txt_historico.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)

        painel_arquivos = TablePanel(frame)
        painel_arquivos.grid(row=2, column=1, sticky="nsew", padx=(6, 0))
        painel_arquivos.grid_columnconfigure(0, weight=1)
        painel_arquivos.grid_rowconfigure(1, weight=1)

        topo_arquivos = ctk.CTkFrame(painel_arquivos, fg_color="transparent")
        topo_arquivos.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        topo_arquivos.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            topo_arquivos,
            text="📦 Arquivos de histórico",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEMA["text"],
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            topo_arquivos,
            text="Selecione um arquivo para o abrir ou eliminar com confirmação.",
            font=ctk.CTkFont(size=11),
            text_color=TEMA["muted"],
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        table_arquivos = ctk.CTkFrame(painel_arquivos, fg_color="transparent")
        table_arquivos.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        table_arquivos.grid_columnconfigure(0, weight=1)
        table_arquivos.grid_rowconfigure(0, weight=1)

        cols = ("arquivo", "data")

        self.tree_arquivos = ttk.Treeview(
            table_arquivos,
            columns=cols,
            show="headings",
            style="Academia.Treeview",
        )

        self.tree_arquivos.heading("arquivo", text="Arquivo")
        self.tree_arquivos.heading("data", text="Data")

        self.tree_arquivos.column("arquivo", width=260)
        self.tree_arquivos.column("data", width=150, anchor="center")

        scroll = ctk.CTkScrollbar(table_arquivos, command=self.tree_arquivos.yview)

        self.tree_arquivos.configure(yscrollcommand=scroll.set)

        self.tree_arquivos.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8),
            pady=4,
        )
        scroll.grid(row=0, column=1, sticky="ns", pady=4)

        return frame

    def _carregar_historico(self):

        self.txt_historico.configure(state="normal")
        self.txt_historico.delete("1.0", "end")

        if os.path.exists(ARQUIVO_LOG):

            with open(
                ARQUIVO_LOG,
                "r",
                encoding="utf-8"
            ) as ficheiro:

                linhas = ficheiro.readlines()

                texto = ""

                for linha in linhas:

                    linha = linha.strip()

                    if not linha:
                        continue

                    partes = linha.split(" - ", 1)

                    if len(partes) == 2:

                        data = partes[0]
                        evento = partes[1]

                        texto += (
                            f"📅 {data}\n"
                            f"└── {evento}\n"
                            f"\n"
                            f"{'─'*60}\n\n"
                        )

                    else:

                        texto += linha + "\n"

                self.txt_historico.insert(
                    "1.0",
                    texto
                )
    def _carregar_arquivos_historico(self):

        pasta = PASTA_ARQUIVOS

        for item in self.tree_arquivos.get_children():
            self.tree_arquivos.delete(item)


        if not os.path.exists(pasta):
            return


        arquivos = os.listdir(pasta)


        for arquivo in arquivos:

            if arquivo.endswith(".txt"):

                data = arquivo.replace(
                    "historico_",
                    ""
                ).replace(
                    ".txt",
                    ""
                )

                self.tree_arquivos.insert(
                    "",
                    "end",
                    values=(
                        arquivo,
                        data.replace("_", " ")
                    )
                )

    def _abrir_historico(self):

        selecionado = self.tree_arquivos.selection()

        if not selecionado:
            messagebox.showinfo(
                "Arquivo",
                "Selecione um histórico arquivado."
            )
            return

        valores = self.tree_arquivos.item(
            selecionado[0],
            "values"
        )

        arquivo = valores[0]

        caminho = os.path.join(PASTA_ARQUIVOS, arquivo)

        if os.path.exists(caminho):

            with open(
                caminho,
                "r",
                encoding="utf-8"
            ) as ficheiro:

                conteudo = ficheiro.read()

            self.txt_historico.configure(state="normal")
            self.txt_historico.delete("1.0", "end")
            self.txt_historico.insert(
                "1.0",
                conteudo
            )

        else:
            messagebox.showerror(
                "Erro",
                "Arquivo não encontrado."
            )

    def _arquivar_historico(self):
        from datetime import datetime
        confirmar = messagebox.askyesno(
            "Arquivar histórico",
            "Deseja arquivar o histórico atual?\n\n"
            "Depois de arquivado, o histórico atual será limpo."
        )

        if not confirmar:
            return

        pasta = PASTA_ARQUIVOS

        os.makedirs(
            pasta,
            exist_ok=True
        )

        data = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        destino = os.path.join(
            pasta,
            f"historico_{data}.txt"
        )

        with open(
            ARQUIVO_LOG,
            "r",
            encoding="utf-8"
        ) as origem:
            conteudo = origem.read()

        with open(
            destino,
            "w",
            encoding="utf-8"
        ) as arquivo:
            arquivo.write(conteudo)

        with open(
            ARQUIVO_LOG,
            "w",
            encoding="utf-8"
        ) as origem:
            origem.write("")

        self._carregar_historico()

        messagebox.showinfo(
            "Histórico",
            "Histórico arquivado com sucesso."
        )

    def _excluir_historico(self):

        from tkinter import simpledialog

        selecionado = self.tree_arquivos.selection()

        if not selecionado:
            messagebox.showinfo(
                "Excluir histórico",
                "Selecione um arquivo de histórico."
            )
            return

        senha = simpledialog.askstring(
            "Confirmação",
            "Introduza a palavra-passe do administrador:",
            show="*"
        )

        if senha is None:
            return

        if senha != self.utilizador["senha"]:
            messagebox.showerror(
                "Erro",
                "Palavra-passe incorreta."
            )
            return

        valores = self.tree_arquivos.item(
            selecionado[0],
            "values"
        )

        arquivo = valores[0]

        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            f"Tem a certeza que pretende eliminar o arquivo:\n\n{arquivo}?"
        )

        if not confirmar:
            return

        caminho = os.path.join(PASTA_ARQUIVOS, arquivo)

        try:
            os.remove(caminho)

            self._carregar_arquivos_historico()

            messagebox.showinfo(
                "Sucesso",
                "Arquivo eliminado com sucesso."
            )

        except Exception as erro:
            messagebox.showerror(
                "Erro",
                str(erro)
            )


if __name__ == "__main__":
    from interface_grafica.main import main

    main()
  
