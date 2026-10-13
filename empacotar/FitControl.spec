# Empacotamento do FitControl com PyInstaller
# ======================================================
# Gera uma pasta com FitControl.exe que corre em qualquer Windows 10/11
# de 64 bits sem instalar Python nem dependências.
# Usar através do construir.bat (que está nesta mesma pasta).

import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

RAIZ = os.path.abspath(os.path.join(SPECPATH, ".."))
MODELOS = os.path.join(os.path.expanduser("~"), ".insightface", "models", "buffalo_l")
SISTEMA = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")


# ficheiros de dados
# ======================================================
datas = []
datas += collect_data_files("customtkinter")
datas += collect_data_files("reportlab")
datas += collect_data_files("insightface", excludes=["gui/**"])
datas += collect_data_files("cv2", includes=["data/haarcascade_frontalface_default.xml"])

# só os dois modelos que o Face ID usa (deteção + reconhecimento)
for nome in ("det_10g.onnx", "w600k_r50.onnx"):
    caminho = os.path.join(MODELOS, nome)
    if not os.path.exists(caminho):
        sys.exit(f"Falta o modelo {caminho}. Abre o Face ID uma vez no run.bat para o descarregar.")
    datas.append((caminho, "insightface_models/models/buffalo_l"))


# runtime do Visual C++ (para não depender do que está instalado)
# ======================================================
binaries = []
for dll in ("msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll", "vcruntime140.dll",
            "vcruntime140_1.dll", "concrt140.dll", "vcomp140.dll"):
    caminho = os.path.join(SISTEMA, dll)
    if os.path.exists(caminho):
        binaries.append((caminho, "."))


# módulos
# ======================================================
escondidos = (
    collect_submodules("interface_grafica")
    + collect_submodules("modulos")
    + collect_submodules("projeto_ginasio")
    + ["insightface.app", "insightface.model_zoo", "onnxruntime", "PIL._tkinter_finder"]
)

excluidos = [
    "insightface.gui", "matplotlib", "pandas", "torch", "tensorflow", "mxnet",
    "IPython", "jupyter", "notebook", "pytest", "sympy",
    "PyQt5", "PyQt6", "PySide2", "PySide6", "tkinter.test",
]


a = Analysis(
    [os.path.join(RAIZ, "run_gui.py")],
    pathex=[RAIZ],
    binaries=binaries,
    datas=datas,
    hiddenimports=escondidos,
    excludes=excluidos,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FitControl",
    icon=os.path.join(SPECPATH, "fitcontrol.ico"),
    console=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="FitControl",
)
