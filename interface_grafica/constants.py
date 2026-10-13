import customtkinter as ctk

from interface_grafica.utils import ler_preferencia, guardar_preferencia

PLANOS = ["Diário", "Mensal", "Trimestral", "Anual"]
VERSAO = "5.0"


# cores
# ======================================================
_ESCURO = {
    "bg": "#09090c",
    "sidebar": "#0e0e12",
    "surface": "#141419",
    "surface_alt": "#1c1c23",
    "surface_hover": "#23232c",
    "border": "#24242d",
    "border_forte": "#33333e",
    "text": "#f3f3f6",
    "muted": "#8b8b98",
    "subtle": "#5d5d6b",
    "accent": "#3ee59a",
    "accent_hover": "#31cc87",
    "accent_suave": "#15281f",
    "on_accent": "#04120b",
    "magenta": "#ff3d8b",
    "violet": "#8f7cff",
    "amber": "#ffb547",
    "cyan": "#4cc9f0",
    "danger": "#ff5468",
    "danger_hover": "#e8455a",
    "danger_suave": "#2a1418",
    "warning": "#ffb547",
    "input_bg": "#101015",
    "table_alt": "#17171d",
    "table_select": "#1f3329",
    "sombra": "#000000",
    "seg_sel": "#2e2e3a",
}

_CLARO = {
    "bg": "#eeeef2",
    "sidebar": "#f8f8fa",
    "surface": "#ffffff",
    "surface_alt": "#f1f1f5",
    "surface_hover": "#e8e8ee",
    "border": "#e1e1e8",
    "border_forte": "#cfcfd9",
    "text": "#121217",
    "muted": "#6b6b78",
    "subtle": "#a0a0ad",
    "accent": "#0fa968",
    "accent_hover": "#0c9159",
    "accent_suave": "#e2f6ec",
    "on_accent": "#ffffff",
    "magenta": "#e0287a",
    "violet": "#6a55f0",
    "amber": "#d98a00",
    "cyan": "#0a8fb3",
    "danger": "#e5354a",
    "danger_hover": "#c92a3e",
    "danger_suave": "#fde8eb",
    "warning": "#d98a00",
    "input_bg": "#f7f7fa",
    "table_alt": "#f8f8fb",
    "table_select": "#dcf3e7",
    "sombra": "#c9c9d3",
    "seg_sel": "#ffffff",
}

RAIO = 18
RAIO_PEQ = 11

# todos os ficheiros importam este mesmo dicionário, por isso basta
# alterá-lo aqui e reconstruir a interface para mudar de tema
TEMA = {}
_modo = "dark"


def modo_tema():
    return _modo


def escuro():
    return _modo == "dark"


def set_tema(modo):
    global _modo

    _modo = "light" if modo == "light" else "dark"

    TEMA.clear()
    TEMA.update(_CLARO if _modo == "light" else _ESCURO)
    TEMA["chart"] = [TEMA["accent"], TEMA["magenta"], TEMA["violet"], TEMA["amber"], TEMA["cyan"]]

    ctk.set_appearance_mode(_modo)
    guardar_preferencia("tema", _modo)
    return _modo


def alternar_tema():
    return set_tema("light" if _modo == "dark" else "dark")


def misturar(cor1, cor2, quanto):
    """Mistura duas cores hex (quanto=0 -> cor1, 1 -> cor2)."""
    a = [int(cor1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(cor2[i:i + 2], 16) for i in (1, 3, 5)]
    c = [round(x + (y - x) * quanto) for x, y in zip(a, b)]
    return "#%02x%02x%02x" % tuple(c)


set_tema(ler_preferencia("tema", "dark"))
