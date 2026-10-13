"""Utilitários e configuração de paths para a interface gráfica."""

import json
import os
import subprocess
import sys
import unicodedata

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setup_paths():
    """Garante que a raiz do projeto fica acessível para imports de pacotes."""
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)


def sem_acentos(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(caractere for caractere in texto if not unicodedata.combining(caractere)).lower()


def aluno_por_id(id_aluno):
    from modulos import gestao_alunos

    for aluno in gestao_alunos.alunos:
        if aluno["id"] == id_aluno:
            return aluno
    return None


def nome_aluno(id_aluno):
    aluno = aluno_por_id(id_aluno)
    if aluno:
        return aluno["nome"]

    from modulos import gestao_alunos
    for arquivado in gestao_alunos.alunos_excluidos:
        if arquivado["id"] == id_aluno:
            return f"{arquivado['nome']} (arquivado)"
    return f"Aluno #{id_aluno} (apagado)"


def euros(valor):
    texto = f"{float(valor or 0):,.2f}"
    return texto.replace(",", " ").replace(".", ",") + " €"


def iniciais(nome):
    partes = [p for p in str(nome or "").split() if p]
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][0].upper()
    return (partes[0][0] + partes[-1][0]).upper()


def tem_foto(aluno):
    foto = (aluno or {}).get("foto")
    return bool(foto) and foto != "sem_foto" and os.path.exists(foto)


def abrir_ficheiro(caminho):
    if sys.platform.startswith("win"):
        os.startfile(caminho)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", caminho])
    else:
        subprocess.Popen(["xdg-open", caminho])


# preferências (tema, menu recolhido)
# ======================================================
def _caminho_preferencias():
    from projeto_ginasio.config import DADOS
    return os.path.join(DADOS, "preferencias.json")


def ler_preferencia(chave, padrao=None):
    try:
        with open(_caminho_preferencias(), "r", encoding="utf-8") as ficheiro:
            return json.load(ficheiro).get(chave, padrao)
    except (OSError, ValueError):
        return padrao


def guardar_preferencia(chave, valor):
    caminho = _caminho_preferencias()
    try:
        with open(caminho, "r", encoding="utf-8") as ficheiro:
            dados = json.load(ficheiro)
    except (OSError, ValueError):
        dados = {}

    dados[chave] = valor
    try:
        with open(caminho, "w", encoding="utf-8") as ficheiro:
            json.dump(dados, ficheiro, indent=2)
    except OSError:
        pass
