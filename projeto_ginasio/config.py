import os
import shutil
import sys

APP_NAME = "FitControl"
MODULO_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(MODULO_DIR)
EXEC_DIR = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) else PROJECT_ROOT
RESOURCE_ROOT = getattr(sys, "_MEIPASS", PROJECT_ROOT)
DADOS_EMBUTIDOS = (
    os.path.join(RESOURCE_ROOT, "projeto_ginasio", "dados")
    if getattr(sys, "frozen", False)
    else os.path.join(MODULO_DIR, "dados")
)

# Pasta onde ficam os dados graváveis da aplicação
DADOS = (
    os.path.join(EXEC_DIR, "dados")
    if getattr(sys, "frozen", False)
    else os.path.join(MODULO_DIR, "dados")
)
PASTA_ARQUIVOS = os.path.join(DADOS, "arquivos")
PASTA_FACES = os.path.join(DADOS, "faces")
PASTA_CAPTURAS = os.path.join(DADOS, "capturas")
PASTA_VIDEOS = os.path.join(DADOS, "videos")

for pasta in (DADOS, PASTA_ARQUIVOS, PASTA_FACES, PASTA_CAPTURAS, PASTA_VIDEOS):
    os.makedirs(pasta, exist_ok=True)


def _copiar_dados_iniciais():
    if not getattr(sys, "frozen", False):
        return

    ficheiros_iniciais = (
        "alunos.json",
        "alunos_excluidos.json",
        "funcionarios.json",
        "logs.txt",
        "pagamentos.json",
        "presencas.json",
        "historico_acessos.json",
    )

    for nome in ficheiros_iniciais:
        origem = os.path.join(DADOS_EMBUTIDOS, nome)
        destino = os.path.join(DADOS, nome)
        if os.path.exists(origem) and not os.path.exists(destino):
            shutil.copy2(origem, destino)


_copiar_dados_iniciais()

# Ficheiros de dados
ARQUIVO = os.path.join(DADOS, "alunos.json")
ARQUIVO_LOG = os.path.join(DADOS, "logs.txt")
ARQUIVO_PAGAMENTOS = os.path.join(DADOS, "pagamentos.json")
ARQUIVO_PRESENCAS = os.path.join(DADOS, "presencas.json")
ARQUIVO_ALUNOS_EXCLUIDOS = os.path.join(DADOS, "alunos_excluidos.json")
ARQUIVO_FUNCIONARIOS = os.path.join(DADOS, "funcionarios.json")
