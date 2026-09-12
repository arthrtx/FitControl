from datetime import datetime

from projeto_ginasio.db_adapter import (
    get_alunos, get_alunos_excluidos, get_pagamentos, 
    get_presencas, get_funcionarios, check_and_migrate,
    get_presencas_dia, limpar_presencas_anteriores
)

# Inicializar com dados do banco de dados
check_and_migrate()

alunos = get_alunos()
alunos_excluidos = get_alunos_excluidos()
pagamentos = get_pagamentos()
funcionarios = get_funcionarios()

# As presenças são um histórico diário: a tabela guarda apenas as entradas
# do dia atual. Todos os dias, as entradas anteriores são eliminadas da
# tabela 'presencas' (ficam, de forma permanente, nos Logs do tipo
# 'presenca' — ver o Arquivo de Presenças).
try:
    hoje = datetime.now().strftime("%d/%m/%Y")
    limpar_presencas_anteriores(hoje)
    presencas = get_presencas_dia(hoje)
except Exception:
    presencas = get_presencas()