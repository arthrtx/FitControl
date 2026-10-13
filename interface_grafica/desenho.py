"""Peças desenhadas com o PIL para o dashboard: LEDs, medidor, linha com
tracejado, barras em 'pill' e barra de espectro.

Tudo é desenhado 2x maior e reduzido (cantos suaves). As funções recebem
a imagem final e uma caixa (x, y, largura, altura) onde desenhar."""

import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from interface_grafica.constants import escuro

SS = 2


def rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


def misturar_rgb(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def _camada(w, h):
    return Image.new("RGBA", (max(int(w * SS), 1), max(int(h * SS), 1)), (0, 0, 0, 0))


def _colar(destino, camada, x, y):
    # reduce() faz a média de blocos 2x2: muito mais rápido do que LANCZOS
    reduzida = camada.reduce(SS) if min(camada.size) >= SS else camada
    destino.alpha_composite(reduzida, (int(x), int(y)))


def _brilho(camada, raio):
    """Desfoque barato do brilho. Desfoca-se com a cor multiplicada pelo
    alfa; sem isso os píxeis transparentes (pretos) davam um halo escuro."""
    w, h = camada.size
    pequeno = camada.resize((max(w // 4, 1), max(h // 4, 1)), Image.BILINEAR)
    pixels = np.asarray(pequeno, dtype=np.float32)
    alfa = pixels[..., 3:4] / 255.0
    pre = np.concatenate([pixels[..., :3] * alfa, pixels[..., 3:4]], axis=2).astype(np.uint8)
    pre = Image.fromarray(pre, "RGBA").filter(ImageFilter.GaussianBlur(max(raio / 4, 1)))
    pixels = np.asarray(pre, dtype=np.float32)
    alfa = np.maximum(pixels[..., 3:4], 1) / 255.0
    rgb_ = np.clip(pixels[..., :3] / alfa, 0, 255)
    final = np.concatenate([rgb_, pixels[..., 3:4]], axis=2).astype(np.uint8)
    if not escuro():
        # no tema claro o brilho fica mais discreto
        final[..., 3] = (final[..., 3] * 0.5).astype(np.uint8)
    return Image.fromarray(final, "RGBA").resize((w, h), Image.BILINEAR)


_linhas = {}


def degrade_h(w, h, cores):
    """Degradê horizontal entre várias cores."""
    w = max(int(w), 2)
    chave = (w, tuple(cores))
    linha = _linhas.get(chave)
    if linha is None:
        pontos = np.array([rgb(c) for c in cores], dtype=np.float32)
        t = np.linspace(0, len(cores) - 1, w)
        i = np.minimum(t.astype(int), len(cores) - 2)
        f = (t - i)[:, None]
        cor = pontos[i] * (1 - f) + pontos[i + 1] * f
        pixels = np.concatenate([cor, np.full((w, 1), 255, np.float32)], axis=1).astype(np.uint8)
        linha = Image.fromarray(pixels[None, :, :], "RGBA")
        if len(_linhas) > 300:
            _linhas.clear()
        _linhas[chave] = linha
    return linha.resize((w, max(int(h), 1)), Image.NEAREST)


# LEDs
# ======================================================
def leds(destino, x, y, w, h, cores, apagado, raio=None, colunas=None, brilho=True):
    """Uma linha (ou grelha) de LEDs. 'cores' tem uma cor por LED, ou None
    para os apagados."""
    n = len(cores)
    if not n:
        return
    colunas = colunas or n
    linhas = math.ceil(n / colunas)
    passo_x = w / colunas
    passo_y = h / max(linhas, 1)
    r = raio or min(passo_x, passo_y) * 0.32
    # margem à volta para o brilho não ficar cortado num retângulo
    m = int(r * 3) + 2
    camada = _camada(w + 2 * m, h + 2 * m)
    d = ImageDraw.Draw(camada)
    acesos = _camada(w + 2 * m, h + 2 * m)
    da = ImageDraw.Draw(acesos)
    for i, cor in enumerate(cores):
        cx = ((i % colunas + 0.5) * passo_x + m) * SS
        cy = ((i // colunas + 0.5) * passo_y + m) * SS
        caixa = (cx - r * SS, cy - r * SS, cx + r * SS, cy + r * SS)
        if cor is None:
            d.ellipse(caixa, fill=rgb(apagado) + (255,))
        else:
            da.ellipse(caixa, fill=rgb(cor) + (255,))
    if brilho:
        camada.alpha_composite(_brilho(acesos, r * SS * 2.2))
    camada.alpha_composite(acesos)
    _colar(destino, camada, x - m, y - m)


def leds_proporcao(total_leds, fracao, cor):
    acesos = round(max(0.0, min(1.0, fracao)) * total_leds)
    return [cor if i < acesos else None for i in range(total_leds)]


def equalizador(destino, x, y, w, h, valores, cor, apagado, niveis=5):
    """Colunas de LEDs (como um equalizador): uma coluna por valor."""
    if not valores:
        return
    maximo = max(max(valores), 1)
    colunas = len(valores)
    cores = []
    for nivel in range(niveis, 0, -1):
        for v in valores:
            acesos = math.ceil(v / maximo * niveis) if v else 0
            cores.append(cor if acesos >= nivel else None)
    leds(destino, x, y, w, h, cores, apagado, colunas=colunas)


# medidor (gauge)
# ======================================================
def medidor(destino, x, y, lado, fracao, cores, trilho, espessura=12):
    abertura = 240
    inicio = 90 + (360 - abertura) / 2
    camada = _camada(lado, lado)
    d = ImageDraw.Draw(camada)
    e = espessura * SS
    folga = e * 2
    caixa = (folga, folga, lado * SS - folga, lado * SS - folga)
    d.arc(caixa, inicio, inicio + abertura, fill=rgb(trilho) + (255,), width=e)
    raio = (caixa[2] - caixa[0]) / 2 - e / 2
    meio = lado * SS / 2

    def ponta(ang, cor, alvo):
        a = math.radians(ang)
        px, py = meio + raio * math.cos(a), meio + raio * math.sin(a)
        alvo.ellipse((px - e / 2, py - e / 2, px + e / 2, py + e / 2), fill=cor)

    ponta(inicio, rgb(trilho) + (255,), d)
    ponta(inicio + abertura, rgb(trilho) + (255,), d)

    if fracao > 0.003:
        fim = inicio + abertura * min(fracao, 1)
        mascara = Image.new("L", camada.size, 0)
        dm = ImageDraw.Draw(mascara)
        dm.arc(caixa, inicio, fim, fill=255, width=e)
        ponta(inicio, 255, dm)
        ponta(fim, 255, dm)
        # degradê a acompanhar o arco (da esquerda para a direita)
        cor = degrade_h(camada.width, camada.height, cores)
        cor.putalpha(mascara)
        camada.alpha_composite(_brilho(cor, e * 1.6))
        camada.alpha_composite(cor)
    _colar(destino, camada, x, y)


# barra de espectro (como a do "730 Excellent")
# ======================================================
def espectro(destino, x, y, w, h, fracao, cores, trilho):
    camada = _camada(w, h + 16)
    d = ImageDraw.Draw(camada)
    yy = 8 * SS
    d.rounded_rectangle((0, yy, w * SS, yy + h * SS), radius=h * SS, fill=rgb(trilho) + (255,))
    barra = degrade_h(int(w * SS), int(h * SS), cores)
    mascara = Image.new("L", barra.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, barra.width - 1, barra.height - 1), radius=h * SS, fill=255)
    barra.putalpha(mascara)
    cheio = Image.new("RGBA", camada.size, (0, 0, 0, 0))
    cheio.paste(barra, (0, yy))
    corte = int(w * SS * max(0.0, min(1.0, fracao)))
    if corte < cheio.width:
        ImageDraw.Draw(cheio).rectangle((corte, 0, cheio.width, cheio.height), fill=(0, 0, 0, 0))
    camada.alpha_composite(_brilho(cheio, 10 * SS))
    camada.alpha_composite(cheio)
    if corte > 0:
        # marcador
        d2 = ImageDraw.Draw(camada)
        d2.line((corte, 0, corte, camada.height), fill=(255, 255, 255, 230), width=SS)
    _colar(destino, camada, x, y - 8)


# linha com área tracejada
# ======================================================
def suavizar(pontos, passos=8):
    if len(pontos) < 3:
        return pontos
    curva = []
    p = [pontos[0]] + pontos + [pontos[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for s in range(passos):
            t = s / passos
            t2, t3 = t * t, t * t * t
            curva.append(tuple(
                0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                       + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)
                for k in (0, 1)))
    curva.append(pontos[-1])
    return curva


def linha_area(destino, x, y, w, h, valores, topo, cores, fundo_rgb):
    """Devolve os pontos (coordenadas da imagem final) para o 'hover'."""
    n = len(valores)
    if n < 2:
        return []
    passo = w / (n - 1)
    pontos = [(i * passo, h - h * (v / topo if topo else 0)) for i, v in enumerate(valores)]
    curva = [(px * SS, min(py, h) * SS) for px, py in suavizar(pontos)]
    W, H = int(w * SS), int(h * SS)
    camada = Image.new("RGBA", (W, H + 20 * SS), (0, 0, 0, 0))

    # área: tracejado diagonal + degradê, a desvanecer para baixo
    mascara = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mascara).polygon(curva + [(W, H), (0, H)], fill=255)
    coluna = (230 * (1 - np.arange(H) / H) ** 1.2).astype(np.uint8)
    vertical = Image.fromarray(coluna[:, None], "L").resize((W, H), Image.NEAREST)
    riscas = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(riscas)
    for k in range(-H, W, 7 * SS):
        dr.line((k, H, k + H, 0), fill=255, width=SS)
    alfa = ImageChops.multiply(ImageChops.multiply(mascara, vertical), riscas)
    alfa = ImageChops.add(alfa, ImageChops.multiply(ImageChops.multiply(mascara, vertical), Image.new("L", (W, H), 95)))
    area = degrade_h(W, H, cores)
    area.putalpha(alfa)
    camada.alpha_composite(area, (0, 0))

    # linha com degradê e brilho
    traco = Image.new("L", (W, H), 0)
    ImageDraw.Draw(traco).line(curva, fill=255, width=int(2.6 * SS), joint="curve")
    linha = degrade_h(W, H, cores)
    linha.putalpha(traco)
    camada.alpha_composite(_brilho(linha, 6 * SS), (0, 0))
    camada.alpha_composite(linha, (0, 0))

    # ponto final aceso
    fx, fy = pontos[-1]
    fx, fy = fx * SS, min(fy, h) * SS
    d = ImageDraw.Draw(camada)
    lado = 44 * SS
    halo = Image.new("RGBA", (lado, lado), rgb(cores[-1]) + (0,))
    ImageDraw.Draw(halo).ellipse((lado / 2 - 10 * SS, lado / 2 - 10 * SS, lado / 2 + 10 * SS, lado / 2 + 10 * SS),
                                 fill=rgb(cores[-1]) + (140,))
    halo = _brilho(halo, 8 * SS)
    destino_x, destino_y = int(fx - lado / 2), int(fy - lado / 2)
    corte = halo.crop((max(0, -destino_x), max(0, -destino_y), lado, lado))
    camada.alpha_composite(corte, (max(destino_x, 0), max(destino_y, 0)))
    d.ellipse((fx - 5 * SS, fy - 5 * SS, fx + 5 * SS, fy + 5 * SS), fill=fundo_rgb + (255,),
              outline=rgb(cores[-1]) + (255,), width=int(2.5 * SS))
    _colar(destino, camada, x, y)
    return [(x + px, y + py) for px, py in pontos]


# barras em 'pill' (trilho fino e parte cheia)
# ======================================================
def barras_pill(destino, x, y, w, h, valores, topo, cores, trilho, destaque):
    """Devolve as caixas de cada barra (para o 'hover')."""
    n = len(valores)
    if not n:
        return []
    passo = w / n
    largura = max(min(passo * 0.34, 14), 5)
    camada = _camada(w, h)
    d = ImageDraw.Draw(camada)
    brilhos = _camada(w, h)
    caixas = []
    for i, v in enumerate(valores):
        cx = (i + 0.5) * passo
        x1, x2 = (cx - largura / 2) * SS, (cx + largura / 2) * SS
        d.rounded_rectangle((x1, 0, x2, h * SS), radius=largura * SS / 2, fill=rgb(trilho) + (255,))
        altura = h * (v / topo if topo else 0)
        caixas.append((x + cx - largura / 2, y + h - altura, x + cx + largura / 2, y + h))
        if altura < 1:
            continue
        y1 = (h - altura) * SS
        bh = max(int(h * SS - y1), int(largura * SS))
        y1 = h * SS - bh
        cor = [destaque, destaque] if i == n - 1 else cores
        grad = degrade_h(bh, int(x2 - x1) + 1, cor).rotate(90, expand=True)
        mascara = Image.new("L", grad.size, 0)
        ImageDraw.Draw(mascara).rounded_rectangle((0, 0, grad.width - 1, grad.height - 1),
                                                  radius=largura * SS / 2, fill=255)
        grad.putalpha(mascara)
        camada.alpha_composite(grad, (int(x1), int(y1)))
        if i == n - 1:
            brilhos.alpha_composite(grad, (int(x1), int(y1)))
    camada.alpha_composite(_brilho(brilhos, 10 * SS))
    camada.alpha_composite(brilhos)
    _colar(destino, camada, x, y)
    return caixas


def pill(destino, x, y, w, h, cor_fundo, alfa=255):
    """Pastilha arredondada (para valores e etiquetas sobre o vidro)."""
    camada = _camada(w, h)
    ImageDraw.Draw(camada).rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=h * SS / 2,
                                             fill=rgb(cor_fundo) + (alfa,))
    _colar(destino, camada, x, y)


def circulo_icone(destino, x, y, lado, cor, icone_pil, fundo_alfa=40):
    camada = _camada(lado, lado)
    d = ImageDraw.Draw(camada)
    d.ellipse((0, 0, lado * SS - 1, lado * SS - 1), fill=rgb(cor) + (fundo_alfa,),
              outline=rgb(cor) + (110,), width=SS)
    _colar(destino, camada, x, y)
    if icone_pil is not None:
        i = icone_pil.resize((int(lado * 0.48), int(lado * 0.48)), Image.LANCZOS)
        destino.alpha_composite(i, (int(x + lado * 0.26), int(y + lado * 0.26)))
