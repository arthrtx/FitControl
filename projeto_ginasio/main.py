from modulos import gestao_alunos
from modulos import pagamentos
from modulos import presencas
from modulos import estatistica
from modulos import funcionarios
from modulos import privacidade

# inicialização
# ======================================================
def inicializar():
    gestao_alunos.carregar_alunos()
    gestao_alunos.carregar_alunos_excluidos()
    pagamentos.carregar_pagamentos()
    presencas.carregar_presencas()
    gestao_alunos.limpar_alunos_expirados()
    funcionarios.carregar_funcionarios()
    privacidade.limpar_logs_antigos()

if __name__ == "__main__":
    inicializar()