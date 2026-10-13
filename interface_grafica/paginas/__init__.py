from interface_grafica.paginas.dashboard import PaginaDashboard
from interface_grafica.paginas.alunos import PaginaAlunos
from interface_grafica.paginas.pagamentos import PaginaPagamentos
from interface_grafica.paginas.presencas import PaginaPresencas
from interface_grafica.paginas.arquivos import PaginaArquivoPresencas, PaginaArquivoAlunos
from interface_grafica.paginas.sistema import PaginaFuncionarios, PaginaAdministracao
from interface_grafica.paginas.camara import PaginaCamara

# as páginas só são criadas na primeira vez que se abrem
PAGINAS = {
    "dashboard": PaginaDashboard,
    "alunos": PaginaAlunos,
    "pagamentos": PaginaPagamentos,
    "presencas": PaginaPresencas,
    "arq_presencas": PaginaArquivoPresencas,
    "excluidos": PaginaArquivoAlunos,
    "funcionarios": PaginaFuncionarios,
    "administracao": PaginaAdministracao,
    "camera": PaginaCamara,
}
