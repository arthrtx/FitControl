"""Ponto de entrada da interface gráfica."""

import os
import traceback
from datetime import datetime

from interface_grafica.app import AcademiaApp
from interface_grafica.login import LoginWindow
from projeto_ginasio.config import DADOS

# se a aplicação falhar sempre seguida, não fica em loop infinito
MAX_FALHAS_CONSECUTIVAS = 3


def _registrar_erro(texto):
    """Guarda o erro num ficheiro para diagnosticar sem partir a app."""
    try:
        caminho = os.path.join(DADOS, "erros_interface.log")
        with open(caminho, "a", encoding="utf-8") as f:
            f.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} =====\n{texto}\n")
    except Exception:
        pass


def _fechar_janela_pendente():
    """Fecha uma janela que ficou a meio (construção incompleta)."""
    try:
        import tkinter as tk
        raiz = tk._default_root
        if raiz is not None:
            raiz.destroy()
    except Exception:
        pass


def main():
    falhas = 0
    while True:
        # login
        try:
            login = LoginWindow()
            login.mainloop()
            utilizador = login.utilizador_autenticado
        except Exception:
            falhas += 1
            _registrar_erro(traceback.format_exc())
            traceback.print_exc()
            _fechar_janela_pendente()
            if falhas >= MAX_FALHAS_CONSECUTIVAS:
                break
            continue

        if not utilizador:
            break

        # aplicação principal: qualquer erro aí não mata o programa —
        # fica registado e volta-se ao login para tentar de novo
        try:
            app = AcademiaApp(utilizador)
            app.mainloop()
            reabrir = app.reabrir_login
            falhas = 0
        except Exception:
            falhas += 1
            _registrar_erro(traceback.format_exc())
            traceback.print_exc()
            _fechar_janela_pendente()
            if falhas >= MAX_FALHAS_CONSECUTIVAS:
                break
            continue

        if not reabrir:
            break


if __name__ == "__main__":
    main()
