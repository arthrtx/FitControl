"""Utilitários e configuração de paths para a interface gráfica."""

import os
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
    return aluno["nome"] if aluno else f"ID {id_aluno}"
