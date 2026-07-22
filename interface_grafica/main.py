"""Ponto de entrada da interface gráfica."""

from interface_grafica.login import LoginWindow


def main():

    app = LoginWindow()

    app.mainloop()


if __name__ == "__main__":
    main()