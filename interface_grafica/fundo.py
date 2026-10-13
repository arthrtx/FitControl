"""Fundo em degradê 'malha' (verde, violeta, azul) por trás das páginas e
superfícies de vidro desfocado.

O Tk não tem transparência entre widgets. Por isso o fundo é uma imagem
única do painel principal e cada zona "transparente" (páginas, barras)
desenha o pedaço do fundo que lhe fica por trás. Assim o degradê parece
contínuo por trás de tudo."""

import math
import random
import tkinter as tk

import customtkinter as ctk
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageTk

from interface_grafica.constants import TEMA, escuro


def _rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb[:3])


# malha de cores
# ======================================================
def malha(largura, altura, modo_escuro):
    """Manchas de cor desfocadas + umas faixas de luz finas (tipo aurora).
    As faixas é que fazem o vidro parecer vidro: fora dele vêem-se nítidas,
    por baixo dele ficam desfocadas."""
    if modo_escuro:
        base = "#07080b"
        manchas = [
            (0.08, -0.05, 0.62, "#0f6b46", 0.95),
            (0.55, 0.30, 0.40, "#0b3f4a", 0.55),
            (1.02, 1.05, 0.62, "#3a2580", 0.85),
            (0.92, 0.05, 0.30, "#5b1747", 0.45),
            (0.15, 1.05, 0.40, "#0b2f3a", 0.55),
        ]
        faixa_cor, faixa_alfa = (120, 255, 200), 34
    else:
        base = "#eceff3"
        manchas = [
            (0.05, -0.05, 0.62, "#bfeed8", 0.95),
            (0.55, 0.35, 0.42, "#d6ecff", 0.70),
            (1.02, 1.05, 0.62, "#ddd3ff", 0.95),
            (0.95, 0.02, 0.30, "#ffd9e8", 0.70),
            (0.10, 1.05, 0.40, "#ffe6d2", 0.65),
        ]
        faixa_cor, faixa_alfa = (255, 255, 255), 120

    escala = 8
    pw, ph = max(largura // escala, 8), max(altura // escala, 8)
    img = Image.new("RGB", (pw, ph), _rgb(base))
    for x, y, r, cor, forca in manchas:
        camada = Image.new("RGB", (pw, ph), _rgb(cor))
        mascara = Image.new("L", (pw, ph), 0)
        raio = r * max(pw, ph)
        ImageDraw.Draw(mascara).ellipse((x * pw - raio, y * ph - raio * 0.8, x * pw + raio, y * ph + raio * 0.8),
                                        fill=int(255 * forca))
        mascara = mascara.filter(ImageFilter.GaussianBlur(raio * 0.45))
        img = Image.composite(camada, img, mascara)
    img = img.resize((largura, altura), Image.BICUBIC).convert("RGBA")

    # faixas de luz finas
    faixas = Image.new("RGBA", (largura, altura), faixa_cor + (0,))
    d = ImageDraw.Draw(faixas)
    aleatorio = random.Random(5)
    for n in range(7):
        pontos = []
        fase = aleatorio.uniform(0, math.pi)
        amplitude = altura * aleatorio.uniform(0.08, 0.2)
        base_y = altura * (0.15 + n * 0.11)
        for i in range(0, largura + 40, 40):
            pontos.append((i, base_y + amplitude * math.sin(i / largura * math.pi * 1.6 + fase)))
        d.line(pontos, fill=faixa_cor + (faixa_alfa,), width=2, joint="curve")
    img.alpha_composite(faixas.filter(ImageFilter.GaussianBlur(0.8)))

    # grão leve (metade da resolução, duplicado: mesmo aspeto, 4x mais barato
    # do que gerar o ruído em float64 a toda a área da janela)
    meio_w, meio_h = max(largura // 2, 1), max(altura // 2, 1)
    ruido = np.random.default_rng(3).normal(0, 3.2, (meio_h, meio_w, 1)).astype(np.float32)
    ruido = np.repeat(np.repeat(ruido, 2, axis=0), 2, axis=1)[:altura, :largura]
    if ruido.shape[0] < altura or ruido.shape[1] < largura:
        ruido = np.pad(ruido, ((0, altura - ruido.shape[0]), (0, largura - ruido.shape[1]), (0, 0)),
                       mode="edge")
    pixels = np.asarray(img.convert("RGB"), dtype=np.float32) + ruido
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))


_mascaras = {}


def _mascara_e_contorno(w, h, raio, modo_escuro):
    """Máscara arredondada + contorno fino, guardados por tamanho."""
    chave = (w, h, raio, modo_escuro)
    if chave in _mascaras:
        return _mascaras[chave]
    mascara = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=raio * 2, fill=255)
    mascara = mascara.reduce(2)

    contorno = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    cor = (255, 255, 255) if modo_escuro else (20, 20, 40)
    alfa = 26 if modo_escuro else 22
    ImageDraw.Draw(contorno).rounded_rectangle((1, 1, w * 2 - 2, h * 2 - 2), radius=raio * 2,
                                               outline=cor + (alfa,), width=2)
    contorno = contorno.reduce(2)

    # brilho no topo do cartão (luz a bater no vidro)
    coluna = np.clip(1 - np.arange(h) / (h * 0.45), 0, 1) * (22 if modo_escuro else 40)
    brilho = Image.fromarray(np.repeat(coluna.astype(np.uint8)[:, None], w, axis=1), "L")
    luz = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    luz.putalpha(brilho)
    contorno = Image.alpha_composite(luz, contorno)

    if len(_mascaras) > 60:
        _mascaras.clear()
    _mascaras[chave] = (mascara, contorno)
    return mascara, contorno


def fosco(imagem, modo_escuro=None):
    """Versão desfocada e tingida de uma imagem (o 'vidro' sem forma)."""
    if modo_escuro is None:
        modo_escuro = escuro()
    w, h = imagem.size
    pequeno = imagem.convert("RGB").resize((max(w // 6, 1), max(h // 6, 1)), Image.BILINEAR)
    pequeno = pequeno.filter(ImageFilter.GaussianBlur(5))
    if modo_escuro:
        pequeno = Image.blend(pequeno, Image.new("RGB", pequeno.size, (14, 15, 19)), 0.58)
        pequeno = Image.blend(pequeno, Image.new("RGB", pequeno.size, (255, 255, 255)), 0.035)
    else:
        pequeno = Image.blend(pequeno, Image.new("RGB", pequeno.size, (255, 255, 255)), 0.62)
    return pequeno.resize((w, h), Image.BILINEAR).convert("RGBA")


def colar_vidro(destino, fosco_img, x, y, w, h, raio, modo_escuro=None):
    """Recorta o vidro já desfocado para um cartão e cola-o no destino."""
    if modo_escuro is None:
        modo_escuro = escuro()
    if w < 4 or h < 4:
        return
    mascara, contorno = _mascara_e_contorno(w, h, raio, modo_escuro)
    pedaco = fosco_img.crop((x, y, x + w, y + h))
    pedaco.alpha_composite(contorno)
    pedaco.putalpha(ImageChops.multiply(pedaco.getchannel("A"), mascara))
    destino.alpha_composite(pedaco, (x, y))


def vidro(recorte, raio, modo_escuro=None):
    """Cartão de vidro fosco (RGBA) a partir de um pedaço do fundo."""
    w, h = recorte.size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    colar_vidro(img, fosco(recorte, modo_escuro), 0, 0, w, h, raio, modo_escuro)
    return img


# fundo partilhado pela janela
# ======================================================
class Fundo:
    """Guarda a imagem do fundo do painel e avisa as zonas transparentes."""

    def __init__(self, painel):
        self.painel = painel
        self.imagem = None
        self.pequena = None
        self.versao = 0
        self._zonas = []

    def gerar(self, largura, altura):
        self.imagem = malha(largura, altura, escuro())
        self.pequena = self.imagem.resize((max(largura // 8, 1), max(altura // 8, 1)), Image.BILINEAR)
        self.versao += 1
        for zona in list(self._zonas):
            if zona.winfo_exists():
                zona.agendar()
            else:
                self._zonas.remove(zona)

    def registar(self, zona):
        self._zonas.append(zona)

    def posicao(self, widget):
        return (widget.winfo_rootx() - self.painel.winfo_rootx(),
                widget.winfo_rooty() - self.painel.winfo_rooty())

    def recorte(self, x, y, w, h):
        if self.imagem is None:
            return Image.new("RGB", (max(w, 1), max(h, 1)), _rgb(TEMA["bg"]))
        img = Image.new("RGB", (max(w, 1), max(h, 1)), _rgb(TEMA["bg"]))
        img.paste(self.imagem.crop((x, y, x + w, y + h)), (0, 0))
        return img

    def cor_media(self, x, y, w, h):
        if self.pequena is None:
            return TEMA["bg"]
        pw, ph = self.pequena.size
        x1, y1 = max(0, x // 8), max(0, y // 8)
        x2, y2 = min(pw, max(x1 + 1, (x + w) // 8)), min(ph, max(y1 + 1, (y + h) // 8))
        if x1 >= pw or y1 >= ph:
            return TEMA["bg"]
        pedaco = np.asarray(self.pequena.crop((x1, y1, x2, y2)), dtype=np.float32)
        return _hex(pedaco.reshape(-1, 3).mean(axis=0))


class PainelFundo(tk.Canvas):
    """O painel principal arredondado, com o degradê."""

    def __init__(self, master, cor_fora):
        super().__init__(master, highlightthickness=0, bd=0, bg=cor_fora)
        self.cor_fora = cor_fora
        self.fundo = Fundo(self)
        self._job = None
        self._tamanho = None
        self._foto = None
        self.bind("<Configure>", self._agendar)

    def _agendar(self, _e=None):
        if self._job:
            self.after_cancel(self._job)
        # debounce: durante um redimensionamento o Configure dispara dezenas
        # de vezes; regenerar o degradê só quando o utilizador pára
        self._job = self.after(150, self.desenhar)

    def desenhar(self):
        # se o repaint ainda estiver pendente (chamada direta), cancela-o:
        # senão fica um after órfão que dispara depois do widget morrer
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        self._job = None
        w, h = self.winfo_width(), self.winfo_height()
        if w < 50 or h < 50 or (w, h) == self._tamanho:
            return
        self._tamanho = (w, h)
        self.fundo.gerar(w, h)
        raio = 24
        mascara = Image.new("L", (w * 2, h * 2), 0)
        ImageDraw.Draw(mascara).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=raio * 2, fill=255)
        mascara = mascara.resize((w, h), Image.LANCZOS)
        final = Image.new("RGB", (w, h), _rgb(self.cor_fora))
        final.paste(self.fundo.imagem, (0, 0), mascara)
        contorno = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
        ImageDraw.Draw(contorno).rounded_rectangle((1, 1, w * 2 - 2, h * 2 - 2), radius=raio * 2,
                                                   outline=_rgb(TEMA["border"]) + (255,), width=2)
        final = final.convert("RGBA")
        final.alpha_composite(contorno.resize((w, h), Image.LANCZOS))
        self._foto = ImageTk.PhotoImage(final)
        self.delete("fundo")
        self.create_image(0, 0, image=self._foto, anchor="nw", tags="fundo")
        self.tag_lower("fundo")

    def destroy(self):
        # sem isto o 'after' pendente dispara depois do widget morrer e o
        # Tk queixa-se com "invalid command name ... desenhar"
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        super().destroy()


class Transparente(tk.Canvas):
    """Zona que mostra o fundo do painel por trás (páginas, barras...).
    Os widgets do customtkinter lá dentro ficam com os cantos da cor certa."""

    def __init__(self, master, fundo, **kwargs):
        super().__init__(master, highlightthickness=0, bd=0, bg=TEMA["bg"], **kwargs)
        self.fundo_painel = fundo
        self._job = None
        self._estado = None
        self._foto = None
        fundo.registar(self)
        self.bind("<Configure>", self.agendar, add="+")

    def _get_widget_scaling(self):
        return ctk.ScalingTracker.get_widget_scaling(self)

    def agendar(self, _e=None):
        if self._job:
            self.after_cancel(self._job)
        # cada repaint cria uma PhotoImage do tamanho da zona toda; com o
        # debounce mais longo só se repinta quando o redimensionamento pára
        self._job = self.after(120, self.redesenhar)

    def recorte(self):
        x, y = self.fundo_painel.posicao(self)
        return self.fundo_painel.recorte(x, y, self.winfo_width(), self.winfo_height())

    def redesenhar(self, forcar=False):
        # idem a PainelFundo.desenhar: nunca deixar um after órfão pendente
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        self._job = None
        if not self.winfo_exists():
            return
        w, h = self.winfo_width(), self.winfo_height()
        if w < 2 or h < 2:
            return
        x, y = self.fundo_painel.posicao(self)
        estado = (x, y, w, h, self.fundo_painel.versao)
        if estado == self._estado and not forcar:
            return
        self._estado = estado
        self.pintar(self.fundo_painel.recorte(x, y, w, h), w, h)
        self.configure(bg=self.fundo_painel.cor_media(x, y, w, h))
        self.ajustar_filhos(x, y)

    def pintar(self, imagem, w, h):
        """Por omissão só mostra o fundo; o dashboard desenha mais coisas."""
        self._foto = ImageTk.PhotoImage(imagem)
        self.delete("fundo")
        self.create_image(0, 0, image=self._foto, anchor="nw", tags="fundo")
        self.tag_lower("fundo")

    def ajustar_filhos(self, x, y):
        for filho in self.winfo_children():
            if not isinstance(filho, ctk.CTkBaseClass) or not filho.winfo_ismapped():
                continue
            fx, fy = x + filho.winfo_x(), y + filho.winfo_y()
            cor = self.fundo_painel.cor_media(fx, fy, filho.winfo_width(), filho.winfo_height())
            if getattr(filho, "_cor_fundo_aplicada", None) != cor:
                filho._cor_fundo_aplicada = cor
                try:
                    filho.configure(bg_color=cor)
                except (ValueError, tk.TclError):
                    pass

    def destroy(self):
        # cancela o repaint pendente antes de morrer (ver PainelFundo.destroy)
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        super().destroy()
