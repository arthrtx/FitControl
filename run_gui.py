"""Inicia a interface gráfica do Sistema de Gestão de Academia."""

import os
import sys

# no executável não há consola: as mensagens vão para um ficheiro ao lado do .exe
if getattr(sys, "frozen", False) and (sys.stdout is None or sys.stderr is None):
    try:
        registo = open(os.path.join(os.path.dirname(sys.executable), "fitcontrol.log"),
                       "a", encoding="utf-8", buffering=1)
    except OSError:
        registo = open(os.devnull, "w")
    sys.stdout = sys.stdout or registo
    sys.stderr = sys.stderr or registo
if getattr(sys, "frozen", False):
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(line_buffering=True)
        except (AttributeError, ValueError):
            pass

from interface_grafica.utils import setup_paths

setup_paths()

from interface_grafica.main import main

if __name__ == "__main__":
    main()
