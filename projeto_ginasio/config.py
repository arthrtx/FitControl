import os
import sys

APP_NAME = "FitControl"
MODULO_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(MODULO_DIR)
EXEC_DIR = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) else PROJECT_ROOT
RESOURCE_ROOT = getattr(sys, "_MEIPASS", PROJECT_ROOT)

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

# Caminhos de arquivos JSON (mantidos para compatibilidade durante migração)
ARQUIVO = os.path.join(DADOS, "alunos.json")
ARQUIVO_LOG = os.path.join(DADOS, "logs.txt")
ARQUIVO_PAGAMENTOS = os.path.join(DADOS, "pagamentos.json")
ARQUIVO_PRESENCAS = os.path.join(DADOS, "presencas.json")
ARQUIVO_ALUNOS_EXCLUIDOS = os.path.join(DADOS, "alunos_excluidos.json")
ARQUIVO_FUNCIONARIOS = os.path.join(DADOS, "funcionarios.json")
ARQUIVO_HISTORICO_ACESSOS = os.path.join(DADOS, "historico_acessos.json")