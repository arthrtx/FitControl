"""Interface gráfica do Sistema de Gestão de Academia."""

__all__ = ["AcademiaApp"]


def __getattr__(name):
    if name == "AcademiaApp":
        from interface_grafica.app import AcademiaApp

        return AcademiaApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
