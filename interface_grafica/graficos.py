"""Gráficos desenhados com o PIL e mostrados num Canvas.

Substituem o matplotlib: arrancam muito mais depressa, ficam com cantos
suaves e brilho como nas referências, e o texto é escrito pelo próprio
Canvas para ficar nítido."""

import math
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageChops, ImageDraw, ImageTk

from interface_grafica.constants import TEMA, misturar

SS = 2  # desenha-se 2x maior e reduz-se (anti-aliasing)
FONTE = ("Segoe UI", 9)
FONTE_TIP = ("Segoe UI", 9, "bold")


def _rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


def _suavizar(pontos, passos=10):
    """Curva Catmull-Rom a passar por todos os pontos."""
    if len(pontos) < 3:
        return pontos
    curva = []
    p = [pontos[0]] + pontos + [pontos[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for s in range(passos):
            t = s / passos
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            curva.append((x, y))
    curva.append(pontos[-1])
    return curva


def _brilho(camada, raio):
    from interface_grafica.desenho import _brilho as brilho_correto
    return brilho_correto(camada, raio)


_colunas = {}


def _degrade_vertical(w, h, cor, alfa_topo, alfa_fundo):
    chave = (h, cor, alfa_topo, alfa_fundo)
    if chave in _colunas:
        return _colunas[chave].resize((w, h))
    coluna = Image.new("RGBA", (1, h))
    r, g, b = _rgb(cor)
    for y in range(h):
        t = y / max(h - 1, 1)
        coluna.putpixel((0, y), (r, g, b, int(alfa_topo + (alfa_fundo - alfa_topo) * t)))
    if len(_colunas) > 200:
        _colunas.clear()
    _colunas[chave] = coluna
    return coluna.resize((w, h))


def _escala_bonita(maximo):
    if maximo <= 0:
        return 4
    for passo in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000, 25000, 50000):
        if maximo / passo <= 4:
            return passo * 4
    return maximo * 1.2


def escala_de(widget):
    try:
        return ctk.ScalingTracker.get_widget_scaling(widget)
    except Exception:
        return 1.0


def _formatar(valor, euros=False):
    if euros:
        if valor >= 1000:
            return f"{valor / 1000:.1f}k €".replace(".", ",")
        return f"{valor:.0f} €"
    return f"{int(valor)}"


class _Base(tk.Canvas):

    margens = (38, 14, 14, 28)  # esquerda, cima, direita, baixo

    def __init__(self, master, euros=False, cor=None):
        super().__init__(master, highlightthickness=0, bd=0, bg=TEMA["surface"],
                         height=int(150 * escala_de(master)))
        self.euros = euros
        self.cor = cor or TEMA["accent"]
        self.rotulos = []
        self.valores = []
        self._foto = None
        self._job = None
        self._pontos = []
        self._ultimo = None
        self.bind("<Configure>", self._agendar)
        self.bind("<Motion>", self._mover)
        self.bind("<Leave>", lambda _e=None: self.delete("hover"))

    def definir(self, rotulos, valores):
        if rotulos == self.rotulos and valores == self.valores:
            return
        self.rotulos = list(rotulos)
        self.valores = list(valores)
        self._agendar()

    def _agendar(self, _evento=None):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(60, self._desenhar)

    def _area(self):
        w, h = self.winfo_width(), self.winfo_height()
        e, c, d, b = self.margens
        return w, h, e, c, w - d, h - b

    def _desenhar(self):
        self._job = None
        w, h, x1, y1, x2, y2 = self._area()
        if w < 60 or h < 60:
            return
        # o Configure dispara muitas vezes com o mesmo tamanho
        assinatura = (w, h, tuple(self.valores), tuple(self.rotulos), self.cor)
        if assinatura == self._ultimo:
            return
        self._ultimo = assinatura
        self.delete("all")

        topo = _escala_bonita(max(self.valores) if self.valores else 0)
        self._topo = topo

        # a margem esquerda acompanha o tamanho do texto do eixo
        maior = max(len(_formatar(topo * i / 4, self.euros)) for i in range(5))
        x1 = 16 + 7 * maior
        self._x1 = x1

        # grelha e eixos desenhados pelo Canvas (nítidos e sem custo)
        grelha = misturar(TEMA["surface"], TEMA["border_forte"], 0.6)
        for i in range(5):
            y = y2 - (y2 - y1) * i / 4
            self.create_line(x1, y, x2, y, fill=grelha, dash=(2, 4))
            self.create_text(x1 - 8, y, text=_formatar(topo * i / 4, self.euros),
                             anchor="e", fill=TEMA["subtle"], font=FONTE)

        # o desenho tem fundo transparente e fica por cima da grelha
        img = Image.new("RGBA", (w * SS, h * SS), _rgb(TEMA["surface"]) + (0,))
        if self.valores:
            self._pintar(img, x1, y1, x2, y2, topo)
        img = img.resize((w, h), Image.BILINEAR)
        self._foto = ImageTk.PhotoImage(img)
        self.create_image(0, 0, image=self._foto, anchor="nw")
        self._eixo_x(x1, x2, y2)

    def _eixo_x(self, x1, x2, y2):
        if not self._pontos:
            return
        passo = max(1, len(self.rotulos) // 6)
        for i in range(0, len(self.rotulos), passo):
            self.create_text(self._pontos[i][0], y2 + 14, text=self.rotulos[i],
                             fill=TEMA["subtle"], font=FONTE)

    def _y(self, valor, y1, y2, topo):
        return y2 - (y2 - y1) * (valor / topo if topo else 0)

    def _mover(self, evento):
        if not self._pontos:
            return
        i = min(range(len(self._pontos)), key=lambda k: abs(self._pontos[k][0] - evento.x))
        self.delete("hover")
        self._hover(i)

    def _tooltip(self, x, y, texto):
        largura = 7 * len(texto) + 18
        w = self.winfo_width()
        xi = min(max(x - largura / 2, 4), w - largura - 4)
        yi = max(y - 40, 2)
        fundo = TEMA["text"]
        self._retangulo(xi, yi, xi + largura, yi + 26, 8, fundo, "hover")
        self.create_text(xi + largura / 2, yi + 13, text=texto, fill=TEMA["surface"],
                         font=FONTE_TIP, tags="hover")

    def _retangulo(self, x1, y1, x2, y2, r, cor, tag):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        self.create_polygon(pts, smooth=True, fill=cor, outline="", tags=tag)


class GraficoArea(_Base):
    """Linha suave com área em degradê e brilho."""

    def _pintar(self, img, x1, y1, x2, y2, topo):
        n = len(self.valores)
        passo = (x2 - x1) / max(n - 1, 1)
        self._pontos = [(x1 + i * passo, self._y(v, y1, y2, topo)) for i, v in enumerate(self.valores)]
        # a curva suave pode passar abaixo do zero entre pontos
        curva = [(x * SS, min(y, y2) * SS) for x, y in _suavizar(self._pontos, 6)]

        W, H = img.size
        topo_px, fundo_px = int(y1 * SS), int(y2 * SS)

        # área: degradê vertical recortado pela curva
        mascara = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mascara).polygon(curva + [(x2 * SS, fundo_px), (x1 * SS, fundo_px)], fill=255)
        degrade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        degrade.paste(_degrade_vertical(W, fundo_px - topo_px, self.cor, 110, 0), (0, topo_px))
        alfa = ImageChops.multiply(degrade.getchannel("A"), mascara)
        degrade.putalpha(alfa)
        img.alpha_composite(degrade)

        linha = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(linha).line(curva, fill=_rgb(self.cor) + (255,), width=int(2.4 * SS), joint="curve")
        img.alpha_composite(_brilho(linha, 5 * SS))
        img.alpha_composite(linha)

    def _hover(self, i):
        x, y = self._pontos[i]
        _, h, _, y1, _, y2 = self._area()
        self.create_line(x, y1, x, y2, fill=TEMA["border_forte"], dash=(3, 3), tags="hover")
        self.create_oval(x - 6, y - 6, x + 6, y + 6, fill=TEMA["surface"], outline=self.cor, width=3, tags="hover")
        valor = self.valores[i]
        texto = f"{self.rotulos[i]}  ·  {_formatar(valor, self.euros)}"
        if not self.euros:
            texto += " entrada" if valor == 1 else " entradas"
        self._tooltip(x, y, texto)


class GraficoBarras(_Base):
    """Barras arredondadas; a última (mês atual) fica destacada."""

    def _pintar(self, img, x1, y1, x2, y2, topo):
        n = len(self.valores)
        largura = (x2 - x1) / n
        barra = min(largura * 0.56, 34)
        self._pontos = []
        self._barras = []
        d = ImageDraw.Draw(img)
        base = misturar(TEMA["surface"], self.cor, 0.5)
        vazio = _rgb(misturar(TEMA["surface"], TEMA["border_forte"], 0.7))

        for i, v in enumerate(self.valores):
            cx = x1 + largura * (i + 0.5)
            topo_y = self._y(v, y1, y2, topo)
            self._pontos.append((cx, topo_y))
            self._barras.append((cx - barra / 2, topo_y, cx + barra / 2, y2))
            bx1, bx2 = int((cx - barra / 2) * SS), int((cx + barra / 2) * SS)
            if v <= 0:
                d.rounded_rectangle((bx1, (y2 - 3) * SS, bx2, y2 * SS), radius=SS, fill=vazio)
                continue

            atual = i == n - 1
            cor = self.cor if atual else base
            by1, by2 = int(topo_y * SS), int(y2 * SS)
            bw, bh = max(bx2 - bx1, 1), max(by2 - by1, 1)
            raio = int(min(bw / 2.6, bh / 2))

            if atual:
                brilho = Image.new("RGBA", img.size, (0, 0, 0, 0))
                ImageDraw.Draw(brilho).rounded_rectangle((bx1, by1, bx2, by2), radius=raio,
                                                         fill=_rgb(cor) + (150,))
                img.alpha_composite(_brilho(brilho, 7 * SS))

            # cada barra só mexe na sua própria área (antes eram máscaras do
            # tamanho do gráfico inteiro, 12 vezes por desenho)
            grad = _degrade_vertical(bw, bh, cor, 255, 150)
            mascara = Image.new("L", (bw, bh), 0)
            ImageDraw.Draw(mascara).rounded_rectangle((0, 0, bw - 1, bh - 1), radius=raio, fill=255)
            grad.putalpha(ImageChops.multiply(grad.getchannel("A"), mascara))
            img.alpha_composite(grad, (bx1, by1))

    def _hover(self, i):
        x1, y1, x2, y2 = self._barras[i]
        self._retangulo(x1 - 4, 6, x2 + 4, y2 + 2, 8, misturar(TEMA["surface"], TEMA["text"], 0.06), "hover")
        self.tag_lower("hover")
        self._tooltip((x1 + x2) / 2, y1, f"{self.rotulos[i]}  ·  {_formatar(self.valores[i], self.euros)}")


class Anel(tk.Canvas):
    """Anel de progresso com brilho (como os das referências)."""

    def __init__(self, master, tamanho=64, espessura=None, cor=None, fundo=None, texto=True, fonte=None):
        self.fundo = fundo or TEMA["surface"]
        escala = escala_de(master)
        tamanho = int(tamanho * escala)
        super().__init__(master, width=tamanho, height=tamanho, highlightthickness=0, bd=0, bg=self.fundo)
        self.tamanho = tamanho
        self.espessura = int((espessura or max(5, tamanho / escala // 9)) * escala)
        self.cor = cor or TEMA["accent"]
        self.mostrar_texto = texto
        self.fonte = fonte or ("Segoe UI", max(9, tamanho // 6), "bold")
        self.fracao = 0.0
        self._atual = 0.0
        self._job = None
        self._foto = None
        self._icone = None
        self._desenhar(0)

    def definir(self, fracao, animar=True):
        self.fracao = max(0.0, min(1.0, fracao))
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        if not animar:
            self._atual = self.fracao
            self._desenhar(self._atual)
            return
        self._passo()

    def definir_icone(self, imagem_pil):
        lado = int(self.tamanho * 0.36)
        self._icone = ImageTk.PhotoImage(imagem_pil.resize((lado, lado), Image.LANCZOS))
        self._desenhar(self._atual)

    def _passo(self):
        diferenca = self.fracao - self._atual
        if abs(diferenca) < 0.004:
            self._atual = self.fracao
            self._desenhar(self._atual)
            self._job = None
            return
        self._atual += diferenca * 0.25
        self._desenhar(self._atual)
        self._job = self.after(16, self._passo)

    def _desenhar(self, fracao):
        fracao = round(fracao, 3)
        chave = (self.tamanho, self.espessura, self.cor, self.fundo, fracao)
        foto = _aneis.get(chave)
        if foto is None:
            foto = ImageTk.PhotoImage(self._imagem(fracao))
            if len(_aneis) > 400:
                _aneis.clear()
            _aneis[chave] = foto
        self._foto = foto

        self.delete("all")
        self.create_image(0, 0, image=self._foto, anchor="nw")
        meio = self.tamanho / 2
        if self._icone is not None:
            self.create_image(meio, meio, image=self._icone)
        elif self.mostrar_texto:
            self.create_text(meio, meio, text=f"{round(self.fracao * 100)}%", fill=TEMA["text"], font=self.fonte)

    def _imagem(self, fracao):
        escala = 3
        lado = self.tamanho * escala
        img = Image.new("RGBA", (lado, lado), _rgb(self.fundo) + (255,))
        e = self.espessura * escala
        folga = e * 1.6
        caixa = (folga, folga, lado - folga, lado - folga)
        trilho = misturar(self.fundo, TEMA["border_forte"], 0.9)
        ImageDraw.Draw(img).ellipse(caixa, outline=_rgb(trilho), width=int(e))

        if fracao > 0.002:
            arco = Image.new("RGBA", (lado, lado), _rgb(self.cor) + (0,))
            d = ImageDraw.Draw(arco)
            inicio = -90
            fim = -90 + 360 * fracao
            cor = _rgb(self.cor) + (255,)
            d.arc(caixa, inicio, fim, fill=cor, width=int(e))
            # pontas redondas
            r = (caixa[2] - caixa[0]) / 2 - e / 2
            cx = cy = lado / 2
            for ang in (inicio, fim):
                a = math.radians(ang)
                px, py = cx + r * math.cos(a), cy + r * math.sin(a)
                d.ellipse((px - e / 2, py - e / 2, px + e / 2, py + e / 2), fill=cor)
            img.alpha_composite(_brilho(arco, e * 0.9))
            img.alpha_composite(arco)

        return img.resize((self.tamanho, self.tamanho), Image.LANCZOS)


# anéis já desenhados (as animações repetem sempre as mesmas frações)
_aneis = {}
