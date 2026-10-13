"""Janelas de diálogo."""

import os
import threading
from datetime import datetime

import customtkinter as ctk

from interface_grafica.camera_ui import LeitorCamera, VisorCamera
from interface_grafica.constants import PLANOS, TEMA, misturar
from interface_grafica.icones import icone
from interface_grafica.termos import TERMOS_TEXTO, POLITICA_PRIVACIDADE, CONSENTIMENTO_FACIAL
from interface_grafica.utils import tem_foto
from interface_grafica.widgets import (
    Cartao, Janela, ativar, botao, campo, confirmar, fonte, opcao, rotulo, segmentos,
)
from modulos import notificacoes, relatorios
from projeto_ginasio import Camara
from projeto_ginasio.config import PASTA_CAPTURAS


def _texto_longo(master, texto, altura=300):
    caixa = ctk.CTkTextbox(master, height=altura, corner_radius=12, border_width=1,
                           border_color=TEMA["border"], fg_color=TEMA["input_bg"],
                           text_color=TEMA["text"], font=fonte(12), wrap="word")
    caixa.insert("1.0", texto)
    caixa.configure(state="disabled")
    return caixa


# termos e política de privacidade
# ======================================================
class DialogoTermos(Janela):
    """Com aceitar=True obriga a escolher aceitar/recusar (resultado True/False)."""

    def __init__(self, master, aceitar=True):
        super().__init__(master, "Termos e Privacidade", 640, 640)
        self.resultado = False
        cartao = Cartao(self)
        cartao.pack(fill="both", expand=True, padx=16, pady=16)

        topo = ctk.CTkFrame(cartao, fg_color="transparent")
        topo.pack(fill="x", padx=22, pady=(20, 10))
        ctk.CTkLabel(topo, text="", image=icone("privacidade", TEMA["accent"], 22), width=44, height=44,
                     fg_color=TEMA["accent_suave"], corner_radius=14).pack(side="left")
        textos = ctk.CTkFrame(topo, fg_color="transparent")
        textos.pack(side="left", padx=14)
        rotulo(textos, "Termos e Política de Privacidade", 17, "bold").pack(anchor="w")
        rotulo(textos, "Leia com atenção antes de continuar." if aceitar else "Versão em vigor.",
               12, cor=TEMA["muted"]).pack(anchor="w")

        self.abas = segmentos(cartao, ["Termos de Utilização", "Política de Privacidade"], self._trocar)
        self.abas.pack(fill="x", padx=22, pady=(4, 10))
        self.abas.set("Termos de Utilização")

        self.caixa = _texto_longo(cartao, TERMOS_TEXTO, 330)
        self.caixa.pack(fill="both", expand=True, padx=22)

        barra = ctk.CTkFrame(cartao, fg_color="transparent")
        barra.pack(fill="x", padx=22, pady=18)

        if aceitar:
            self.var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(barra, text="Li e aceito os Termos e a Política de Privacidade",
                            variable=self.var, command=self._verificar, font=fonte(12),
                            text_color=TEMA["text"], fg_color=TEMA["accent"],
                            hover_color=TEMA["accent_hover"], checkmark_color=TEMA["on_accent"],
                            border_color=TEMA["border_forte"], corner_radius=6).pack(anchor="w", pady=(0, 14))
            linha = ctk.CTkFrame(barra, fg_color="transparent")
            linha.pack(fill="x")
            self.btn_aceitar = botao(linha, "Aceitar e continuar", self._aceitar)
            ativar(self.btn_aceitar, False)
            self.btn_aceitar.pack(side="right")
            botao(linha, "Recusar", self.fechar, "secundario").pack(side="right", padx=8)
        else:
            botao(barra, "Fechar", self.fechar, width=120).pack(side="right")

    def _trocar(self, valor):
        texto = TERMOS_TEXTO if valor == "Termos de Utilização" else POLITICA_PRIVACIDADE
        self.caixa.configure(state="normal")
        self.caixa.delete("1.0", "end")
        self.caixa.insert("1.0", texto)
        self.caixa.configure(state="disabled")

    def _verificar(self):
        ativar(self.btn_aceitar, self.var.get())

    def _aceitar(self):
        self.resultado = True
        self.fechar()


# captura de foto dentro da aplicação
# ======================================================
class CapturaFoto(Janela):
    """Devolve o caminho de uma foto temporária ou None."""

    def __init__(self, master, nome=""):
        super().__init__(master, "Fotografia do aluno", 560, 600)
        self.leitor = LeitorCamera(detetar=True)
        self.frame_capturado = None

        cartao = Cartao(self)
        cartao.pack(fill="both", expand=True, padx=16, pady=16)
        rotulo(cartao, "Fotografia para o Face ID", 17, "bold").pack(anchor="w", padx=22, pady=(20, 0))
        rotulo(cartao, f"Centre o rosto de {nome or 'aluno'} e olhe de frente para a câmara.",
               12, cor=TEMA["muted"]).pack(anchor="w", padx=22)

        moldura = ctk.CTkFrame(cartao, fg_color=TEMA["surface_alt"], corner_radius=16)
        moldura.pack(fill="both", expand=True, padx=22, pady=14)
        self.visor = VisorCamera(moldura, texto_vazio="A ligar a câmara...")
        self.visor.pack(fill="both", expand=True, padx=6, pady=6)

        self.lbl_estado = rotulo(cartao, "", 12, cor=TEMA["muted"])
        self.lbl_estado.pack(anchor="w", padx=22)

        barra = ctk.CTkFrame(cartao, fg_color="transparent")
        barra.pack(fill="x", padx=22, pady=(10, 20))
        self.btn_principal = botao(barra, "Capturar", self._capturar, icone_nome="camara", width=150)
        self.btn_principal.pack(side="right")
        self.btn_repetir = botao(barra, "Repetir", self._repetir, "secundario", icone_nome="atualizar")
        botao(barra, "Cancelar", self.fechar, "fantasma").pack(side="left")

        # vai carregando o modelo facial enquanto a pessoa se posiciona
        threading.Thread(target=_pre_carregar_modelo, daemon=True).start()

        self.leitor.iniciar()
        self.visor.ligar(self.leitor.obter)
        self.after(400, self._vigiar)

    def _vigiar(self):
        if not self.winfo_exists() or self.frame_capturado is not None:
            return
        if self.leitor.erro:
            self.visor.desligar(self.leitor.erro + "\nVerifique a câmara na página Câmara.")
            self.btn_principal.configure(state="disabled")
            return
        _n, _frame, rostos = self.leitor.obter()
        if rostos:
            self.lbl_estado.configure(text="Rosto detetado. Pode capturar.", text_color=TEMA["accent"])
        else:
            self.lbl_estado.configure(text="À procura de um rosto...", text_color=TEMA["muted"])
        self.after(250, self._vigiar)

    def _capturar(self):
        _n, frame, _rostos = self.leitor.obter()
        if frame is None:
            return
        self.frame_capturado = frame.copy()
        self.visor.congelar()
        self.lbl_estado.configure(text="Foto tirada. Está boa?", text_color=TEMA["text"])
        self.btn_principal.configure(text="Usar esta foto", command=self._usar, image=icone("visto", TEMA["on_accent"], 16))
        self.btn_repetir.pack(side="right", padx=8)

    def _repetir(self):
        self.frame_capturado = None
        self.btn_repetir.pack_forget()
        self.btn_principal.configure(text="Capturar", command=self._capturar, image=icone("camara", TEMA["on_accent"], 16))
        self.visor.ligar(self.leitor.obter)
        self._vigiar()

    def _usar(self):
        caminho = os.path.join(PASTA_CAPTURAS, f"registo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
        if Camara.guardar_imagem(caminho, self.frame_capturado):
            self.resultado = caminho
        self.fechar()

    def fechar(self):
        self.visor.desligar()
        self.leitor.parar()
        super().fechar()


def _pre_carregar_modelo():
    try:
        from projeto_ginasio.reconhecimento.reconhecimento import carregar_modelo
        carregar_modelo()
    except Exception as erro:
        print(f"Modelo facial não carregado: {erro}")


# aluno
# ======================================================
class AlunoFormDialog(Janela):
    """callback(nome, telemovel, documento, plano, foto, remover_foto)"""

    def __init__(self, master, titulo, callback, aluno=None):
        super().__init__(master, titulo, 560, 640 if aluno else 600)
        self.callback = callback
        self.aluno = aluno

        cartao = Cartao(self)
        cartao.pack(fill="both", expand=True, padx=16, pady=16)
        cartao.grid_columnconfigure((0, 1), weight=1)

        rotulo(cartao, titulo, 18, "bold").grid(row=0, column=0, columnspan=2, sticky="w", padx=24, pady=(22, 0))
        rotulo(cartao, "Os campos marcados são obrigatórios.", 12, cor=TEMA["muted"]).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=24, pady=(0, 14))

        self.entradas = {}
        campos = [
            ("nome", "Nome completo *", "Nome e apelido", 2, 0, 2),
            ("telemovel", "Telemóvel *", "9 dígitos", 4, 0, 1),
            ("documento", "Documento *", "Máx. 12 caracteres", 4, 1, 1),
        ]
        for chave, texto, dica, linha, coluna, largura in campos:
            rotulo(cartao, texto, 12, cor=TEMA["muted"]).grid(
                row=linha, column=coluna, columnspan=largura, sticky="w",
                padx=(24 if coluna == 0 else 8, 24 if coluna + largura == 2 else 8))
            entrada = campo(cartao, placeholder_text=dica)
            entrada.grid(row=linha + 1, column=coluna, columnspan=largura, sticky="ew",
                         padx=(24 if coluna == 0 else 8, 24 if coluna + largura == 2 else 8), pady=(4, 12))
            self.entradas[chave] = entrada

        rotulo(cartao, "Plano *", 12, cor=TEMA["muted"]).grid(row=6, column=0, columnspan=2, sticky="w", padx=24)
        self.plano = segmentos(cartao, PLANOS, None)
        self.plano.grid(row=7, column=0, columnspan=2, sticky="ew", padx=24, pady=(4, 14))
        self.plano.set(PLANOS[1])

        # consentimento facial (RGPD art. 9.º)
        caixa_rgpd = ctk.CTkFrame(cartao, fg_color=TEMA["surface_alt"], corner_radius=14)
        caixa_rgpd.grid(row=8, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 8))
        caixa_rgpd.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(caixa_rgpd, text="", image=icone("rosto", TEMA["accent"], 20)).grid(
            row=0, column=0, rowspan=2, padx=(14, 10), pady=14, sticky="n")

        self.var_foto = ctk.BooleanVar(value=False)
        self.var_remover = ctk.BooleanVar(value=False)
        com_foto = aluno is not None and tem_foto(aluno)

        if com_foto:
            texto_switch = "Tirar uma nova fotografia"
        else:
            texto_switch = "Consentimento para reconhecimento facial"
        ctk.CTkSwitch(caixa_rgpd, text=texto_switch, variable=self.var_foto, font=fonte(13, "bold"),
                      text_color=TEMA["text"], progress_color=TEMA["accent"], button_color="#ffffff",
                      fg_color=TEMA["border_forte"], command=self._trocou_foto).grid(
            row=0, column=1, sticky="w", pady=(14, 0), padx=(0, 14))
        rotulo(caixa_rgpd, CONSENTIMENTO_FACIAL, 11, cor=TEMA["muted"], wraplength=400, justify="left").grid(
            row=1, column=1, sticky="w", pady=(2, 12), padx=(0, 14))

        if com_foto:
            ctk.CTkCheckBox(caixa_rgpd, text="O aluno retirou o consentimento (apagar foto e modelo facial)",
                            variable=self.var_remover, command=self._trocou_remover, font=fonte(12),
                            text_color=TEMA["danger"], fg_color=TEMA["danger"], hover_color=TEMA["danger_hover"],
                            border_color=TEMA["border_forte"], corner_radius=6).grid(
                row=2, column=1, sticky="w", pady=(0, 14), padx=(0, 14))

        self.lbl_erro = rotulo(cartao, "", 12, cor=TEMA["danger"])
        self.lbl_erro.grid(row=9, column=0, columnspan=2, sticky="w", padx=24)

        barra = ctk.CTkFrame(cartao, fg_color="transparent")
        barra.grid(row=10, column=0, columnspan=2, sticky="ew", padx=24, pady=(6, 22))
        botao(barra, "Guardar", self._guardar, icone_nome="visto", width=130).pack(side="right")
        botao(barra, "Cancelar", self.fechar, "secundario").pack(side="right", padx=8)

        if aluno:
            self.entradas["nome"].insert(0, aluno["nome"])
            self.entradas["telemovel"].insert(0, aluno["telemovel"])
            self.entradas["documento"].insert(0, aluno["documento"])
            self.plano.set(aluno["plano"])

        self.bind("<Return>", lambda _e=None: self._guardar())
        self.after(150, self.entradas["nome"].focus_set)
        self.mostrar()

    def _trocou_foto(self):
        if self.var_foto.get():
            self.var_remover.set(False)

    def _trocou_remover(self):
        if self.var_remover.get():
            self.var_foto.set(False)

    def _erro(self, texto, chave=None):
        self.lbl_erro.configure(text=texto)
        for nome, entrada in self.entradas.items():
            entrada.configure(border_color=TEMA["danger"] if nome == chave else TEMA["border"])
        if chave:
            self.entradas[chave].focus_set()

    def _guardar(self):
        nome = " ".join(self.entradas["nome"].get().split())
        telemovel = self.entradas["telemovel"].get().strip().replace(" ", "")
        documento = self.entradas["documento"].get().strip()
        plano = self.plano.get()

        if len(nome.split()) < 2:
            return self._erro("Indique o nome e o apelido.", "nome")
        if not telemovel.isdigit() or len(telemovel) != 9:
            return self._erro("O telemóvel deve ter exatamente 9 dígitos.", "telemovel")
        if not documento:
            return self._erro("O documento não pode estar vazio.", "documento")
        if len(documento) > 12:
            return self._erro("O documento não pode ter mais de 12 caracteres.", "documento")
        if plano not in PLANOS:
            return self._erro("Escolha um plano.")

        foto = None
        if self.var_foto.get():
            self.grab_release()
            foto = CapturaFoto(self, nome).esperar()
            if not foto:
                if not confirmar(self, "Sem fotografia",
                                 "Não foi tirada nenhuma foto. Quer guardar o aluno sem Face ID?",
                                 texto_botao="Guardar sem foto"):
                    self._prender()
                    return

        dados = (nome, telemovel, documento, plano, foto, self.var_remover.get())
        self.fechar()
        self.callback(*dados)


# funcionário
# ======================================================
class FuncionarioFormDialog(Janela):
    def __init__(self, master, callback, funcionario=None):
        titulo = "Editar funcionário" if funcionario else "Novo funcionário"
        super().__init__(master, titulo, 500, 520)
        self.callback = callback

        cartao = Cartao(self)
        cartao.pack(fill="both", expand=True, padx=16, pady=16)
        rotulo(cartao, titulo, 18, "bold").pack(anchor="w", padx=24, pady=(22, 14))

        self.entradas = {}
        dica_senha = "Deixe vazio para manter a atual" if funcionario else "Palavra-passe"
        for chave, texto, dica in (("nome", "Nome", "Nome completo"), ("usuario", "Utilizador", "Ex.: ana.silva"),
                                   ("senha", "Palavra-passe", dica_senha)):
            rotulo(cartao, texto, 12, cor=TEMA["muted"]).pack(anchor="w", padx=24)
            entrada = campo(cartao, placeholder_text=dica, show="•" if chave == "senha" else "")
            entrada.pack(fill="x", padx=24, pady=(4, 12))
            self.entradas[chave] = entrada

        rotulo(cartao, "Cargo", 12, cor=TEMA["muted"]).pack(anchor="w", padx=24)
        self.tipo = segmentos(cartao, ["Funcionario", "Administrador"], None)
        self.tipo.pack(fill="x", padx=24, pady=(4, 10))
        self.tipo.set("Funcionario")

        self.lbl_erro = rotulo(cartao, "", 12, cor=TEMA["danger"])
        self.lbl_erro.pack(anchor="w", padx=24)

        barra = ctk.CTkFrame(cartao, fg_color="transparent")
        barra.pack(side="bottom", fill="x", padx=24, pady=22)
        botao(barra, "Guardar", self._guardar, icone_nome="visto", width=130).pack(side="right")
        botao(barra, "Cancelar", self.fechar, "secundario").pack(side="right", padx=8)

        if funcionario:
            self.entradas["nome"].insert(0, funcionario["nome"])
            self.entradas["usuario"].insert(0, funcionario["usuario"])
            self.tipo.set(funcionario["tipo"])
        self.novo = funcionario is None

        self.bind("<Return>", lambda _e=None: self._guardar())
        self.after(150, self.entradas["nome"].focus_set)
        self.mostrar()

    def _guardar(self):
        nome = self.entradas["nome"].get().strip()
        usuario = self.entradas["usuario"].get().strip()
        senha = self.entradas["senha"].get().strip()
        if not nome or not usuario or (self.novo and not senha):
            self.lbl_erro.configure(text="Preencha todos os campos.")
            return
        if senha and len(senha) < 4:
            self.lbl_erro.configure(text="A palavra-passe deve ter pelo menos 4 caracteres.")
            return
        dados = (nome, usuario, senha, self.tipo.get())
        self.fechar()
        self.callback(*dados)


# notificações
# ======================================================
class NotificacoesDialog(Janela):
    def __init__(self, master, ao_fechar=None):
        super().__init__(master, "Notificações", 560, 560)
        self.ao_fechar = ao_fechar

        cartao = Cartao(self)
        cartao.pack(fill="both", expand=True, padx=16, pady=16)

        topo = ctk.CTkFrame(cartao, fg_color="transparent")
        topo.pack(fill="x", padx=22, pady=(20, 8))
        rotulo(topo, "Notificações", 18, "bold").pack(side="left")
        botao(topo, "Marcar todas como lidas", self._marcar_todas, "fantasma", height=32).pack(side="right")
        self.lbl_total = rotulo(cartao, "", 12, cor=TEMA["muted"])
        self.lbl_total.pack(anchor="w", padx=22)

        self.lista = ctk.CTkScrollableFrame(cartao, fg_color="transparent",
                                            scrollbar_button_color=TEMA["border_forte"])
        self.lista.pack(fill="both", expand=True, padx=14, pady=10)
        self.lista.grid_columnconfigure(0, weight=1)

        barra = ctk.CTkFrame(cartao, fg_color="transparent")
        barra.pack(fill="x", padx=22, pady=(0, 20))
        botao(barra, "Limpar lidas", self._limpar_lidas, "secundario", icone_nome="lixo").pack(side="left")
        botao(barra, "Fechar", self.fechar, width=110).pack(side="right")

        self._renderizar()
        self.mostrar()

    def _renderizar(self):
        for filho in self.lista.winfo_children():
            filho.destroy()

        registos = notificacoes.listar()
        pendentes = notificacoes.por_ler()
        self.lbl_total.configure(text=f"{pendentes} por ler" if pendentes else "Está tudo lido.")

        if not registos:
            rotulo(self.lista, "Sem notificações de momento.", 13, cor=TEMA["subtle"]).grid(row=0, column=0, pady=40)
            return

        for i, registo in enumerate(registos):
            self._linha(registo).grid(row=i, column=0, sticky="ew", pady=(0, 8))

    def _linha(self, registo):
        lida = bool(registo["lida"])
        cor = TEMA["danger"] if registo["tipo"] == "atraso" else TEMA["warning"]
        if lida:
            cor = TEMA["subtle"]

        linha = ctk.CTkFrame(self.lista, fg_color=TEMA["surface_alt"] if not lida else TEMA["surface"],
                             corner_radius=14, border_width=1,
                             border_color=misturar(TEMA["surface"], cor, 0.4) if not lida else TEMA["border"])
        linha.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(linha, text="", image=icone("cartao" if registo["tipo"] == "pagamento" else "alerta", cor, 18),
                     width=36, height=36, fg_color=misturar(TEMA["surface"], cor, 0.14), corner_radius=10).grid(
            row=0, column=0, rowspan=2, padx=12, pady=12)
        rotulo(linha, registo["titulo"], 13, "bold", anchor="w").grid(row=0, column=1, sticky="ew", pady=(12, 0))
        rotulo(linha, registo["mensagem"], 12, cor=TEMA["muted"], anchor="w", justify="left",
               wraplength=330).grid(row=1, column=1, sticky="ew", pady=(0, 12))
        rotulo(linha, registo["data"][:10], 11, cor=TEMA["subtle"]).grid(row=0, column=2, rowspan=2, padx=12)

        if not lida:
            for filho in [linha] + list(linha.winfo_children()):
                filho.bind("<Button-1>", lambda _e=None, r=registo: self._marcar_lida(r))
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

    def fechar(self):
        super().fechar()
        if self.ao_fechar:
            self.ao_fechar()


# relatório
# ======================================================
class RelatorioDialog(Janela):
    def __init__(self, master, ao_gerar):
        super().__init__(master, "Relatório PDF", 460, 330)
        self.ao_gerar = ao_gerar
        self.opcoes = relatorios.meses_disponiveis()

        cartao = Cartao(self)
        cartao.pack(fill="both", expand=True, padx=16, pady=16)
        topo = ctk.CTkFrame(cartao, fg_color="transparent")
        topo.pack(fill="x", padx=22, pady=(22, 0))
        ctk.CTkLabel(topo, text="", image=icone("ficheiro", TEMA["violet"], 22), width=44, height=44,
                     fg_color=misturar(TEMA["surface"], TEMA["violet"], 0.14), corner_radius=14).pack(side="left")
        rotulo(topo, "Relatório mensal em PDF", 17, "bold").pack(side="left", padx=14)
        rotulo(cartao, "Junta os pagamentos do mês, o resumo por plano, as mensalidades em atraso "
                       "e os alunos sem pagamento.", 12, cor=TEMA["muted"], wraplength=380,
               justify="left").pack(anchor="w", padx=22, pady=(12, 12))

        self.mes = ctk.StringVar(value=self.opcoes[0]["rotulo"])
        opcao(cartao, values=[o["rotulo"] for o in self.opcoes], variable=self.mes).pack(fill="x", padx=22)

        barra = ctk.CTkFrame(cartao, fg_color="transparent")
        barra.pack(side="bottom", fill="x", padx=22, pady=20)
        botao(barra, "Gerar PDF", self._gerar, icone_nome="download", width=130).pack(side="right")
        botao(barra, "Cancelar", self.fechar, "secundario").pack(side="right", padx=8)
        self.mostrar()

    def _gerar(self):
        for opcao_mes in self.opcoes:
            if opcao_mes["rotulo"] == self.mes.get():
                self.fechar()
                self.ao_gerar(opcao_mes["ano"], opcao_mes["mes"])
                return
