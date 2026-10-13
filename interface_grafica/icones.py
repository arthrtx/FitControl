"""Ícones de linha desenhados com o PIL (sem ficheiros de imagem externos).

Cada ícone é desenhado numa grelha de 96x96 e reduzido, o que dá cantos
suaves. Ficam em cache por (nome, cor, tamanho)."""

import math

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter

G = 96
TRACO = 7

_cache = {}


def _rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


# primitivas
# ======================================================
def _linha(d, pontos, cor, w=TRACO):
    d.line(pontos, fill=cor, width=w, joint="curve")
    r = w / 2
    for x, y in (pontos[0], pontos[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=cor)


def _circulo(d, cx, cy, r, cor, w=TRACO):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=cor, width=w)


def _caixa(d, x1, y1, x2, y2, cor, raio=10, w=TRACO):
    d.rounded_rectangle((x1, y1, x2, y2), radius=raio, outline=cor, width=w)


def _arco(d, cx, cy, r, inicio, fim, cor, w=TRACO):
    d.arc((cx - r, cy - r, cx + r, cy + r), inicio, fim, fill=cor, width=w)
    for ang in (inicio, fim):
        a = math.radians(ang)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=cor)


# desenhos
# ======================================================
def _casa(d, c):
    _linha(d, [(14, 46), (48, 18), (82, 46)], c)
    _linha(d, [(24, 40), (24, 80), (72, 80), (72, 40)], c)
    _linha(d, [(40, 80), (40, 60), (56, 60), (56, 80)], c)


def _alunos(d, c):
    _circulo(d, 38, 32, 13, c)
    _arco(d, 38, 82, 26, 200, 340, c)
    _circulo(d, 66, 38, 9, c, 6)
    _arco(d, 70, 80, 18, 215, 330, c, 6)


def _utilizador(d, c):
    _circulo(d, 48, 32, 15, c)
    _arco(d, 48, 88, 32, 205, 335, c)


def _funcionarios(d, c):
    _caixa(d, 20, 18, 76, 82, c, 12)
    _circulo(d, 48, 42, 10, c, 6)
    _linha(d, [(34, 66), (62, 66)], c)
    _linha(d, [(40, 10), (56, 10)], c)


def _arquivo(d, c):
    _caixa(d, 12, 18, 84, 36, c, 6)
    _linha(d, [(20, 36), (20, 80), (76, 80), (76, 36)], c)
    _linha(d, [(38, 52), (58, 52)], c)


def _escudo(d, c):
    pts = [(48, 12), (78, 24), (76, 52), (48, 84), (20, 52), (18, 24), (48, 12)]
    d.line(pts, fill=c, width=TRACO, joint="curve")
    _linha(d, [(34, 48), (44, 58), (62, 38)], c)


def _cartao(d, c):
    _caixa(d, 12, 22, 84, 74, c, 12)
    _linha(d, [(14, 40), (82, 40)], c)
    _linha(d, [(26, 60), (42, 60)], c)


def _visto(d, c):
    _circulo(d, 48, 48, 34, c)
    _linha(d, [(32, 49), (43, 60), (64, 37)], c)


def _relogio(d, c):
    _circulo(d, 48, 48, 34, c)
    _linha(d, [(48, 28), (48, 49), (62, 58)], c)


def _camara(d, c):
    _caixa(d, 10, 30, 86, 78, c, 14)
    _linha(d, [(32, 30), (38, 20), (58, 20), (64, 30)], c)
    _circulo(d, 48, 54, 13, c)


def _sair(d, c):
    _linha(d, [(44, 16), (20, 16), (20, 80), (44, 80)], c)
    _linha(d, [(38, 48), (82, 48)], c)
    _linha(d, [(66, 32), (82, 48), (66, 64)], c)


def _sino(d, c):
    d.line([(20, 68), (26, 58), (26, 40)], fill=c, width=TRACO, joint="curve")
    d.line([(76, 68), (70, 58), (70, 40)], fill=c, width=TRACO, joint="curve")
    _arco(d, 48, 40, 22, 180, 360, c)
    _linha(d, [(16, 68), (80, 68)], c)
    _arco(d, 48, 74, 9, 20, 160, c)


def _sol(d, c):
    _circulo(d, 48, 48, 15, c)
    for i in range(8):
        a = math.radians(i * 45)
        _linha(d, [(48 + 26 * math.cos(a), 48 + 26 * math.sin(a)),
                   (48 + 36 * math.cos(a), 48 + 36 * math.sin(a))], c, 6)


def _lua(d, c):
    lua = Image.new("L", (G, G), 0)
    m = ImageDraw.Draw(lua)
    m.ellipse((14, 14, 82, 82), fill=255)
    m.ellipse((34, 2, 98, 66), fill=0)
    oco = Image.new("L", (G, G), 0)
    m2 = ImageDraw.Draw(oco)
    m2.ellipse((21, 21, 75, 75), fill=255)
    m2.ellipse((27, -5, 105, 73), fill=255)
    anel = Image.composite(Image.new("L", (G, G), 0), lua, oco)
    d._image.paste(Image.new("RGBA", (G, G), c), (0, 0), anel)


def _pesquisa(d, c):
    _circulo(d, 42, 42, 24, c)
    _linha(d, [(60, 60), (80, 80)], c)


def _mais(d, c):
    _linha(d, [(48, 20), (48, 76)], c)
    _linha(d, [(20, 48), (76, 48)], c)


def _editar(d, c):
    d.line([(26, 70), (66, 30), (76, 40), (36, 80), (22, 82), (26, 70)], fill=c, width=TRACO, joint="curve")
    _linha(d, [(58, 38), (68, 48)], c, 6)


def _lixo(d, c):
    _linha(d, [(16, 28), (80, 28)], c)
    _linha(d, [(38, 28), (40, 16), (56, 16), (58, 28)], c)
    _linha(d, [(24, 28), (28, 82), (68, 82), (72, 28)], c)
    _linha(d, [(42, 44), (42, 66)], c, 6)
    _linha(d, [(54, 44), (54, 66)], c, 6)


def _atualizar(d, c):
    _arco(d, 48, 48, 30, 30, 300, c)
    _linha(d, [(62, 16), (76, 22), (72, 38)], c)


def _restaurar(d, c):
    _arco(d, 48, 50, 30, 210, 500, c)
    _linha(d, [(16, 22), (20, 36), (34, 32)], c)


def _ficheiro(d, c):
    d.line([(24, 12), (58, 12), (74, 28), (74, 84), (24, 84), (24, 12)], fill=c, width=TRACO, joint="curve")
    _linha(d, [(56, 14), (56, 30), (72, 30)], c, 6)
    _linha(d, [(36, 50), (62, 50)], c, 6)
    _linha(d, [(36, 66), (54, 66)], c, 6)


def _download(d, c):
    _linha(d, [(48, 14), (48, 60)], c)
    _linha(d, [(30, 44), (48, 62), (66, 44)], c)
    _linha(d, [(16, 66), (16, 80), (80, 80), (80, 66)], c)


def _olho(d, c):
    _arco(d, 48, 78, 44, 225, 315, c)
    _arco(d, 48, 18, 44, 45, 135, c)
    _circulo(d, 48, 48, 11, c)


def _olho_fechado(d, c):
    _olho(d, c)
    _linha(d, [(18, 80), (78, 16)], c)


def _cadeado(d, c):
    _caixa(d, 18, 42, 78, 84, c, 10)
    _arco(d, 48, 42, 18, 180, 360, c)
    _linha(d, [(30, 42), (30, 40)], c)
    _linha(d, [(48, 58), (48, 68)], c)


def _rosto(d, c):
    for x, y, sx, sy in ((14, 14, 1, 1), (82, 14, -1, 1), (14, 82, 1, -1), (82, 82, -1, -1)):
        _linha(d, [(x, y + sy * 18), (x, y), (x + sx * 18, y)], c)
    _linha(d, [(38, 38), (38, 44)], c)
    _linha(d, [(58, 38), (58, 44)], c)
    _arco(d, 48, 50, 15, 30, 150, c)


def _play(d, c):
    d.polygon([(30, 18), (78, 48), (30, 78)], fill=c)


def _parar(d, c):
    d.rounded_rectangle((24, 24, 72, 72), radius=8, fill=c)


def _menu_esq(d, c):
    _caixa(d, 12, 16, 84, 80, c, 12)
    _linha(d, [(38, 18), (38, 78)], c)
    _linha(d, [(64, 38), (54, 48), (64, 58)], c, 6)


def _menu_dir(d, c):
    _caixa(d, 12, 16, 84, 80, c, 12)
    _linha(d, [(38, 18), (38, 78)], c)
    _linha(d, [(54, 38), (64, 48), (54, 58)], c, 6)


def _carteira(d, c):
    _caixa(d, 12, 26, 84, 78, c, 12)
    _linha(d, [(20, 26), (60, 14), (66, 26)], c)
    d.ellipse((60, 46, 72, 58), fill=c)


def _haltere(d, c):
    _linha(d, [(30, 48), (66, 48)], c)
    for x in (18, 26, 70, 78):
        h = 20 if x in (26, 70) else 12
        _linha(d, [(x, 48 - h), (x, 48 + h)], c)


def _grafico(d, c):
    _linha(d, [(14, 14), (14, 82), (82, 82)], c)
    _linha(d, [(26, 64), (44, 44), (58, 56), (80, 28)], c)


def _info(d, c):
    _circulo(d, 48, 48, 34, c)
    _linha(d, [(48, 44), (48, 64)], c)
    d.ellipse((44, 28, 52, 36), fill=c)


def _alerta(d, c):
    d.line([(48, 14), (84, 78), (12, 78), (48, 14)], fill=c, width=TRACO, joint="curve")
    _linha(d, [(48, 38), (48, 56)], c)
    d.ellipse((44, 63, 52, 71), fill=c)


def _fechar(d, c):
    _linha(d, [(26, 26), (70, 70)], c)
    _linha(d, [(70, 26), (26, 70)], c)


def _privacidade(d, c):
    _escudo_base = [(48, 12), (78, 24), (76, 52), (48, 84), (20, 52), (18, 24), (48, 12)]
    d.line(_escudo_base, fill=c, width=TRACO, joint="curve")
    _caixa(d, 36, 46, 60, 66, c, 4, 6)
    _arco(d, 48, 46, 8, 180, 360, c, 6)


DESENHOS = {
    "casa": _casa, "alunos": _alunos, "utilizador": _utilizador,
    "funcionarios": _funcionarios, "arquivo": _arquivo, "escudo": _escudo,
    "cartao": _cartao, "visto": _visto, "relogio": _relogio, "camara": _camara,
    "sair": _sair, "sino": _sino, "sol": _sol, "lua": _lua, "pesquisa": _pesquisa,
    "mais": _mais, "editar": _editar, "lixo": _lixo, "atualizar": _atualizar,
    "restaurar": _restaurar, "ficheiro": _ficheiro, "download": _download,
    "olho": _olho, "olho_fechado": _olho_fechado, "cadeado": _cadeado,
    "rosto": _rosto, "play": _play, "parar": _parar, "menu_esq": _menu_esq,
    "menu_dir": _menu_dir, "carteira": _carteira, "haltere": _haltere,
    "grafico": _grafico, "info": _info, "alerta": _alerta, "fechar": _fechar,
    "privacidade": _privacidade,
}


def limpar_cache():
    # as imagens ficam presas à janela Tk que as criou; ao abrir uma janela
    # principal nova (login -> app -> login) é preciso criá-las de novo
    _cache.clear()


def imagem(nome, cor, px=48):
    base = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    DESENHOS[nome](d, _rgb(cor) + (255,))
    return base.resize((px, px), Image.LANCZOS)


def icone(nome, cor, tamanho=18):
    chave = (nome, cor, tamanho)
    if chave not in _cache:
        img = imagem(nome, cor, tamanho * 3)
        _cache[chave] = ctk.CTkImage(light_image=img, dark_image=img, size=(tamanho, tamanho))
    return _cache[chave]


# logótipo
# ======================================================
def logo(px, cor1, cor2, cor_icone="#ffffff"):
    """Quadrado arredondado com degradê e o haltere por cima."""
    escala = 4
    lado = px * escala
    a, b = _rgb(cor1), _rgb(cor2)

    grad = Image.new("RGBA", (lado, lado))
    linha = Image.new("RGBA", (lado * 2, 1))
    for x in range(lado * 2):
        t = x / (lado * 2 - 1)
        linha.putpixel((x, 0), tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,))
    linha = linha.resize((lado * 2, lado * 2))
    grad = linha.rotate(45, resample=Image.BICUBIC).crop((lado // 2, lado // 2, lado // 2 + lado, lado // 2 + lado))

    mascara = Image.new("L", (lado, lado), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, lado - 1, lado - 1), radius=int(lado * 0.3), fill=255)
    final = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    final.paste(grad, (0, 0), mascara)

    simbolo = imagem("haltere", cor_icone, int(lado * 0.7))
    final.alpha_composite(simbolo, (int(lado * 0.15), int(lado * 0.15)))
    return final.resize((px, px), Image.LANCZOS)


def logo_ctk(tamanho, cor1, cor2, cor_icone="#ffffff"):
    chave = ("logo", cor1, cor2, cor_icone, tamanho)
    if chave not in _cache:
        img = logo(tamanho * 3, cor1, cor2, cor_icone)
        _cache[chave] = ctk.CTkImage(light_image=img, dark_image=img, size=(tamanho, tamanho))
    return _cache[chave]


def brilho(largura, altura, cor, fundo):
    """Barrinha com brilho (como o indicador do menu nas referências)."""
    escala = 3
    w, h = largura * escala, altura * escala
    img = Image.new("RGBA", (w, h), _rgb(fundo) + (0,))
    camada = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    barra_w = 3 * escala
    x = w - barra_w - 2 * escala
    d.rounded_rectangle((x, h * 0.18, x + barra_w, h * 0.82), radius=barra_w, fill=_rgb(cor) + (255,))
    halo = camada.filter(ImageFilter.GaussianBlur(7 * escala))
    halo2 = camada.filter(ImageFilter.GaussianBlur(3 * escala))
    img.alpha_composite(halo)
    img.alpha_composite(halo2)
    img.alpha_composite(camada)
    img = img.resize((largura * 2, altura * 2), Image.LANCZOS)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(largura, altura))
