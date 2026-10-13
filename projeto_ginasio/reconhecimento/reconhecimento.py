import glob
import os
import shutil
import sys
import threading
import time
import warnings

import cv2
import insightface
import numpy as np

from projeto_ginasio.config import RESOURCE_ROOT
from projeto_ginasio.Camara import abrir_captura
from modulos.presencas import registar_presenca

# avisos internos do insightface/scikit-image que só sujam a consola
warnings.filterwarnings("ignore", category=FutureWarning)


# afinação
# ======================================================
# semelhança mínima (cosseno) para aceitar um rosto. O antigo limite de
# distância 0.9 era muito apertado em webcams fracas e falhava muito.
LIMIAR_SEMELHANCA = 0.42
# cada passagem da IA ocupa ~150-250 ms de CPU; a 0,5 s o dever de casa fica
# perto de metade e o reconhecimento continua instantâneo do ponto de vista do utilizador
INTERVALO_IA = 0.5
INTERVALO_RECARREGAR = 30
LARGURA_ANALISE = 640
MODULOS_IA = ["detection", "recognition"]


def _obter_root_modelos():
    """No executável usa os modelos embutidos (funciona sem internet).
    Em desenvolvimento usa a pasta padrão ~/.insightface."""
    if getattr(sys, "frozen", False):
        raiz = os.path.join(RESOURCE_ROOT, "insightface_models")
        if os.path.isdir(os.path.join(raiz, "models", "buffalo_l")):
            return raiz
    return os.path.expanduser("~/.insightface")


def _verificar_pasta_modelo(root):
    # se um download anterior foi interrompido a pasta fica criada mas
    # incompleta, e o insightface já não volta a descarregar
    pasta = os.path.join(root, "models", "buffalo_l")
    if not os.path.isdir(pasta):
        return
    if len(glob.glob(os.path.join(pasta, "*.onnx"))) >= 2:
        return
    if getattr(sys, "frozen", False):
        return
    print("Modelo facial incompleto, a descarregar de novo...")
    shutil.rmtree(pasta, ignore_errors=True)
    zip_antigo = pasta + ".zip"
    if os.path.exists(zip_antigo):
        os.remove(zip_antigo)


def _garantir_dados_insightface():
    """No build do PyInstaller os dados do insightface (meanshape_68.pkl,
    máscaras) ficam em _MEIPASS/insightface/data, mas ele procura-os em
    _MEIPASS/objects e _MEIPASS/images. Copia-se para lá antes de carregar."""
    if not getattr(sys, "frozen", False):
        return
    try:
        origem = os.path.join(RESOURCE_ROOT, "insightface", "data")
        for nome in ("objects", "images"):
            destino = os.path.join(RESOURCE_ROOT, nome)
            fonte = os.path.join(origem, nome)
            if not os.path.isdir(destino) and os.path.isdir(fonte):
                shutil.copytree(fonte, destino)
    except Exception as erro:
        print(f"Aviso: não foi possível preparar os dados do insightface: {erro}")


modelo_face = None
_modelo_lock = threading.Lock()
_reconhecimento_em_execucao = False
_reconhecimento_lock = threading.Lock()
_reconhecimento_stop_event = threading.Event()
_estado_lock = threading.Lock()
_estado_reconhecimento = {
    "estado": "parado",
    "titulo": "Face ID inativo",
    "detalhe": "Carregue em 'Iniciar Face ID' para começar o reconhecimento facial.",
}
_presencas_registadas_counter = 0

# último frame da câmara + rostos encontrados, para a interface desenhar
_frame_lock = threading.Lock()
_frame_atual = None
_deteccoes_atuais = []
_numero_frame = 0


# modelo
# ======================================================
def carregar_modelo():

    global modelo_face

    with _modelo_lock:
        if modelo_face is not None:
            return modelo_face

        _garantir_dados_insightface()
        root = _obter_root_modelos()
        _verificar_pasta_modelo(root)

        print("A carregar modelo facial...")
        try:
            modelo = insightface.app.FaceAnalysis(
                root=root,
                allowed_modules=MODULOS_IA,
                providers=["CPUExecutionProvider"],
            )
            modelo.prepare(ctx_id=-1, det_size=(320, 320))
        except Exception as erro:
            raise RuntimeError(
                "Não foi possível carregar o modelo facial. Na primeira "
                "utilização é preciso internet para o descarregar (cerca de 280 MB).\n"
                f"Detalhe: {erro}"
            )

        modelo_face = modelo
        print("Modelo facial carregado.")
        return modelo_face


def maior_rosto(rostos):
    if not rostos:
        return None
    return max(
        rostos,
        key=lambda rosto: (rosto.bbox[2] - rosto.bbox[0]) * (rosto.bbox[3] - rosto.bbox[1])
    )


# estado
# ======================================================
def reconhecimento_ativo():

    return _reconhecimento_em_execucao and not _reconhecimento_stop_event.is_set()


def _atualizar_estado(estado, titulo, detalhe):

    with _estado_lock:
        _estado_reconhecimento["estado"] = estado
        _estado_reconhecimento["titulo"] = titulo
        _estado_reconhecimento["detalhe"] = detalhe


def obter_estado_reconhecimento():

    with _estado_lock:
        return dict(_estado_reconhecimento)


def obter_novas_presencas():
    """Contador que sobe sempre que o Face ID regista uma presença."""
    with _estado_lock:
        return _presencas_registadas_counter


def obter_frame():
    """Devolve (numero, frame BGR, rostos) do último frame lido."""
    with _frame_lock:
        return _numero_frame, _frame_atual, list(_deteccoes_atuais)


def _publicar_frame(frame, deteccoes):

    global _frame_atual, _deteccoes_atuais, _numero_frame

    with _frame_lock:
        _frame_atual = frame
        _deteccoes_atuais = deteccoes
        _numero_frame += 1


def parar_reconhecimento():
    """Só assinala o pedido. Quem liberta a câmara é o próprio thread do
    Face ID (no finally), para não mexer no VideoCapture a meio de um read()."""

    _reconhecimento_stop_event.set()

    if not _reconhecimento_em_execucao:
        return

    _atualizar_estado(
        "a_parar",
        "A parar Face ID",
        "A libertar a câmara..."
    )


# alunos
# ======================================================
def carregar_alunos():

    try:
        from projeto_ginasio.db_adapter import get_alunos
        return get_alunos()
    except Exception as erro:
        print(f"Erro ao carregar alunos do banco de dados: {erro}")
        return []


def preparar_embeddings(alunos):

    validos = []

    for aluno in alunos:
        embedding = aluno.get("embedding")

        if embedding:
            vetor = np.array(embedding, dtype=np.float32)
            norma = np.linalg.norm(vetor)
            if norma == 0:
                continue
            aluno["embedding"] = vetor / norma
            validos.append(aluno)

    return validos


def reconhecer_rosto(embedding, alunos):

    embedding = embedding / np.linalg.norm(embedding)

    melhor_aluno = None
    melhor_semelhanca = -1.0

    for aluno in alunos:
        semelhanca = float(np.dot(embedding, aluno["embedding"]))

        if semelhanca > melhor_semelhanca:
            melhor_semelhanca = semelhanca
            melhor_aluno = aluno

    if melhor_semelhanca >= LIMIAR_SEMELHANCA:
        return melhor_aluno

    return None


def _analisar(ia, frame):
    # reduz sem deformar a imagem (antes era esticada para 320x320, o que
    # estragava o embedding e fazia falhar o reconhecimento)
    altura, largura = frame.shape[:2]
    escala = 1.0
    if largura > LARGURA_ANALISE:
        escala = LARGURA_ANALISE / largura
        frame = cv2.resize(frame, (LARGURA_ANALISE, int(altura * escala)))

    rostos = ia.get(frame) or []
    for rosto in rostos:
        rosto.bbox = rosto.bbox / escala
    return rostos


# ciclo principal
# ======================================================
def iniciar_reconhecimento():

    global _reconhecimento_em_execucao
    global _presencas_registadas_counter

    with _reconhecimento_lock:
        if _reconhecimento_em_execucao:
            print("Face ID já está em execução.")
            return

        _reconhecimento_em_execucao = True
        _reconhecimento_stop_event.clear()

    camera = None
    terminou_com_erro = False

    try:
        _atualizar_estado(
            "a_iniciar",
            "A iniciar Face ID",
            "A carregar o modelo facial e a preparar a câmara."
        )

        ia = carregar_modelo()

        if _reconhecimento_stop_event.is_set():
            return

        alunos = preparar_embeddings(carregar_alunos())

        if not alunos:
            terminou_com_erro = True
            _atualizar_estado(
                "sem_alunos",
                "Sem rostos registados",
                "Nenhum aluno tem foto com consentimento facial.\n"
                "Registe a foto de um aluno para usar o Face ID."
            )
            return

        camera = abrir_captura()

        if not camera.isOpened():
            terminou_com_erro = True
            _atualizar_estado(
                "erro",
                "Câmara indisponível",
                "Não foi possível abrir a câmara. Confirme na página Câmara "
                "qual está selecionada ou se outra aplicação a está a usar."
            )
            return

        ultimo_processamento = 0
        ultima_recarga = time.time()
        ultima_publicacao = 0.0
        presencas_recentes = {}
        deteccoes = []
        falhas_seguidas = 0

        _atualizar_estado(
            "ativo",
            "Face ID ativo",
            "À procura de rostos."
        )

        while not _reconhecimento_stop_event.is_set():
            sucesso, frame = camera.read()

            if _reconhecimento_stop_event.is_set():
                break

            if not sucesso:
                falhas_seguidas += 1
                if falhas_seguidas > 60:
                    terminou_com_erro = True
                    _atualizar_estado(
                        "erro",
                        "A câmara deixou de responder",
                        "Volte a iniciar o Face ID."
                    )
                    break
                time.sleep(0.05)
                continue

            falhas_seguidas = 0
            agora = time.time()

            # alunos novos registados enquanto o Face ID está ligado
            if agora - ultima_recarga > INTERVALO_RECARREGAR:
                ultima_recarga = agora
                novos = preparar_embeddings(carregar_alunos())
                if novos:
                    alunos = novos

            if agora - ultimo_processamento >= INTERVALO_IA:
                ultimo_processamento = agora

                try:
                    rostos = _analisar(ia, frame)
                except Exception as erro_ia:
                    print(f"Erro momentâneo na deteção facial: {erro_ia}")
                    rostos = []

                deteccoes = []
                detalhe = "À procura de rostos."
                estado = "ativo"
                titulo = "Face ID ativo"

                for rosto in rostos:
                    aluno = None
                    if rosto.embedding is not None:
                        aluno = reconhecer_rosto(rosto.embedding, alunos)

                    deteccoes.append({
                        "caixa": [int(v) for v in rosto.bbox],
                        "nome": aluno["nome"] if aluno else "Desconhecido",
                        "conhecido": aluno is not None,
                    })

                    if not aluno:
                        if estado != "reconhecido":
                            estado = "desconhecido"
                            titulo = "Rosto não reconhecido"
                            detalhe = "Aproxime-se da câmara e olhe de frente."
                        continue

                    nome = aluno["nome"]
                    id_aluno = aluno["id"]
                    estado = "reconhecido"
                    titulo = f"Reconhecido: {nome}"

                    ultima = presencas_recentes.get(id_aluno)

                    if ultima and agora - ultima <= 60:
                        detalhe = f"{nome} identificado recentemente."
                        continue

                    try:
                        resultado = registar_presenca(id_aluno)
                    except Exception as erro_presenca:
                        print(f"Erro ao registar presença de {nome}: {erro_presenca}")
                        resultado = "ERRO_AO_GRAVAR"

                    if resultado == "OK":
                        presencas_recentes[id_aluno] = agora
                        detalhe = f"Presença registada para {nome}."
                        with _estado_lock:
                            _presencas_registadas_counter += 1
                    elif resultado == "ERRO_AO_GRAVAR":
                        detalhe = f"{nome} identificado, mas houve um erro ao gravar. A tentar de novo."
                    else:
                        presencas_recentes[id_aluno] = agora
                        detalhe = f"{nome} identificado ({resultado})."

                _atualizar_estado(estado, titulo, detalhe)

            # o visor vai buscar o frame ~30 vezes por segundo; publicar no
            # máximo a cada 50 ms dá ~15 imagens/segundos e poupa CPU
            if agora - ultima_publicacao >= 0.05:
                ultima_publicacao = agora
                _publicar_frame(frame, deteccoes)

    except Exception as erro:
        terminou_com_erro = True
        print(f"Erro no Face ID: {erro}")
        _atualizar_estado("erro", "Erro no Face ID", str(erro))

    finally:
        _reconhecimento_stop_event.set()
        _reconhecimento_em_execucao = False

        if camera is not None:
            try:
                camera.release()
            except Exception:
                pass

        _publicar_frame(None, [])

        if not terminou_com_erro:
            _atualizar_estado(
                "parado",
                "Face ID inativo",
                "Carregue em 'Iniciar Face ID' para começar o reconhecimento facial."
            )
