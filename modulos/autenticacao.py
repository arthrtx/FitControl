from datetime import datetime, timedelta

from projeto_ginasio.db_adapter import add_log, get_funcionarios
from modulos import funcionarios as gestao_funcionarios

# CONFIGURAÇÕES
# =====================================================
MAX_TENTATIVAS = 3
TEMPO_BLOQUEIO = 60

funcionarios = []
sessao = None
tentativas_falhadas = {}

# INICIALIZAÇÃO
# =====================================================
def inicializar():
    carregar_funcionarios()


# funcionarios
# =====================================================
def carregar_funcionarios():
    global funcionarios
    # Os funcionários são carregados do SQLite
    funcionarios = get_funcionarios()

    # CRIAR ADMIN TEMPORÁRIO SE NÃO EXISTIR
    if not procurar_utilizador("adm"):
        gestao_funcionarios.criar_funcionario(
            nome="Administrador Temporário",
            usuario="adm",
            senha="adm",
            tipo="Administrador",
        )
        funcionarios = get_funcionarios()


# LOGS (escritos na tabela SQLite 'logs', tipo 'administracao')
# =====================================================
def escrever_log(evento):
    try:
        add_log(evento, tipo="administracao")
    except Exception:
        pass


# AUXILIARES
# =====================================================
def procurar_utilizador(usuario):
    for utilizador in funcionarios:
        if utilizador["usuario"].lower() == usuario.lower():
            return utilizador
    return None


def e_admin_temporario(utilizador):
    """Indica se o utilizador é ainda o administrador temporário original.

    O aviso de administrador temporário deixa de aparecer assim que os
    dados da conta forem alterados, ou quando a conta for excluída.
    """
    if not utilizador:
        return False
    return (
        str(utilizador.get("usuario", "")).lower() == "adm"
        and utilizador.get("senha") == "adm"
        and utilizador.get("nome") == "Administrador Temporário"
    )

# BLOQUEIO DE LOGIN
# =====================================================
def usuario_bloqueado(usuario):
    registo = tentativas_falhadas.get(usuario.lower())
    if not registo:
        return False
    bloqueado = registo.get("bloqueado_ate")
    if not bloqueado:
        return False
    if datetime.now() < bloqueado:
        return True
    tentativas_falhadas[usuario.lower()] = {
        "tentativas": 0,
        "bloqueado_ate": None
    }
    return False


def registar_tentativa_falhada(usuario):
    chave = usuario.lower()
    registo = tentativas_falhadas.get(
        chave,
        {
            "tentativas": 0,
            "bloqueado_ate": None
        }
    )
    registo["tentativas"] += 1
    if registo["tentativas"] >= MAX_TENTATIVAS:
        registo["tentativas"] = 0
        registo["bloqueado_ate"] = (
            datetime.now() +
            timedelta(seconds=TEMPO_BLOQUEIO)
        )
        escrever_log(
            f"Utilizador bloqueado: {usuario}"
        )
    tentativas_falhadas[chave] = registo


def limpar_tentativas(usuario):
    tentativas_falhadas[usuario.lower()] = {
        "tentativas": 0,
        "bloqueado_ate": None
    }


# LOGIN
# =====================================================
def autenticar(usuario, senha):
    global sessao

    carregar_funcionarios()

    if usuario_bloqueado(usuario):
        registo = tentativas_falhadas[usuario.lower()]
        segundos = max(
            0,
            int(
                (
                    registo["bloqueado_ate"] -
                    datetime.now()
                ).total_seconds()
            )
        )
        return (False, "BLOQUEADO", segundos)

    utilizador = procurar_utilizador(usuario)

    if not utilizador:
        registar_tentativa_falhada(usuario)
        escrever_log(f"Login inválido: {usuario}")
        return (False, "Utilizador inexistente.", None)

    if utilizador["senha"] != senha:
        registar_tentativa_falhada(usuario)
        escrever_log(f"senha incorreta: {usuario}")
        restantes = (
            MAX_TENTATIVAS -
            tentativas_falhadas[usuario.lower()]["tentativas"]
        )
        return (False, f"senha incorreta.\nTentativas restantes: {restantes}", None)

    limpar_tentativas(usuario)
    sessao = utilizador

    escrever_log(f"Login: {utilizador['usuario']}")

    return (True, f"Bem-vindo {utilizador['nome']}", utilizador)


# LOGOUT
# =====================================================
def terminar_sessao():
    global sessao
    if not sessao:
        return
    escrever_log(f"Logout: {sessao['usuario']}")
    sessao = None


# SESSÃO
# =====================================================
def sessao_ativa():
    return sessao is not None


def obter_utilizador_atual():
    return sessao


# PERMISSÕES
# =====================================================
def tem_permissao(tipo):
    if not sessao:
        return False
    if sessao.get("tipo") == "Administrador":
        return True
    return sessao.get("tipo") == tipo


def validar_acesso(tipo="Utilizador"):
    if not sessao:
        escrever_log("Acesso negado - sem sessão.")
        return False
    if tem_permissao(tipo):
        escrever_log(
            f"Acesso autorizado: {sessao['usuario']} ({tipo})"
        )
        return True
    escrever_log(f"Acesso negado: {sessao['usuario']}")
    return False


# FUNCIONÁRIOS
# =====================================================
def listar_funcionarios():
    carregar_funcionarios()
    return funcionarios
