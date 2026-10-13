"""Componentes visuais reutilizáveis."""

import tkinter as tk
from datetime import datetime
from tkinter import ttk

import customtkinter as ctk

from interface_grafica.constants import TEMA, RAIO, RAIO_PEQ, misturar
from interface_grafica.fundo import Transparente
from interface_grafica.graficos import Anel
from interface_grafica.icones import icone, imagem as imagem_icone
from interface_grafica.utils import sem_acentos


def fonte(tamanho=13, peso="normal"):
    return ctk.CTkFont(size=tamanho, weight=peso)


# botões
# ======================================================
def botao(master, texto, comando=None, tipo="principal", icone_nome=None, **kwargs):
    if tipo == "principal":
        cores = dict(fg_color=TEMA["accent"], hover_color=TEMA["accent_hover"],
                     text_color=TEMA["on_accent"], border_width=0)
        cor_icone = TEMA["on_accent"]
    elif tipo == "perigo":
        cores = dict(fg_color=TEMA["danger_suave"], hover_color=misturar(TEMA["danger_suave"], TEMA["danger"], 0.25),
                     text_color=TEMA["danger"], border_width=0)
        cor_icone = TEMA["danger"]
    elif tipo == "fantasma":
        cores = dict(fg_color="transparent", hover_color=TEMA["surface_alt"],
                     text_color=TEMA["muted"], border_width=0)
        cor_icone = TEMA["muted"]
    else:
        cores = dict(fg_color=TEMA["surface_alt"], hover_color=TEMA["surface_hover"],
                     text_color=TEMA["text"], border_width=1, border_color=TEMA["border"])
        cor_icone = TEMA["text"]

    opcoes = dict(text=texto, command=comando, height=38, corner_radius=RAIO_PEQ,
                  font=fonte(13, "bold"), text_color_disabled=TEMA["subtle"])
    opcoes.update(cores)
    if icone_nome:
        opcoes["image"] = icone(icone_nome, cor_icone, 16)
        opcoes["compound"] = "left"
    if not texto:
        opcoes["width"] = 38
    opcoes.update(kwargs)
    return ctk.CTkButton(master, **opcoes)


def ativar(botao_ctk, ligado, tipo="principal"):
    """Liga/desliga um botão e muda a cor, para se perceber que está inativo."""
    if ligado:
        cor = {"principal": TEMA["accent"], "secundario": TEMA["surface_alt"]}.get(tipo, TEMA["accent"])
        botao_ctk.configure(state="normal", fg_color=cor)
    else:
        botao_ctk.configure(state="disabled", fg_color=TEMA["surface_alt"])


def campo(master, **kwargs):
    opcoes = dict(height=40, corner_radius=RAIO_PEQ, border_width=1,
                  border_color=TEMA["border"], fg_color=TEMA["input_bg"],
                  text_color=TEMA["text"], placeholder_text_color=TEMA["subtle"],
                  font=fonte(13))
    opcoes.update(kwargs)
    entrada = ctk.CTkEntry(master, **opcoes)
    entrada.bind("<FocusIn>", lambda _e=None: entrada.configure(border_color=TEMA["accent"]), add="+")
    entrada.bind("<FocusOut>", lambda _e=None: entrada.configure(border_color=TEMA["border"]), add="+")
    return entrada


def opcao(master, **kwargs):
    opcoes = dict(height=40, corner_radius=RAIO_PEQ, fg_color=TEMA["input_bg"],
                  button_color=TEMA["surface_alt"], button_hover_color=TEMA["surface_hover"],
                  text_color=TEMA["text"], dropdown_fg_color=TEMA["surface"],
                  dropdown_hover_color=TEMA["surface_alt"], dropdown_text_color=TEMA["text"],
                  font=fonte(13), dropdown_font=fonte(13))
    opcoes.update(kwargs)
    return ctk.CTkOptionMenu(master, **opcoes)


def rotulo(master, texto, tamanho=13, peso="normal", cor=None, **kwargs):
    return ctk.CTkLabel(master, text=texto, font=fonte(tamanho, peso),
                        text_color=cor or TEMA["text"], **kwargs)


def ponto(master, cor, tamanho=10):
    return ctk.CTkFrame(master, width=tamanho, height=tamanho, corner_radius=tamanho // 2,
                        fg_color=cor, border_width=0)


def etiqueta(master, texto, cor):
    """Pequena 'pill' colorida (estado, plano...)."""
    return ctk.CTkLabel(master, text=texto, font=fonte(11, "bold"), text_color=cor,
                        fg_color=misturar(TEMA["surface"], cor, 0.14), corner_radius=8,
                        height=24, padx=10)


def segmentos(master, valores, comando, **kwargs):
    opcoes = dict(values=valores, command=comando, height=34, corner_radius=RAIO_PEQ,
                  fg_color=TEMA["surface_alt"], selected_color=TEMA["seg_sel"],
                  selected_hover_color=TEMA["seg_sel"], unselected_color=TEMA["surface_alt"],
                  unselected_hover_color=TEMA["surface_hover"], text_color=TEMA["text"],
                  font=fonte(12, "bold"))
    opcoes.update(kwargs)
    return ctk.CTkSegmentedButton(master, **opcoes)


class Cartao(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", TEMA["surface"])
        kwargs.setdefault("corner_radius", RAIO)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", TEMA["border"])
        super().__init__(master, **kwargs)


class Pagina(Transparente):
    """Página: mostra o degradê do painel por trás dos cartões."""
    titulo = ""
    subtitulo = ""
    so_admin = False

    def __init__(self, app):
        super().__init__(app.conteudo, app.fundo)
        self.app = app

    def zona(self):
        """Contentor 'transparente' (barras de ferramentas, colunas)."""
        return Transparente(self, self.app.fundo)

    def ao_mostrar(self):
        pass

    def ao_esconder(self):
        pass


def titulo_cartao(master, texto, subtitulo=None):
    caixa = ctk.CTkFrame(master, fg_color="transparent")
    rotulo(caixa, texto, 15, "bold").pack(anchor="w")
    if subtitulo:
        rotulo(caixa, subtitulo, 12, cor=TEMA["muted"]).pack(anchor="w")
    return caixa


# pesquisa com atraso (não refaz a lista a cada tecla)
# ======================================================
class CampoPesquisa(ctk.CTkFrame):
    def __init__(self, master, ao_mudar, texto="Pesquisar...", largura=260):
        super().__init__(master, fg_color=TEMA["input_bg"], corner_radius=RAIO_PEQ,
                         border_width=1, border_color=TEMA["border"], height=40, width=largura)
        self.ao_mudar = ao_mudar
        self._job = None
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text="", image=icone("pesquisa", TEMA["subtle"], 16), width=20).grid(
            row=0, column=0, padx=(12, 4), pady=6)
        self.entrada = ctk.CTkEntry(self, placeholder_text=texto, border_width=0, fg_color="transparent",
                                    text_color=TEMA["text"], placeholder_text_color=TEMA["subtle"],
                                    font=fonte(13), height=32, width=largura - 50)
        self.entrada.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=3)
        self.entrada.bind("<KeyRelease>", self._agendar)
        self.entrada.bind("<FocusIn>", lambda _e=None: self.configure(border_color=TEMA["accent"]))
        self.entrada.bind("<FocusOut>", lambda _e=None: self.configure(border_color=TEMA["border"]))

    def _agendar(self, _e=None):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(160, self._disparar)

    def _disparar(self):
        self._job = None
        self.ao_mudar()

    def destroy(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        super().destroy()

    def get(self):
        return sem_acentos(self.entrada.get().strip())


# tabela
# ======================================================
def estilo_tabela():
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.layout("FC.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    estilo.configure("FC.Treeview", background=TEMA["surface"], fieldbackground=TEMA["surface"],
                     foreground=TEMA["text"], rowheight=40, borderwidth=0, relief="flat",
                     font=("Segoe UI", 10))
    estilo.configure("FC.Treeview.Heading", background=TEMA["surface"], foreground=TEMA["subtle"],
                     borderwidth=0, relief="flat", font=("Segoe UI", 9, "bold"), padding=(10, 10))
    estilo.map("FC.Treeview.Heading", background=[("active", TEMA["surface"])],
               foreground=[("active", TEMA["text"])])
    estilo.map("FC.Treeview", background=[("selected", TEMA["table_select"])],
               foreground=[("selected", TEMA["text"])])


def _chave_ordenacao(valor):
    texto = str(valor)
    try:
        return (0, float(texto.replace("€", "").replace(" ", "").replace(",", ".")))
    except ValueError:
        pass
    for formato in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%H:%M"):
        try:
            return (1, datetime.strptime(texto, formato).timestamp())
        except ValueError:
            pass
    return (2, sem_acentos(texto))


class Tabela(ctk.CTkFrame):
    """Treeview com linhas alternadas, realce ao passar o rato,
    ordenação ao clicar no cabeçalho e mensagem quando está vazia."""

    def __init__(self, master, colunas, vazio="Sem registos."):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.colunas = [c[0] for c in colunas]
        self._linhas = []
        self._hover = None
        self._ordem = (None, False)

        self.tree = ttk.Treeview(self, columns=self.colunas, show="headings", style="FC.Treeview",
                                 selectmode="browse")
        self._larguras = {}
        self._largura_aplicada = None
        for chave, titulo, largura, ancora in colunas:
            self.tree.heading(chave, text=titulo.upper(), anchor=ancora,
                              command=lambda c=chave: self._ordenar(c))
            self.tree.column(chave, width=largura, minwidth=30, anchor=ancora, stretch=True)
            self._larguras[chave] = largura
        # o Treeview não encolhe as colunas sozinho; reparte-se o espaço disponível
        self.tree.bind("<Configure>", self._repartir, add="+")

        self.tree.tag_configure("impar", background=TEMA["table_alt"])
        self.tree.tag_configure("hover", background=TEMA["surface_hover"])
        self.tree.tag_configure("perigo", foreground=TEMA["danger"])
        self.tree.tag_configure("aviso", foreground=TEMA["warning"])

        barra = ctk.CTkScrollbar(self, command=self.tree.yview, button_color=TEMA["border_forte"],
                                 button_hover_color=TEMA["subtle"], fg_color="transparent")
        self.tree.configure(yscrollcommand=barra.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns", padx=(4, 0))

        self.lbl_vazio = ctk.CTkLabel(self, text=vazio, font=fonte(13), text_color=TEMA["subtle"],
                                      fg_color=TEMA["surface"])
        self.tree.bind("<Motion>", self._mover)
        self.tree.bind("<Leave>", lambda _e=None: self._tirar_hover())

    def _repartir(self, evento):
        total = sum(self._larguras.values())
        if evento.width < 50 or not total or evento.width == self._largura_aplicada:
            return
        self._largura_aplicada = evento.width
        # a soma tem de dar exatamente a largura (com arredondamentos a tabela
        # pedia mais 1 px, o layout mudava e entrava num ciclo de redesenho)
        chaves = list(self._larguras)
        usado = 0
        for chave in chaves[:-1]:
            largura = int(self._larguras[chave] * evento.width / total)
            self.tree.column(chave, width=largura)
            usado += largura
        self.tree.column(chaves[-1], width=max(evento.width - usado, 30))

    def preencher(self, linhas):
        """linhas = [(iid, valores, tags_extra)]"""
        self._linhas = list(linhas)
        coluna, invertido = self._ordem
        if coluna:
            indice = self.colunas.index(coluna)
            self._linhas.sort(key=lambda l: _chave_ordenacao(l[1][indice]), reverse=invertido)
        self._mostrar()

    def _mostrar(self):
        selecionado = self.selecionado()
        self._hover = None
        self.tree.delete(*self.tree.get_children())
        for n, (iid, valores, extra) in enumerate(self._linhas):
            tags = list(extra or [])
            if n % 2:
                tags.append("impar")
            self.tree.insert("", "end", iid=iid, values=valores, tags=tags)
        if selecionado and self.tree.exists(selecionado):
            self.tree.selection_set(selecionado)
            self.tree.see(selecionado)
        if self._linhas:
            self.lbl_vazio.place_forget()
        else:
            self.lbl_vazio.place(relx=0.5, rely=0.5, anchor="center")

    def _ordenar(self, coluna):
        atual, invertido = self._ordem
        invertido = not invertido if atual == coluna else False
        self._ordem = (coluna, invertido)
        for c in self.colunas:
            texto = self.tree.heading(c, "text").rstrip(" ▲▼")
            if c == coluna:
                texto += " ▼" if invertido else " ▲"
            self.tree.heading(c, text=texto)
        self.preencher(self._linhas)

    def _mover(self, evento):
        linha = self.tree.identify_row(evento.y)
        if linha == self._hover:
            return
        self._tirar_hover()
        if linha:
            tags = list(self.tree.item(linha, "tags"))
            self.tree.item(linha, tags=tags + ["hover"])
            self._hover = linha

    def _tirar_hover(self):
        if self._hover and self.tree.exists(self._hover):
            tags = [t for t in self.tree.item(self._hover, "tags") if t != "hover"]
            self.tree.item(self._hover, tags=tags)
        self._hover = None

    def selecionado(self):
        selecao = self.tree.selection()
        return selecao[0] if selecao else None

    def ao_selecionar(self, funcao):
        self.tree.bind("<<TreeviewSelect>>", lambda _e=None: funcao(), add="+")

    def ao_duplo_clique(self, funcao):
        self.tree.bind("<Double-1>", lambda _e=None: funcao() if self.selecionado() else None, add="+")


# cartão de métrica (pill com anel)
# ======================================================
class CartaoMetrica(Cartao):
    def __init__(self, master, titulo, cor, icone_nome=None, euros=False):
        super().__init__(master, corner_radius=26)
        self.euros = euros
        self._estreito = False
        self._alvo = 0.0
        self._mostrado = 0.0
        self._job = None
        self.grid_columnconfigure(1, weight=1)

        self.anel = Anel(self, tamanho=60, cor=cor, fundo=TEMA["surface"], fonte=("Segoe UI", 9, "bold"))
        self.anel.grid(row=0, column=0, rowspan=2, padx=(14, 12), pady=14)
        if icone_nome:
            self.anel.definir_icone(imagem_icone(icone_nome, cor, 64))

        self.lbl_valor = rotulo(self, "0", 24, "bold")
        self.lbl_valor.grid(row=0, column=1, sticky="sw", padx=(0, 14), pady=(14, 0))
        self.lbl_titulo = rotulo(self, titulo, 12, cor=TEMA["muted"])
        self.lbl_titulo.grid(row=1, column=1, sticky="nw", padx=(0, 14), pady=(0, 14))
        self.bind("<Configure>", self._ajustar, add="+")

    def _ajustar(self, _evento=None):
        # em janelas estreitas o anel sai para o número caber
        estreito = self.winfo_width() < 215 * self._get_widget_scaling()
        if estreito == self._estreito:
            return
        self._estreito = estreito
        if estreito:
            self.anel.grid_remove()
            self.lbl_valor.grid_configure(padx=18)
            self.lbl_titulo.grid_configure(padx=18)
        else:
            self.anel.grid()
            self.lbl_valor.grid_configure(padx=(0, 14))
            self.lbl_titulo.grid_configure(padx=(0, 14))

    def definir(self, valor, fracao=None):
        self._alvo = float(valor or 0)
        if fracao is not None:
            self.anel.definir(fracao)
        if self._job:
            self.after_cancel(self._job)
        self._passo()

    def _passo(self):
        diferenca = self._alvo - self._mostrado
        if abs(diferenca) < 0.05:
            self._mostrado = self._alvo
            self._escrever()
            self._job = None
            return
        self._mostrado += diferenca * 0.2
        self._escrever()
        self._job = self.after(16, self._passo)

    def _escrever(self):
        if self.euros:
            texto = f"{int(round(self._mostrado)):,}".replace(",", " ")
            self.lbl_valor.configure(text=f"{texto} €")
        else:
            self.lbl_valor.configure(text=str(int(round(self._mostrado))))

    def destroy(self):
        if self._job:
            self.after_cancel(self._job)
        super().destroy()


# seletor de aluno com pesquisa (substitui o menu com centenas de nomes)
# ======================================================
_seletores = []


def fechar_listas():
    """Fecha as listas de sugestões abertas (ao mudar de página)."""
    for seletor in list(_seletores):
        try:
            if seletor.winfo_exists():
                seletor._fechar(forcar=True)
                continue
        except Exception:
            # o widget pertence a uma janela já destruída (logout): o
            # winfo_exists rebenta em vez de devolver False
            pass
        try:
            _seletores.remove(seletor)
        except ValueError:
            pass


class SeletorAluno(ctk.CTkFrame):
    def __init__(self, master, obter_alunos, texto="Escreva o nome do aluno...", ao_escolher=None):
        super().__init__(master, fg_color="transparent")
        self.obter_alunos = obter_alunos
        self.ao_escolher = ao_escolher
        self.id_escolhido = None
        self._opcoes = []
        self._popup = None
        _seletores.append(self)
        self.grid_columnconfigure(0, weight=1)

        self.entrada = campo(self, placeholder_text=texto)
        self.entrada.grid(row=0, column=0, sticky="ew")
        self.entrada.bind("<KeyRelease>", self._tecla)
        self.entrada.bind("<FocusIn>", lambda _e=None: self.after(10, self._abrir), add="+")
        self.entrada.bind("<FocusOut>", lambda _e=None: self.after(180, self._fechar), add="+")
        self.entrada.bind("<Down>", lambda _e=None: self._mover(1))
        self.entrada.bind("<Up>", lambda _e=None: self._mover(-1))
        self.entrada.bind("<Return>", lambda _e=None: self._confirmar())
        self.entrada.bind("<Escape>", lambda _e=None: self._fechar())
        # ao mudar de página a lista não pode ficar a flutuar por cima
        self.bind("<Unmap>", lambda _e=None: self._fechar(forcar=True), add="+")

    def get(self):
        return self.id_escolhido

    def limpar(self):
        self.id_escolhido = None
        self.entrada.delete(0, "end")

    def _filtrar(self):
        termo = sem_acentos(self.entrada.get().strip())
        lista = []
        for aluno in self.obter_alunos():
            if not termo or termo in sem_acentos(aluno["nome"]) or termo == str(aluno["id"]):
                lista.append(aluno)
            if len(lista) >= 60:
                break
        return lista

    def _tecla(self, evento):
        if evento.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return
        self.id_escolhido = None
        self._abrir()

    def _abrir(self):
        # só abre se o campo estiver mesmo visível e com o foco
        if not self.winfo_exists() or not self.winfo_viewable() or self.focus_get() != self.entrada._entry:
            return
        self._opcoes = self._filtrar()
        if self._popup is None or not self._popup.winfo_exists():
            self._popup = tk.Toplevel(self)
            self._popup.overrideredirect(True)
            self._popup.configure(bg=TEMA["border"])
            self._lista = tk.Listbox(
                self._popup, bd=0, highlightthickness=0, activestyle="none",
                bg=TEMA["surface"], fg=TEMA["text"], selectbackground=TEMA["table_select"],
                selectforeground=TEMA["text"], font=("Segoe UI", 10), relief="flat")
            self._lista.pack(fill="both", expand=True, padx=1, pady=1)
            self._lista.bind("<ButtonRelease-1>", lambda _e=None: self._confirmar())
        self._lista.delete(0, "end")
        if not self._opcoes:
            self._lista.insert("end", "  Nenhum aluno encontrado")
        for aluno in self._opcoes:
            self._lista.insert("end", f"  {aluno['nome']}   ·  #{aluno['id']}")
        if self._opcoes:
            self._lista.selection_set(0)
        altura = min(max(len(self._opcoes), 1), 7) * 26 + 4
        x = self.entrada.winfo_rootx()
        y = self.entrada.winfo_rooty() + self.entrada.winfo_height() + 4
        self._popup.geometry(f"{self.entrada.winfo_width()}x{altura}+{x}+{y}")
        self._popup.lift()

    def _mover(self, direcao):
        if not self._popup or not self._opcoes:
            return
        atual = self._lista.curselection()
        indice = (atual[0] if atual else -1) + direcao
        indice = max(0, min(len(self._opcoes) - 1, indice))
        self._lista.selection_clear(0, "end")
        self._lista.selection_set(indice)
        self._lista.see(indice)

    def _confirmar(self):
        if not self._popup or not self._opcoes:
            return
        atual = self._lista.curselection()
        if not atual:
            return
        aluno = self._opcoes[atual[0]]
        self.id_escolhido = aluno["id"]
        self.entrada.delete(0, "end")
        self.entrada.insert(0, aluno["nome"])
        self._fechar(forcar=True)
        if self.ao_escolher:
            self.ao_escolher(aluno["id"])

    def _fechar(self, forcar=False):
        try:
            if self._popup is not None and self._popup.winfo_exists():
                if not forcar and self.focus_get() == self.entrada._entry:
                    return
                self._popup.destroy()
        except Exception:
            # a janela do popup pode já ter morrido com a janela principal
            pass
        self._popup = None

    def destroy(self):
        try:
            _seletores.remove(self)
        except ValueError:
            pass
        super().destroy()


# avisos rápidos (toast) no canto da janela
# ======================================================
def toast(janela, texto, tipo="sucesso", duracao=3200):
    raiz = janela.winfo_toplevel()
    anterior = getattr(raiz, "_toast_atual", None)
    if anterior is not None and anterior.winfo_exists():
        anterior.destroy()

    cores = {"sucesso": TEMA["accent"], "erro": TEMA["danger"], "aviso": TEMA["warning"], "info": TEMA["cyan"]}
    icones_tipo = {"sucesso": "visto", "erro": "alerta", "aviso": "alerta", "info": "info"}
    cor = cores.get(tipo, TEMA["accent"])

    caixa = ctk.CTkFrame(raiz, fg_color=TEMA["surface_alt"], corner_radius=14,
                         border_width=1, border_color=misturar(TEMA["surface_alt"], cor, 0.5))
    ctk.CTkLabel(caixa, text="", image=icone(icones_tipo.get(tipo, "info"), cor, 18)).pack(
        side="left", padx=(14, 8), pady=12)
    ctk.CTkLabel(caixa, text=texto, font=fonte(13), text_color=TEMA["text"], wraplength=340,
                 justify="left").pack(side="left", padx=(0, 16), pady=12)
    raiz._toast_atual = caixa

    def animar(y):
        if not caixa.winfo_exists():
            return
        caixa.place(relx=1.0, rely=1.0, x=-24, y=y, anchor="se")
        caixa.lift()
        if y > -24:
            caixa.after(12, lambda: animar(y - 6))

    animar(36)
    caixa.after(duracao, lambda: caixa.destroy() if caixa.winfo_exists() else None)
    caixa.bind("<Button-1>", lambda _e=None: caixa.destroy())


# janelas modais
# ======================================================
class Janela(ctk.CTkToplevel):
    def __init__(self, master, titulo, largura, altura):
        super().__init__(master)
        self.withdraw()
        self.title(titulo)
        self.configure(fg_color=TEMA["bg"])
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.resultado = None
        self.protocol("WM_DELETE_WINDOW", self.fechar)
        self.bind("<Escape>", lambda _e=None: self.fechar())
        self._largura, self._altura = largura, altura

    def mostrar(self):
        mestre = self.master.winfo_toplevel()
        self.update_idletasks()
        escala = self._get_window_scaling() if hasattr(self, "_get_window_scaling") else 1
        w, h = int(self._largura * escala), int(self._altura * escala)
        x = mestre.winfo_rootx() + (mestre.winfo_width() - w) // 2
        y = mestre.winfo_rooty() + (mestre.winfo_height() - h) // 2
        self.geometry(f"{self._largura}x{self._altura}+{max(x, 0)}+{max(y, 0)}")
        from interface_grafica.janela import preparar_janela
        preparar_janela(self, principal=False)
        self.deiconify()
        self.lift()
        self.focus_force()
        self.after(60, self._prender)

    def _prender(self):
        try:
            self.grab_set()
        except tk.TclError:
            self.after(100, self._prender)

    def fechar(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    def esperar(self):
        self.mostrar()
        self.master.wait_window(self)
        return self.resultado


def _cabecalho_modal(janela, titulo, texto, icone_nome, cor):
    caixa = Cartao(janela)
    caixa.pack(fill="both", expand=True, padx=16, pady=16)
    topo = ctk.CTkFrame(caixa, fg_color="transparent")
    topo.pack(fill="x", padx=22, pady=(22, 0))
    ctk.CTkLabel(topo, text="", image=icone(icone_nome, cor, 22), width=44, height=44,
                 fg_color=misturar(TEMA["surface"], cor, 0.14), corner_radius=14).pack(side="left")
    rotulo(topo, titulo, 17, "bold").pack(side="left", padx=14)
    if texto:
        rotulo(caixa, texto, 13, cor=TEMA["muted"], wraplength=380, justify="left").pack(
            fill="x", padx=22, pady=(14, 0))
    return caixa


def confirmar(master, titulo, texto, perigo=False, texto_botao="Confirmar"):
    janela = Janela(master, titulo, 460, 250)
    cor = TEMA["danger"] if perigo else TEMA["accent"]
    caixa = _cabecalho_modal(janela, titulo, texto, "alerta" if perigo else "info", cor)
    barra = ctk.CTkFrame(caixa, fg_color="transparent")
    barra.pack(side="bottom", fill="x", padx=22, pady=20)

    def sim():
        janela.resultado = True
        janela.fechar()

    if perigo:
        botao(barra, texto_botao, sim, "principal", fg_color=TEMA["danger"], hover_color=TEMA["danger_hover"],
              text_color="#ffffff").pack(side="right")
    else:
        botao(barra, texto_botao, sim).pack(side="right")
    botao(barra, "Cancelar", janela.fechar, "secundario").pack(side="right", padx=8)
    janela.bind("<Return>", lambda _e=None: sim())
    return bool(janela.esperar())


def mensagem(master, titulo, texto, tipo="info"):
    cores = {"erro": TEMA["danger"], "aviso": TEMA["warning"], "info": TEMA["cyan"], "sucesso": TEMA["accent"]}
    altura = 230 + 18 * (texto.count("\n") + len(texto) // 60)
    janela = Janela(master, titulo, 460, min(altura, 520))
    caixa = _cabecalho_modal(janela, titulo, texto, "alerta" if tipo in ("erro", "aviso") else "info",
                             cores.get(tipo, TEMA["cyan"]))
    barra = ctk.CTkFrame(caixa, fg_color="transparent")
    barra.pack(side="bottom", fill="x", padx=22, pady=20)
    botao(barra, "OK", janela.fechar, width=110).pack(side="right")
    janela.bind("<Return>", lambda _e=None: janela.fechar())
    janela.esperar()


def pedir_senha(master, titulo, texto):
    janela = Janela(master, titulo, 460, 320)
    caixa = _cabecalho_modal(janela, titulo, texto, "cadeado", TEMA["danger"])
    entrada = campo(caixa, show="•", placeholder_text="Palavra-passe do administrador")
    entrada.pack(fill="x", padx=22, pady=(16, 0))
    barra = ctk.CTkFrame(caixa, fg_color="transparent")
    barra.pack(side="bottom", fill="x", padx=22, pady=20)

    def ok():
        janela.resultado = entrada.get()
        janela.fechar()

    botao(barra, "Confirmar", ok, fg_color=TEMA["danger"], hover_color=TEMA["danger_hover"],
          text_color="#ffffff").pack(side="right")
    botao(barra, "Cancelar", janela.fechar, "secundario").pack(side="right", padx=8)
    entrada.bind("<Return>", lambda _e=None: ok())
    janela.after(150, entrada.focus_set)
    return janela.esperar()


# alternar tema (sol / lua)
# ======================================================
class AlternadorTema(ctk.CTkFrame):
    def __init__(self, master, comando, escuro):
        super().__init__(master, fg_color=TEMA["surface_alt"], corner_radius=20,
                         border_width=1, border_color=TEMA["border"], height=40)
        self.comando = comando
        self._clicado = False
        for nome, ativo in (("lua", escuro), ("sol", not escuro)):
            cor = TEMA["on_accent"] if ativo else TEMA["muted"]
            ctk.CTkButton(self, text="", image=icone(nome, cor, 16), width=34, height=30, corner_radius=16,
                          fg_color=TEMA["accent"] if ativo else "transparent",
                          hover_color=TEMA["accent_hover"] if ativo else TEMA["surface_hover"],
                          command=None if ativo else self._trocar).pack(side="left", padx=3, pady=4)
        # clicar em qualquer parte da 'pill' também troca
        self.bind("<Button-1>", lambda _e=None: self._trocar())
        self.configure(cursor="hand2")

    def _trocar(self):
        # evita duplo clique a reconstruir a janela duas vezes
        if self._clicado:
            return
        self._clicado = True
        self.after(10, self.comando)


# linha de LEDs (widget)
# ======================================================
class Leds(tk.Canvas):
    def __init__(self, master, largura, altura, fundo=None):
        from interface_grafica.graficos import escala_de
        self.escala = escala_de(master)
        self.largura, self.altura = int(largura * self.escala), int(altura * self.escala)
        self.fundo = fundo or TEMA["surface"]
        super().__init__(master, width=self.largura, height=self.altura, highlightthickness=0, bd=0, bg=self.fundo)
        self._foto = None

    def _mostrar(self, desenhar):
        from PIL import Image, ImageTk
        from interface_grafica import desenho
        img = Image.new("RGBA", (self.largura, self.altura), desenho.rgb(self.fundo) + (255,))
        desenhar(img, desenho)
        self._foto = ImageTk.PhotoImage(img)
        self.delete("all")
        self.create_image(0, 0, image=self._foto, anchor="nw")

    def definir(self, cores):
        apagado = misturar(self.fundo, TEMA["border_forte"], 0.85)
        self._mostrar(lambda img, d: d.leds(img, 0, 0, self.largura, self.altura, cores, apagado))

    def equalizador(self, valores, cor, niveis=4):
        apagado = misturar(self.fundo, TEMA["border_forte"], 0.85)
        self._mostrar(lambda img, d: d.equalizador(img, 0, 0, self.largura, self.altura, valores, cor, apagado, niveis))
