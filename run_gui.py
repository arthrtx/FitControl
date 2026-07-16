"""Inicia a interface gráfica do Sistema de Gestão de Academia."""

from interface_grafica.utils import setup_paths

setup_paths()

from interface_grafica.main import main

if __name__ == "__main__":
    main()
