import os
# Caminhos dos ficheiros
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DADOS = os.path.join(BASE_DIR, "dados")
os.makedirs(DADOS, exist_ok=True)

ARQUIVO = os.path.join(DADOS, "alunos.json")
ARQUIVO_LOG = os.path.join(DADOS, "logs.txt")
ARQUIVO_PAGAMENTOS = os.path.join(DADOS, "pagamentos.json")
ARQUIVO_PRESENCAS = os.path.join(DADOS, "presencas.json")
ARQUIVO_ALUNOS_EXCLUIDOS = os.path.join(DADOS, "alunos_excluidos.json")
