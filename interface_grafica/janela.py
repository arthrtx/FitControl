import ctypes
import os
import sys

import customtkinter as ctk
from PIL import ImageTk

from interface_grafica.icones import limpar_cache, logo
from projeto_ginasio.config import DADOS

WINDOWS = sys.platform.startswith("win")

# O customtkinter, ao mudar de tema no Windows, esconde e volta a mostrar a
# janela inteira só para trocar a cor da barra de título (a janela "pisca").
# Desliga-se isso e pinta-se a barra diretamente (ver pintar_barra_titulo).
ctk.CTk._deactivate_windows_window_header_manipulation = True
ctk.CTkToplevel._deactivate_windows_window_header_manipulation = True


def _ficheiro_icone():
    caminho = os.path.join(DADOS, "fitcontrol.ico")
    if not os.path.exists(caminho):
        imagem = logo(256, "#3ee59a", "#8f7cff")
        imagem.save(caminho, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)])
    return caminho


def _cor_windows(cor):
    # o Windows quer a cor como 0x00BBGGRR
    r, g, b = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
    return b << 16 | g << 8 | r


def pintar_barra_titulo(janela, escuro, cor_fundo=None, cor_texto=None):
    """Barra de título escura/clara sem esconder a janela.
    No Windows 11 a barra fica mesmo com a cor do menu lateral."""
    if not WINDOWS:
        return
    try:
        janela.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(janela.winfo_id())
        dwm = ctypes.windll.dwmapi

        valor = ctypes.c_int(1 if escuro else 0)
        if dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(valor), ctypes.sizeof(valor)) != 0:
            dwm.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(valor), ctypes.sizeof(valor))

        # Windows 11: cor da barra e do texto (no Windows 10 é ignorado)
        if cor_fundo:
            cor = ctypes.c_int(_cor_windows(cor_fundo))
            dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(cor), ctypes.sizeof(cor))
        if cor_texto:
            cor = ctypes.c_int(_cor_windows(cor_texto))
            dwm.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(cor), ctypes.sizeof(cor))

        # obriga o Windows a redesenhar a moldura já
        SWP_FRAMECHANGED, SWP_NOMOVE, SWP_NOSIZE, SWP_NOZORDER, SWP_NOACTIVATE = 0x20, 0x2, 0x1, 0x4, 0x10
        ctypes.windll.user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE,
        )
    except Exception as erro:
        print(f"Barra de título não alterada: {erro}")


def aplicar_tema_barra(janela):
    from interface_grafica.constants import TEMA, escuro
    pintar_barra_titulo(janela, escuro(), TEMA["sidebar"], TEMA["text"])


def _widget_vivo(callback):
    dono = getattr(callback, "__self__", None)
    if dono is None:
        return True
    try:
        return bool(dono.winfo_exists())
    except Exception:
        return False


def _janela_viva(janela):
    try:
        return bool(janela.winfo_exists())
    except Exception:
        return False


def limpar_rastreadores_ctk():
    """Limpa os rastreadores globais do customtkinter entre janelas.

    Quando uma janela é destruída, o Tk mata os widgets no Tcl mas o
    customtkinter mantém os callbacks e as janelas mortas nas suas
    listas globais (AppearanceModeTracker / ScalingTracker). Com
    logout/login e trocas de tema repetidos essas listas cresciam sem
    fim e cada troca de tema ficava mais lenta. Chamar antes de
    construir a janela seguinte."""
    try:
        from customtkinter.windows.widgets.appearance_mode.appearance_mode_tracker import AppearanceModeTracker
        from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker

        # callbacks de widgets já destruídos
        vivos = [c for c in AppearanceModeTracker.callback_list if _widget_vivo(c)]
        mortos = len(AppearanceModeTracker.callback_list) - len(vivos)
        AppearanceModeTracker.callback_list[:] = vivos

        # raízes mortas: o ciclo de verificação do tema do sistema morreu
        # com elas e a bandeira ficava presa em True
        raizes = [a for a in AppearanceModeTracker.app_list if _janela_viva(a)]
        raizes_mortas = len(AppearanceModeTracker.app_list) - len(raizes)
        AppearanceModeTracker.app_list[:] = raizes
        if raizes_mortas and raizes:
            AppearanceModeTracker.update_loop_running = False
            try:
                raizes[-1].after(AppearanceModeTracker.update_loop_interval, AppearanceModeTracker.update)
                AppearanceModeTracker.update_loop_running = True
            except Exception:
                AppearanceModeTracker.update_loop_running = False
        elif not raizes:
            AppearanceModeTracker.update_loop_running = False

        # janelas mortas do rastreador de escala (DPI)
        mortas = [j for j in ScalingTracker.window_widgets_dict if not _janela_viva(j)]
        for j in mortas:
            ScalingTracker.window_widgets_dict.pop(j, None)
            ScalingTracker.window_dpi_scaling_dict.pop(j, None)
        if mortas and ScalingTracker.window_widgets_dict:
            ScalingTracker.update_loop_running = False
            try:
                viva = next(iter(ScalingTracker.window_widgets_dict))
                viva.after(ScalingTracker.update_loop_interval, ScalingTracker.check_dpi_scaling)
                ScalingTracker.update_loop_running = True
            except Exception:
                ScalingTracker.update_loop_running = False
        elif not ScalingTracker.window_widgets_dict:
            ScalingTracker.update_loop_running = False
    except Exception as erro:
        print(f"Rastreadores do customtkinter não limpos: {erro}")


def preparar_janela(janela, principal=True):
    """Ícone do FitControl + barra de título com as cores do tema."""
    # primeiro deixa-se o customtkinter sem callbacks/janelas mortas da
    # janela anterior (login -> app -> logout -> login ...)
    limpar_rastreadores_ctk()
    if principal:
        # as imagens guardadas pertencem à janela anterior (login -> app)
        limpar_cache()
        from interface_grafica import graficos
        graficos._aneis.clear()
    try:
        if WINDOWS:
            # o customtkinter troca o ícone ~200 ms depois de abrir a janela
            caminho = _ficheiro_icone()
            janela.iconbitmap(caminho)
            janela.after(250, lambda: janela.winfo_exists() and janela.iconbitmap(caminho))
        else:
            janela._icone_tk = ImageTk.PhotoImage(logo(64, "#3ee59a", "#8f7cff"))
            janela.iconphoto(principal, janela._icone_tk)
    except Exception as erro:
        print(f"Ícone da janela não aplicado: {erro}")

    janela.after(20, lambda: janela.winfo_exists() and aplicar_tema_barra(janela))


def congelar(janela):
    """Tira uma 'fotografia' da janela e põe-na por cima de tudo enquanto a
    interface é reconstruída (troca de tema sem se ver a janela a montar-se).
    Devolve o rótulo a remover depois, ou None se não for possível."""
    import tkinter as tk
    try:
        from PIL import ImageGrab
        janela.update_idletasks()
        x, y = janela.winfo_rootx(), janela.winfo_rooty()
        w, h = janela.winfo_width(), janela.winfo_height()
        if WINDOWS:
            imagem = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
        else:
            imagem = ImageGrab.grab(bbox=(x, y, x + w, y + h), xdisplay=os.environ.get("DISPLAY"))
        foto = ImageTk.PhotoImage(imagem)
    except Exception:
        return None
    rotulo = tk.Label(janela, image=foto, bd=0, highlightthickness=0)
    rotulo.imagem = foto
    rotulo.place(x=0, y=0, relwidth=1, relheight=1)
    rotulo.lift()
    return rotulo


def descongelar(janela, rotulo):
    if rotulo is None:
        return
    rotulo.lift()
    janela.update_idletasks()
    # dá tempo aos gráficos (que se desenham logo a seguir) antes de mostrar
    janela.after(140, lambda: rotulo.winfo_exists() and rotulo.destroy())


def cancelar_pendentes(janela):
    """Cancela os 'after' que ainda estão na fila antes de fechar a janela.
    Sem isto aparecem mensagens 'invalid command name ...' na consola."""
    try:
        # cancela-se no próprio Tcl: o after_cancel do tkinter apagaria também
        # o comando Python, que o widget dono tenta apagar outra vez ao ser destruído
        for job in janela.tk.splitlist(janela.tk.call("after", "info")):
            try:
                janela.tk.call("after", "cancel", job)
            except Exception:
                pass
    except Exception:
        pass


def area_util(janela):
    """Área do ecrã sem a barra de tarefas (x1, y1, x2, y2), em píxeis reais."""
    if WINDOWS:
        try:
            class RECT(ctypes.Structure):
                _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long), ("r", ctypes.c_long), ("b", ctypes.c_long)]
            r = RECT()
            if ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0):  # SPI_GETWORKAREA
                return r.l, r.t, r.r, r.b
        except Exception:
            pass
    return 0, 0, janela.winfo_screenwidth(), janela.winfo_screenheight()


def centralizar(janela, largura, altura, margem=40):
    """Abre a janela com o tamanho pedido (encolhendo se o ecrã for pequeno)
    e centrada no ecrã."""
    try:
        escala = janela._get_window_scaling()
    except Exception:
        escala = 1.0
    x1, y1, x2, y2 = area_util(janela)
    largura = int(min(largura, (x2 - x1 - margem) / escala))
    altura = int(min(altura, (y2 - y1 - margem) / escala))
    # a barra de título (~32 px) também conta para ficar mesmo ao centro
    x = x1 + (x2 - x1 - round(largura * escala)) // 2
    y = y1 + max((y2 - y1 - round(altura * escala) - 32) // 2, 0)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
