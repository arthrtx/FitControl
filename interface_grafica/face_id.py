"""Carrega o módulo do Face ID (insightface + onnxruntime) num thread.

Importar o insightface demora alguns segundos; feito no thread da
interface, a janela congelava ao abrir a página Presenças."""

import importlib
import sys
import threading
import traceback

NOME = "projeto_ginasio.reconhecimento.reconhecimento"

_lock = threading.Lock()
_thread = None
erro = None


def modulo():
    """Devolve o módulo se já estiver carregado, senão None (não bloqueia)."""
    return sys.modules.get(NOME) if not _a_carregar() else None


def _a_carregar():
    return _thread is not None and _thread.is_alive()


def carregar_em_fundo():
    global _thread
    with _lock:
        if NOME in sys.modules or _a_carregar():
            return
        _thread = threading.Thread(target=_carregar, daemon=True)
        _thread.start()


def _carregar():
    global erro
    try:
        importlib.import_module(NOME)
        erro = None
    except BaseException as e:
        # BaseException: algumas bibliotecas fecham com SystemExit e o
        # ecrã ficava para sempre em "A preparar"
        erro = f"Não foi possível carregar o Face ID: {e}"
        traceback.print_exc()
