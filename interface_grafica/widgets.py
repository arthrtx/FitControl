"""Componentes visuais reutilizáveis."""

import customtkinter as ctk

from interface_grafica.constants import TEMA


def btn_primary(master, **kwargs):
    opts = {
        "fg_color": TEMA["accent"],
        "hover_color": TEMA["accent_hover"],
        "corner_radius": TEMA["radius_sm"],
        "height": 34,
    }
    opts.update(kwargs)
    return ctk.CTkButton(master, **opts)


def btn_secondary(master, **kwargs):
    opts = {
        "fg_color": TEMA["surface_alt"],
        "hover_color": TEMA["border"],
        "corner_radius": TEMA["radius_sm"],
        "height": 34,
    }
    opts.update(kwargs)
    return ctk.CTkButton(master, **opts)


def btn_danger(master, **kwargs):
    opts = {
        "fg_color": TEMA["danger"],
        "hover_color": TEMA["danger_hover"],
        "corner_radius": TEMA["radius_sm"],
        "height": 34,
    }
    opts.update(kwargs)
    return ctk.CTkButton(master, **opts)


def styled_entry(master, **kwargs):
    opts = {
        "height": 36,
        "corner_radius": TEMA["radius_sm"],
        "border_width": 1,
        "border_color": TEMA["border"],
        "fg_color": TEMA["input_bg"],
    }
    opts.update(kwargs)
    return ctk.CTkEntry(master, **opts)


def styled_option(master, **kwargs):
    opts = {
        "height": 36,
        "corner_radius": TEMA["radius_sm"],
        "fg_color": TEMA["input_bg"],
        "button_color": TEMA["border"],
        "button_hover_color": TEMA["accent"],
    }
    opts.update(kwargs)
    return ctk.CTkOptionMenu(master, **opts)


def centre_toplevel(janela, master):
    janela.update_idletasks()
    x = master.winfo_x() + (master.winfo_width() - janela.winfo_width()) // 2
    y = master.winfo_y() + (master.winfo_height() - janela.winfo_height()) // 2
    janela.geometry(f"+{x}+{y}")


class PageFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", TEMA["bg"])
        super().__init__(master, **kwargs)


class SurfaceCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", TEMA["surface"])
        kwargs.setdefault("corner_radius", TEMA["radius"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", TEMA["border"])
        super().__init__(master, **kwargs)


class PageHeader(ctk.CTkFrame):
    def __init__(self, master, title, subtitle=None):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        self.esquerda = ctk.CTkFrame(self, fg_color="transparent")
        self.esquerda.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            self.esquerda,
            text=title,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=TEMA["text"],
        ).pack(anchor="w")
        self.subtitle_label = None
        if subtitle:
            self.subtitle_label = ctk.CTkLabel(
                self.esquerda,
                text=subtitle,
                font=ctk.CTkFont(size=12),
                text_color=TEMA["muted"],
                justify="left",
            )
            self.subtitle_label.pack(anchor="w", pady=(2, 0), fill="x")

        self.actions = ctk.CTkFrame(self, fg_color="transparent")
        self.actions.grid(row=0, column=1, sticky="e")
        self.bind("<Configure>", self._relayout)

    def _relayout(self, _event=None):
        largura = max(self.winfo_width(), 1)
        if self.subtitle_label:
            self.subtitle_label.configure(wraplength=max(220, largura - 80))

        if largura < 980:
            self.actions.grid_configure(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        else:
            self.actions.grid_configure(row=0, column=1, columnspan=1, sticky="e", pady=0)


class TablePanel(SurfaceCard):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
