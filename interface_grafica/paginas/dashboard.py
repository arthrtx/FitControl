from collections import defaultdict
from datetime import datetime, timedelta

from PIL import Image, ImageTk

from interface_grafica import desenho as D
from interface_grafica.constants import TEMA, PLANOS, escuro
from interface_grafica.fundo import colar_vidro, fosco
from interface_grafica.icones import imagem as imagem_icone
from interface_grafica.utils import euros
from interface_grafica.widgets import Pagina, botao
from modulos import estatistica, funcionarios as gestao_funcionarios
from projeto_ginasio.dados import pagamentos as lista_pagamentos
from projeto_ginasio.db_adapter import contar_presencas_por_dia

ATUALIZAR_MS = 15000


def _rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


def presencas_30_dias():
    contagem = contar_presencas_por_dia()
    hoje = datetime.now().date()
    dias = [hoje - timedelta(days=i) for i in range(29, -1, -1)]
    rotulos = [dia.strftime("%d/%m") for dia in dias]
    valores = [contagem.get(dia.strftime("%d/%m/%Y"), 0) for dia in dias]
    return rotulos, valores


def receita_12_meses():
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
    for pagamento in lista_pagamentos:
        try:
            data = datetime.strptime(pagamento["data_pagamento"], "%d/%m/%Y")
            totais[(data.month, data.year)] += float(pagamento.get("valor", 0))
        except (ValueError, TypeError, KeyError):
            continue

    nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    return [nomes[m - 1] for m, _a in chaves], [round(totais[c], 2) for c in chaves]




GAP = 14
RAIO = 20


class PaginaDashboard(Pagina):
    """Dashboard desenhado de uma vez num só Canvas: cartões de vidro fosco
    por cima do degradê, LEDs e gráficos. Só os botões são widgets."""

    titulo = "Dashboard"
    subtitulo = "Visão geral da academia em tempo real"
    so_admin = False

    def __init__(self, app):
        super().__init__(app)
        # atenção: Transparente já usa self._job para o repaint; o ciclo de
        # dados do dashboard tem de usar outro atributo para não o roubar
        self._job_ciclo = None
        self._anim = None
        self._dados = None
        self._assinatura = None
        self._composto = None
        self._vidro_chave = None
        self._vidro_img = None
        self._pontos = []
        self._barras = []
        self._areas = {}
        self._mostrados = {}
        self._alvos = {}

        self.botoes = [
            botao(self, "Novo aluno", lambda: self._ir("alunos", "novo"), icone_nome="mais"),
            botao(self, "Pagamento", lambda: self._ir("pagamentos"), "secundario", icone_nome="cartao"),
            botao(self, "Face ID", lambda: self._ir("presencas"), "secundario", icone_nome="rosto"),
        ]
        self.bind("<Motion>", self._mover)
        self.bind("<Leave>", lambda _e=None: self.delete("hover"))

    def _ir(self, pagina, acao=None):
        self.app.mostrar_pagina(pagina)
        if acao == "novo":
            alvo = self.app.paginas.get("alunos")
            if alvo:
                alvo.novo_aluno()

    # dados
    # ======================================================
    def _recolher(self):
        stats = estatistica.estatisticas()
        rot_pres, val_pres = presencas_30_dias()
        rot_rec, val_rec = receita_12_meses()
        tipos = [f["tipo"] for f in gestao_funcionarios.funcionarios]
        return {
            "stats": stats,
            "rot_pres": rot_pres, "val_pres": val_pres,
            "rot_rec": rot_rec, "val_rec": val_rec,
            "tipos": tipos,
        }

    def atualizar(self, forcar=False):
        dados = self._recolher()
        assinatura = (tuple(sorted(dados["stats"].items())), tuple(dados["val_pres"]),
                      tuple(dados["val_rec"]), tuple(dados["tipos"]))
        if assinatura == self._assinatura and not forcar:
            return
        self._assinatura = assinatura
        self._dados = dados
        self.redesenhar(forcar=True)

    def _ciclo(self):
        self.atualizar()
        self._job_ciclo = self.after(ATUALIZAR_MS, self._ciclo)

    def ao_mostrar(self):
        self._ciclo()

    def ao_esconder(self):
        for job in (self._job_ciclo, self._anim):
            if job:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
        self._job_ciclo = self._anim = None

    # layout
    # ======================================================
    def _layout(self, w, h):
        g = GAP
        caixas = {}
        y = 0
        if h >= 600:
            caixas["hero"] = (0, 0, w, 104)
            y = 104 + g
        c3 = max(int((w - 3 * g) / 4), 250)
        c = int((w - 3 * g - c3) / 3)
        xs = [0, c + g, 2 * (c + g), 3 * (c + g)]
        largura_3 = 3 * c + 2 * g
        for i in range(4):
            caixas[f"m{i}"] = (xs[i], y, c3 if i == 3 else c, 92)
        y += 92 + g
        resto = h - y
        r2 = int((resto - g) / 2)
        caixas["entradas"] = (0, y, largura_3, r2)
        caixas["mensal"] = (xs[3], y, c3, r2)
        y2 = y + r2 + g
        caixas["receita"] = (0, y2, largura_3, resto - r2 - g)
        caixas["planos"] = (xs[3], y2, c3, resto - r2 - g)
        return caixas

    # desenho
    # ======================================================
    def pintar(self, fundo, w, h):
        if self._dados is None:
            self._dados = self._recolher()
        base = fundo.convert("RGBA")
        caixas = self._layout(w, h)
        self._areas = caixas
        self.delete("conteudo")
        self.delete("hover")

        # o fundo inteiro é desfocado uma só vez e cada cartão recorta o seu
        # pedaço; o blur é o passo mais caro, por isso fica em cache enquanto
        # o fundo e a geometria não mudarem (redraws a cada 15 s não o refazem)
        chave = (self.fundo_painel.versao, w, h) + tuple(self.fundo_painel.posicao(self))
        if chave != self._vidro_chave:
            self._vidro_chave = chave
            self._vidro_img = fosco(fundo)
        vidro_pagina = self._vidro_img
        for x, y, cw, ch in caixas.values():
            if cw > 20 and ch > 20:
                colar_vidro(base, vidro_pagina, x, y, cw, ch, RAIO)

        self._apagado = "#2a2c34" if escuro() else "#d8dbe4"
        if "hero" in caixas:
            self._hero(base, *caixas["hero"])
        else:
            for b in self.botoes:
                b.place_forget()
        self._metricas(base, caixas)
        self._entradas(base, *caixas["entradas"])
        self._mensalidades(base, *caixas["mensal"])
        self._receita(base, *caixas["receita"])
        self._planos(base, *caixas["planos"])

        self._composto = base
        self._foto = ImageTk.PhotoImage(base)
        self.delete("fundo")
        self.create_image(0, 0, image=self._foto, anchor="nw", tags="fundo")
        self.tag_lower("fundo")
        self._animar_valores()

    def ajustar_filhos(self, x, y):
        # os botões ficam por cima do vidro, não do fundo: amostra-se a imagem final
        if self._composto is None:
            return
        for filho in self.botoes:
            if not filho.winfo_ismapped():
                continue
            fx, fy = filho.winfo_x(), filho.winfo_y()
            pedaco = self._composto.crop((fx, fy, fx + 6, fy + 6)).convert("RGB").resize((1, 1))
            cor = "#%02x%02x%02x" % pedaco.getpixel((0, 0))
            if getattr(filho, "_cor_fundo_aplicada", None) != cor:
                filho._cor_fundo_aplicada = cor
                filho.configure(bg_color=cor)

    def _texto(self, x, y, texto, tamanho=11, peso="normal", cor="text", ancora="nw", tags=()):
        return self.create_text(x, y, text=texto, anchor=ancora, fill=TEMA[cor],
                                font=("Segoe UI", tamanho, peso), tags=("conteudo",) + tuple(tags))

    def _titulo_cartao(self, x, y, titulo, subtitulo=None):
        self._texto(x + 20, y + 16, titulo, 12, "bold")
        if subtitulo:
            self._texto(x + 20, y + 37, subtitulo, 9, cor="muted")

    def _pastilha(self, base, x_dir, y, texto, cor):
        """Pastilha com texto alinhada à direita em x_dir."""
        largura = 7 * len(texto) + 22
        D.pill(base, x_dir - largura, y, largura, 24, cor, 46 if escuro() else 36)
        self._texto(x_dir - largura / 2, y + 12, texto, 9, "bold", ancora="center")
        self.itemconfigure(self.find_withtag("conteudo")[-1], fill=cor if not escuro() else TEMA["text"])

    def _hero(self, base, x, y, w, h):
        from PIL import ImageDraw, ImageFilter
        # brilhos de cor por dentro do vidro
        luz = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(luz)
        d.ellipse((-80, -60, 360, 200), fill=D.rgb(TEMA["accent"]) + (95,))
        d.ellipse((w * 0.35, -40, w * 0.35 + 380, 180), fill=D.rgb(TEMA["violet"]) + (60,))
        luz = luz.resize((max(w // 6, 1), max(h // 6, 1))).filter(ImageFilter.GaussianBlur(9)).resize((w, h))
        mascara = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mascara).rounded_rectangle((0, 0, w - 1, h - 1), radius=RAIO, fill=255)
        luz.putalpha(Image.composite(luz.getchannel("A"), Image.new("L", (w, h), 0), mascara))
        base.alpha_composite(luz, (x, y))

        stats = self._dados["stats"]
        hora = datetime.now().hour
        saudacao = "Bom dia" if hora < 13 else ("Boa tarde" if hora < 20 else "Boa noite")
        primeiro = self.app.utilizador["nome"].split()[0]
        self._texto(x + 26, y + 16, f"{saudacao}, {primeiro}", 18, "bold")

        hoje, atraso = stats["presencas_hoje"], stats["mensalidades_atrasadas"]
        partes = [f"{hoje} {'entrada' if hoje == 1 else 'entradas'} hoje"]
        partes.append(f"{atraso} em atraso" if atraso else "nada em atraso")
        self._texto(x + 26, y + 48, "  ·  ".join(partes), 10, "bold", cor="muted")

        total = stats["total_alunos"]
        fracao = stats["mensalidades_validas"] / total if total else 0
        largura = int(min(380, w * 0.36))
        D.espectro(base, x + 26, y + 78, largura, 6, fracao,
                   [TEMA["accent"], TEMA["cyan"], TEMA["violet"], TEMA["magenta"]], self._apagado)
        self._texto(x + 26 + largura + 12, y + 81, f"{round(fracao * 100)}% em dia", 9, "bold", ancora="w")

        # botões à direita. O place dos widgets do customtkinter multiplica
        # x/y pela escala do Windows (125%, 150%...), mas aqui as contas são
        # em píxeis reais do canvas: divide-se antes, senão os botões saem
        # para fora do cartão em ecrãs com escala
        escala = self._get_widget_scaling()
        livre = (x + w - 22) - (x + 26 + largura + int(110 * escala))
        if not getattr(self, "_compactos", False):
            # largura com texto (só se mede com o texto visível)
            self._largura_botoes = sum(b.winfo_reqwidth() for b in self.botoes) + 16 * escala
        self._compactar_botoes(self._largura_botoes > livre)
        xb = x + w - 22
        for b in reversed(self.botoes):
            b.update_idletasks()
            xb -= b.winfo_reqwidth()
            b.place(x=xb / escala, y=(y + (h - b.winfo_reqheight()) / 2) / escala)
            xb -= 8 * escala

    def _compactar_botoes(self, compacto):
        # janela estreita (ou escala grande no Windows): só os ícones, para os
        # botões não taparem a saudação
        if compacto == getattr(self, "_compactos", False):
            return
        self._compactos = compacto
        for b, texto in zip(self.botoes, ("Novo aluno", "Pagamento", "Face ID")):
            b.configure(text="" if compacto else texto, width=38 if compacto else 140)
        for b in self.botoes:
            b.update_idletasks()

    def _metricas(self, base, caixas):
        st = self._dados["stats"]
        total = st["total_alunos"] or 0
        rec = self._dados["val_rec"]
        if self.app.admin:
            defs = [
                ("total_alunos", "Total de alunos", "violet", "alunos", "pagas"),
                ("presencas_hoje", "Presenças hoje", "accent", "visto", "semana"),
                ("receita_mes", "Receita do mês", "amber", "carteira", "receita"),
                ("funcionarios_registados", "Funcionários", "cyan", "funcionarios", "equipa"),
            ]
        else:
            defs = [
                ("total_alunos", "Total de alunos", "violet", "alunos", "pagas"),
                ("presencas_hoje", "Presenças hoje", "accent", "visto", "semana"),
                ("mensalidades_validas", "Mensalidades pagas", "cyan", "cartao", "pagas"),
                ("mensalidades_atrasadas", "Em atraso", "magenta", "alerta", "atraso"),
            ]
        self._alvos = {}
        for i, (chave, rotulo, cor, nome_icone, leds) in enumerate(defs):
            x, y, cw, ch = caixas[f"m{i}"]
            cor_hex = TEMA[cor]
            D.circulo_icone(base, x + 16, y + 16, 38, cor_hex, imagem_icone(nome_icone, cor_hex, 64))
            self._texto(x + 66, y + 15, rotulo, 9, cor="muted")
            self._texto(x + 66, y + 30, "0", 19, "bold", tags=(f"valor_{chave}",))
            self._alvos[chave] = (float(st.get(chave, 0)), chave == "receita_mes")

            n = max(int((cw - 32) / 13), 4)
            caixa_led = (x + 16, y + ch - 24, cw - 32, 12)
            if leds == "semana":
                colunas = min(n, 14)
                ultimos = self._dados["val_pres"][-colunas:]
                D.equalizador(base, x + 16, y + ch - 33, colunas * 13, 26, ultimos, cor_hex, self._apagado, niveis=3)
                continue
            if leds == "pagas":
                cores = D.leds_proporcao(n, st["mensalidades_validas"] / total if total else 0, cor_hex)
            elif leds == "atraso":
                cores = D.leds_proporcao(n, st["mensalidades_atrasadas"] / total if total else 0, cor_hex)
            elif leds == "receita":
                anterior = rec[-2] if len(rec) > 1 else 0
                cores = D.leds_proporcao(n, rec[-1] / anterior if anterior else (1 if rec[-1] else 0), cor_hex)
            else:
                tipos = self._dados["tipos"][:n]
                cores = [TEMA["violet"] if t == "Administrador" else cor_hex for t in tipos]
                cores += [None] * (n - len(cores))
            D.leds(base, *caixa_led, cores, self._apagado)

    def _animar_valores(self):
        if self._anim:
            self.after_cancel(self._anim)
            self._anim = None
        continuar = False
        for chave, (alvo, em_euros) in self._alvos.items():
            atual = self._mostrados.get(chave, 0.0)
            diferenca = alvo - atual
            if abs(diferenca) < 0.05:
                atual = alvo
            else:
                atual += diferenca * 0.22
                continuar = True
            self._mostrados[chave] = atual
            if em_euros:
                texto = f"{int(round(atual)):,}".replace(",", " ") + " €"
            else:
                texto = str(int(round(atual)))
            self.itemconfigure(f"valor_{chave}", text=texto)
        if continuar:
            self._anim = self.after(16, self._animar_valores)

    def _eixo_y(self, x, y, h, topo, em_euros=False, x_fim=None):
        for i in range(5):
            yy = y + h - h * i / 4
            valor = topo * i / 4
            if em_euros:
                texto = f"{valor / 1000:.1f}k".replace(".", ",") if valor >= 1000 else f"{valor:.0f}"
            else:
                texto = f"{int(valor)}"
            self._texto(x - 8, yy, texto, 8, cor="subtle", ancora="e")
            if x_fim:
                self.create_line(x, yy, x_fim, yy, fill=TEMA["border_forte"], dash=(1, 4), tags="conteudo")

    def _entradas(self, base, x, y, w, h):
        self._titulo_cartao(x, y, "Entradas", "Últimos 30 dias")
        valores = self._dados["val_pres"]
        media = sum(valores) / len(valores) if valores else 0
        self._pastilha(base, x + w - 18, y + 16, f"Média {media:.1f}/dia".replace(".", ","), TEMA["accent"])

        cx, cy = x + 52, y + 66
        cw, chh = w - 52 - 26, h - 66 - 34
        if chh < 30:
            self._pontos = []
            return
        topo = _escala(max(valores) if valores else 0)
        self._eixo_y(cx, cy, chh, topo, x_fim=cx + cw)
        self._pontos = D.linha_area(base, cx, cy, cw, chh, valores, topo,
                                    [TEMA["accent"], TEMA["cyan"]], D.rgb(TEMA["surface"]))
        self._grafico_entradas = (cx, cy, cw, chh)
        rotulos = self._dados["rot_pres"]
        for i in range(0, len(rotulos), 5):
            self._texto(self._pontos[i][0], cy + chh + 12, rotulos[i], 8, cor="subtle", ancora="n")
        # valor de hoje junto ao último ponto
        px, py = self._pontos[-1]
        texto = f"{valores[-1]} hoje"
        largura = 7 * len(texto) + 18
        D.pill(base, px - largura + 8, py - 36, largura, 22, TEMA["text"], 235)
        self._texto(px - largura / 2 + 8, py - 25, texto, 8, "bold", cor="surface", ancora="center")

    def _mensalidades(self, base, x, y, w, h):
        self._titulo_cartao(x, y, "Mensalidades", "Situação dos alunos")
        st = self._dados["stats"]
        total = st["total_alunos"]
        pagas, atraso = st["mensalidades_validas"], st["mensalidades_atrasadas"]
        sem = max(total - pagas - atraso, 0)
        fracao = pagas / total if total else 0

        lado = int(max(min(w - 60, h - 112, 150), 60))
        gx, gy = x + (w - lado) / 2, y + 56
        D.medidor(base, gx, gy, lado, fracao, [TEMA["accent"], TEMA["cyan"]], self._apagado,
                  espessura=max(8, lado // 14))
        self._texto(x + w / 2, gy + lado * 0.46, f"{round(fracao * 100)}%", max(14, lado // 6), "bold", ancora="center")
        self._texto(x + w / 2, gy + lado * 0.46 + lado // 6, "em dia", 9, cor="muted", ancora="n")

        n = 20
        cores = []
        if total:
            n_pagas = round(pagas / total * n)
            n_atraso = round(atraso / total * n)
            cores = [TEMA["accent"]] * n_pagas + [TEMA["danger"]] * n_atraso
        cores = (cores + [None] * n)[:n]
        D.leds(base, x + 20, y + h - 50, w - 40, 12, cores, self._apagado)

        legenda = [(pagas, "pagas", "accent"), (atraso, "atraso", "danger"), (sem, "sem pag.", "subtle")]
        passo = (w - 40) / 3
        for i, (valor, texto, cor) in enumerate(legenda):
            xx = x + 20 + i * passo
            self.create_oval(xx, y + h - 26, xx + 7, y + h - 19, fill=TEMA[cor], outline="", tags="conteudo")
            self._texto(xx + 12, y + h - 23, f"{valor} {texto}", 9, cor="muted", ancora="w")

    def _receita(self, base, x, y, w, h):
        self._titulo_cartao(x, y, "Receita mensal", "Últimos 12 meses")
        if self.app.admin:
            self._pastilha(base, x + w - 18, y + 16, f"Total {euros(self._dados['stats']['receita_total'])}",
                           TEMA["violet"])
        valores = self._dados["val_rec"]
        cx, cy = x + 58, y + 66
        cw, chh = w - 58 - 26, h - 66 - 34
        if chh < 30:
            self._barras = []
            return
        topo = _escala(max(valores) if valores else 0)
        self._eixo_y(cx, cy, chh, topo, em_euros=True)
        self._barras = D.barras_pill(base, cx, cy, cw, chh, valores, topo,
                                     [TEMA["violet"], TEMA["magenta"]], self._apagado, TEMA["accent"])
        for i, rotulo in enumerate(self._dados["rot_rec"]):
            x1, _y1, x2, _y2 = self._barras[i]
            if i % 2 == 0 or i == len(valores) - 1:
                self._texto((x1 + x2) / 2, cy + chh + 12, rotulo, 8, cor="subtle", ancora="n")
        if valores and valores[-1] > 0:
            x1, y1, x2, _y2 = self._barras[-1]
            texto = f"{valores[-1]:.0f} €"
            largura = 7 * len(texto) + 18
            D.pill(base, (x1 + x2) / 2 - largura / 2, y1 - 30, largura, 22, TEMA["accent"], 255)
            self._texto((x1 + x2) / 2, y1 - 19, texto, 8, "bold", cor="on_accent", ancora="center")

    def _planos(self, base, x, y, w, h):
        self._titulo_cartao(x, y, "Alunos por plano")
        st = self._dados["stats"]
        total = st["total_alunos"]
        quantidades = [st["plano_diario"], st["plano_mensal"], st["plano_trimestral"], st["plano_anual"]]
        cores = [TEMA["accent"], TEMA["violet"], TEMA["amber"], TEMA["magenta"]]
        topo_linhas = y + 50
        passo = max((h - 64) / 4, 20)
        n = max(int((w - 130) / 11), 5)
        for i, (plano, quantidade) in enumerate(zip(PLANOS, quantidades)):
            yy = topo_linhas + i * passo
            self._texto(x + 20, yy + 6, plano, 9, cor="muted", ancora="w")
            D.leds(base, x + 92, yy, n * 11, 12, D.leds_proporcao(n, quantidade / total if total else 0, cores[i]),
                   self._apagado)
            self._texto(x + w - 20, yy + 6, str(quantidade), 10, "bold", ancora="e")

    # rato por cima dos gráficos
    # ======================================================
    def _mover(self, evento):
        self.delete("hover")
        if self._pontos and "entradas" in self._areas:
            cx, cy, cw, chh = self._grafico_entradas
            if cx - 10 <= evento.x <= cx + cw + 10 and cy - 10 <= evento.y <= cy + chh + 10:
                i = min(range(len(self._pontos)), key=lambda k: abs(self._pontos[k][0] - evento.x))
                px, py = self._pontos[i]
                self.create_line(px, cy, px, cy + chh, fill=TEMA["subtle"], dash=(3, 3), tags="hover")
                self.create_oval(px - 6, py - 6, px + 6, py + 6, fill=TEMA["surface"], outline=TEMA["accent"],
                                 width=3, tags="hover")
                valor = self._dados["val_pres"][i]
                self._dica(px, py, f"{self._dados['rot_pres'][i]}  ·  {valor} {'entrada' if valor == 1 else 'entradas'}")
                return
        for i, (x1, y1, x2, y2) in enumerate(self._barras):
            if x1 - 12 <= evento.x <= x2 + 12 and y1 - 200 <= evento.y <= y2:
                self._dica((x1 + x2) / 2, y1, f"{self._dados['rot_rec'][i]}  ·  {euros(self._dados['val_rec'][i])}")
                return

    def _dica(self, x, y, texto):
        largura = 7 * len(texto) + 20
        xi = min(max(x - largura / 2, 4), self.winfo_width() - largura - 4)
        yi = max(y - 44, 2)
        r = 9
        x1, y1, x2, y2 = xi, yi, xi + largura, yi + 26
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        self.create_polygon(pts, smooth=True, fill=TEMA["text"], outline="", tags="hover")
        self.create_text(xi + largura / 2, yi + 13, text=texto, fill=TEMA["surface"],
                         font=("Segoe UI", 9, "bold"), tags="hover")


def _escala(maximo):
    if maximo <= 0:
        return 4
    for passo in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000, 25000, 50000):
        if maximo / passo <= 4:
            return passo * 4
    return maximo * 1.2
