"""Fundos abstratos (tipo 'tinta líquida') gerados na hora com o PIL."""

import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

_cache = {}


def _rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


def fluido(largura, altura, cores, fundo, semente=7, raio=0, grao=True):
    chave = (largura, altura, tuple(cores), fundo, semente, raio, grao)
    if chave in _cache:
        return _cache[chave]

    aleatorio = random.Random(semente)
    pequeno_w, pequeno_h = max(largura // 8, 8), max(altura // 8, 8)
    img = Image.new("RGB", (pequeno_w, pequeno_h), _rgb(fundo))
    d = ImageDraw.Draw(img)

    for i in range(14):
        cor = _rgb(cores[i % len(cores)])
        r = aleatorio.uniform(0.25, 0.6) * max(pequeno_w, pequeno_h)
        x = aleatorio.uniform(-0.1, 1.1) * pequeno_w
        y = aleatorio.uniform(-0.1, 1.1) * pequeno_h
        d.ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), fill=cor)
        # faixas escuras no meio dão o ar de 'tinta a escorrer'
        if i % 4 == 3:
            d.ellipse((x - r * 0.5, y - r * 0.2, x + r * 0.7, y + r * 0.25), fill=_rgb(fundo))

    img = img.filter(ImageFilter.GaussianBlur(max(pequeno_w, pequeno_h) / 9))
    img = img.resize((largura, altura), Image.BICUBIC)

    if grao:
        ruido = np.random.default_rng(semente).normal(0, 7, (altura, largura, 1))
        pixels = np.asarray(img).astype(np.float32) + ruido
        img = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))

    img = img.convert("RGBA")
    if raio:
        mascara = Image.new("L", (largura, altura), 0)
        ImageDraw.Draw(mascara).rounded_rectangle((0, 0, largura - 1, altura - 1), radius=raio, fill=255)
        img.putalpha(mascara)

    _cache[chave] = img
    return img
