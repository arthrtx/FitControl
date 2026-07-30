"""Ponto de entrada da interface gráfica."""

from interface_grafica.app import AcademiaApp
from interface_grafica.login import LoginWindow


def main():
    while True:
        login = LoginWindow()
        login.mainloop()

        utilizador = login.utilizador_autenticado
        if not utilizador:
            break

        app = AcademiaApp(utilizador)
        app.mainloop()

        if not app.reabrir_login:
            break


if __name__ == "__main__":
    main()
