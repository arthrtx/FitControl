"""Constantes visuais da interface gráfica."""

import customtkinter as ctk

PLANOS = ["Diário", "Mensal", "Trimestral", "Anual"]

_TEMA_ESCURO = {
    "bg": "#0c0c10",
    "surface": "#15151c",
    "surface_alt": "#1c1c26",
    "border": "#2a2a38",
    "text": "#f4f4f5",
    "muted": "#8b8b9a",
    "accent": "#7c6cff",
    "accent_hover": "#6b5ce7",
    "cyan": "#22d3ee",
    "success": "#34d399",
    "danger": "#f87171",
    "danger_hover": "#ef4444",
    "warning": "#fbbf24",
    "sidebar": "#101016",
    "sidebar_hover": "#1a1a24",
    "sidebar_active": "#7c6cff",
    "sidebar_active_text": "#a89bff",
    "table_bg": "#15151c",
    "table_head": "#1c1c26",
    "table_row_alt": "#18181f",
    "table_select": "#7c6cff",
    "input_bg": "#1c1c26",
    "radius": 16,
    "radius_sm": 10,
    "chart": ["#7c6cff", "#22d3ee", "#a78bfa", "#34d399", "#fb7185", "#fcd34d"],
    "violet": "#a78bfa",
    "on_surface": "#DCE4EE",
    "on_accent": "#DCE4EE",
}

_TEMA_CLARO = {
    "bg": "#f4f4f7",
    "surface": "#ffffff",
    "surface_alt": "#eeeef4",
    "border": "#dcdce6",
    "text": "#16161d",
    "muted": "#6b6b7b",
    "accent": "#6558e8",
    "accent_hover": "#5447d6",
    "cyan": "#0e7490",
    "success": "#047857",
    "danger": "#dc2626",
    "danger_hover": "#b91c1c",
    "warning": "#b45309",
    "sidebar": "#ffffff",
    "sidebar_hover": "#eeeef4",
    "sidebar_active": "#6558e8",
    "sidebar_active_text": "#ffffff",
    "table_bg": "#ffffff",
    "table_head": "#eeeef4",
    "table_row_alt": "#f7f7fa",
    "table_select": "#6558e8",
    "input_bg": "#ffffff",
    "radius": 16,
    "radius_sm": 10,
    "chart": ["#6558e8", "#0891b2", "#7c3aed", "#047857", "#e11d48", "#b45309"],
    "violet": "#7c3aed",
    "on_surface": "#16161d",
    "on_accent": "#ffffff",
}

# Todos os módulos importam esta mesma instância por referência, pelo que as
# alterações feitas em set_tema() são vistas automaticamente em toda a UI.
TEMA = dict(_TEMA_ESCURO)

CORES = {}

_MODO = "dark"


def _sincronizar_cores():
    CORES.clear()
    CORES.update({
        "sidebar": TEMA["sidebar"],
        "sidebar_hover": TEMA["sidebar_hover"],
        "sidebar_active": TEMA["sidebar_active"],
        "accent": TEMA["accent"],
        "card": TEMA["surface"],
        "success": TEMA["success"],
        "warning": TEMA["warning"],
        "danger": TEMA["danger"],
    })


def modo_tema():
    return _MODO


def set_tema(modo):
    """Aplica o tema pedido (mutando TEMA/CORES in place) e devolve o modo."""
    global _MODO

    claro = modo == "light"
    fonte = _TEMA_CLARO if claro else _TEMA_ESCURO

    TEMA.clear()
    TEMA.update(fonte)
    _MODO = "light" if claro else "dark"
    _sincronizar_cores()

    ctk.set_appearance_mode("light" if claro else "dark")
    return _MODO


def alternar_tema():
    return set_tema("light" if _MODO == "dark" else "dark")


_sincronizar_cores()
