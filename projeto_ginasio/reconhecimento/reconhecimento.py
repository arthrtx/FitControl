import cv2
import json
import os
import shutil
import sys
import threading
import time

import insightface
import numpy as np

from projeto_ginasio.config import RESOURCE_ROOT
from modulos.presencas import registar_presenca


def _obter_root_modelos():
    """Devolve a pasta raiz do insightface com os modelos faciais.

    Em executável congelado usa os modelos empacotados no _internal,
    para funcionar sem internet em qualquer máquina. Em ambiente de
    desenvolvimento usa o folder padrão ~/.insightface.
    """
    if getattr(sys, "frozen", False):
        raiz = os.path.join(RESOURCE_ROOT, "insightface_models")
        if os.path.isdir(os.path.join(raiz, "models", "buffalo_l")):
            return raiz
    return "~/.insightface"


def _garantir_dados_insightface():
    """O insightface assume PyInstaller onefile: o get_object/get_image
    procuram meanshape_68.pkl e máscaras diretamente em _MEIPASS/objects e
    _MEIPASS/images. No build onedir esses dados ficam em
    _MEIPASS/insightface/data/{objects,images}, pelo que a procura falha e o
    lançamento do modelo de marcos termina com AttributeError. Esta função
    copia os dados para o local esperado antes do modelo ser carregado."""
    if not getattr(sys, "frozen", False):
        return
    try:
        origem = os.path.join(RESOURCE_ROOT, "insightface", "data")
        destino_objects = os.path.join(RESOURCE_ROOT, "objects")
        if not os.path.isdir(destino_objects):
            fonte = os.path.join(origem, "objects")
            if os.path.isdir(fonte):
                shutil.copytree(fonte, destino_objects)
        destino_images = os.path.join(RESOURCE_ROOT, "images")
        if not os.path.isdir(destino_images):
            fonte = os.path.join(origem, "images")
            if os.path.isdir(fonte):
                shutil.copytree(fonte, destino_images)
    except Exception as erro:
        print(f"Aviso: não foi possível preparar os dados do insightface: {erro}")


modelo_face = None
_reconhecimento_em_execucao = False
_reconhecimento_lock = threading.Lock()
_reconhecimento_stop_event = threading.Event()
_camera_ativa = None
_janela_face_id = "Face ID - FitControl"
_estado_lock = threading.Lock()
_estado_reconhecimento = {
    "estado": "parado",
    "titulo": "Face ID inativo",
    "detalhe": "Clique no botão 'Iniciar Face ID' para começar o reconhecimento facial.\n"
               "Pressione Q na janela do Face ID para fechar o módulo.",
}
_presencas_registadas_counter = 0


def carregar_modelo():

    global modelo_face

    if modelo_face is None:
        _garantir_dados_insightface()
        _atualizar_estado(
            "a_iniciar",
            "A iniciar Face ID",
            "A carregar o modelo facial."
        )
        print("A carregar modelo facial...")

        modelo_face = insightface.app.FaceAnalysis(
            root=_obter_root_modelos()
        )
        modelo_face.prepare(
            ctx_id=-1,
            det_size=(320, 320)
        )

        print("Modelo facial carregado.")

    return modelo_face


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
    """Retorna True se uma presença foi registada desde a última chamada."""
    global _presencas_registadas_counter
    with _estado_lock:
        counter = _presencas_registadas_counter
    return counter


def parar_reconhecimento():
    """Sinaliza ao thread do Face ID para parar.

    Importante: esta função pode ser chamada a partir do thread principal
    da interface, enquanto o thread do Face ID pode estar, nesse preciso
    momento, dentro de um camera.read(). Libertar ou mexer no objeto
    VideoCapture (ou nas janelas do OpenCV) a partir de outro thread nessa
    altura é o que causava os crashes/bloqueios ao alternar entre Presenças
    e Câmara. Por isso aqui apenas assinalamos o pedido de paragem — quem
    efetivamente liberta a câmera e fecha a janela é sempre o próprio
    thread do reconhecimento, no seu bloco `finally`. Quem chama esta
    função deve depois esperar (join) pelo thread antes de voltar a usar a
    câmera — ver `parar_face_id` em interface_grafica/app.py.
    """

    _reconhecimento_stop_event.set()

    _atualizar_estado(
        "a_parar",
        "A parar Face ID",
        "A libertar a câmera..."
    )


def carregar_alunos():

    try:
        from projeto_ginasio.db_adapter import get_alunos
        return get_alunos()
    except Exception as erro:
        print(
            f"Erro ao carregar alunos do banco de dados: {erro}"
        )
        return []


def preparar_embeddings(alunos):

    validos = []

    for aluno in alunos:
        embedding = aluno.get("embedding")

        if embedding:
            aluno["embedding"] = np.array(
                embedding,
                dtype=np.float32
            )
            validos.append(aluno)

    return validos


def reconhecer_rosto(embedding, alunos):

    embedding = embedding / np.linalg.norm(
        embedding
    )

    melhor_aluno = None
    menor_distancia = float("inf")

    for aluno in alunos:
        distancia = np.linalg.norm(
            embedding - aluno["embedding"]
        )

        if distancia < menor_distancia:
            menor_distancia = distancia
            melhor_aluno = aluno

    if menor_distancia < 0.9:
        return melhor_aluno

    return None


def iniciar_reconhecimento():

    global _reconhecimento_em_execucao
    global _camera_ativa
    global _presencas_registadas_counter

    with _reconhecimento_lock:
        if _reconhecimento_em_execucao:
            print("Face ID já está em execução.")
            return

        _reconhecimento_em_execucao = True
        _reconhecimento_stop_event.clear()

    camera = None

    try:
        print(
            "Sistema Face ID iniciado"
        )
        _atualizar_estado(
            "a_iniciar",
            "A iniciar Face ID",
            "A preparar a webcam e os embeddings faciais."
        )

        ia = carregar_modelo()

        if _reconhecimento_stop_event.is_set():
            return

        alunos = carregar_alunos()
        alunos = preparar_embeddings(
            alunos
        )

        if not alunos:
            print(
                "Nenhum aluno com reconhecimento facial cadastrado."
            )
            _atualizar_estado(
                "sem_alunos",
                "Sem embeddings registados",
                "Nenhum aluno com reconhecimento facial cadastrado.\n"
                "Crie um aluno com foto para ativar o Face ID."
            )
            return

        camera = cv2.VideoCapture(
            0,
            cv2.CAP_DSHOW
        )
        _camera_ativa = camera

        camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            640
        )
        camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            480
        )
        camera.set(
            cv2.CAP_PROP_BUFFERSIZE,
            1
        )

        if not camera.isOpened():
            print(
                "Erro ao abrir câmera"
            )
            _atualizar_estado(
                "erro",
                "Erro na webcam",
                "Não foi possível abrir a câmera para o Face ID."
            )
            return

        ultimo_processamento = 0
        intervalo_ia = 0.5
        presencas_recentes = {}
        ultimo_nome_reconhecido = None
        tempo_ultimo_reconhecimento = 0
        _atualizar_estado(
            "ativo",
            "Face ID ativo",
            "A procurar rostos na webcam.\nPressione Q na janela do Face ID para fechar."
        )

        while not _reconhecimento_stop_event.is_set():
            sucesso, frame = camera.read()

            if _reconhecimento_stop_event.is_set():
                break

            if not sucesso:
                time.sleep(0.05)
                continue

            agora = time.time()
            nome = "Desconhecido"
            detalhe_estado = "A procurar rostos na webcam.\nPressione Q para fechar."

            if agora - ultimo_processamento >= intervalo_ia:
                ultimo_processamento = agora

                pequeno = cv2.resize(
                    frame,
                    (320, 320)
                )
                try:
                    rostos = ia.get(
                        pequeno
                    ) or []
                except Exception as erro_ia:
                    print(
                        f"Erro momentâneo na deteção facial: {erro_ia}"
                    )
                    rostos = []

                if rostos:
                    detalhe_estado = "Rosto detetado, a validar identidade."

                for rosto in rostos:
                    if rosto.embedding is None:
                        continue
                    aluno = reconhecer_rosto(
                        rosto.embedding,
                        alunos
                    )

                    if aluno:
                        nome = aluno["nome"]
                        id_aluno = aluno["id"]

                        ultimo_nome_reconhecido = nome
                        tempo_ultimo_reconhecimento = agora

                        ultima = presencas_recentes.get(
                            id_aluno
                        )

                        if not ultima or agora - ultima > 60:
                            try:
                                resultado = registar_presenca(
                                    id_aluno
                                )
                                print(
                                    f"{nome} -> {resultado}"
                                )
                            except Exception as erro_presenca:
                                print(
                                    f"Erro ao registar presença de {nome}: {erro_presenca}"
                                )
                                resultado = "ERRO_AO_GRAVAR"

                            if resultado != "ERRO_AO_GRAVAR":
                                presencas_recentes[
                                    id_aluno
                                ] = agora

                            if resultado == "OK":
                                detalhe_estado = f"Presença registada para {nome}."
                                with _estado_lock:
                                    _presencas_registadas_counter += 1
                            elif resultado == "PRESENCA_JA_REGISTADA":
                                detalhe_estado = f"{nome} já tem presença registada hoje."
                            elif resultado == "ERRO_AO_GRAVAR":
                                detalhe_estado = f"{nome} identificado, mas houve um erro ao gravar a presença. A tentar novamente."
                            else:
                                detalhe_estado = f"{nome} identificado, resultado: {resultado}."
                        else:
                            detalhe_estado = f"{nome} identificado recentemente."

                        break

                if nome == "Desconhecido" and rostos:
                    detalhe_estado = "Rosto não reconhecido."

            if nome == "Desconhecido" and ultimo_nome_reconhecido and (agora - tempo_ultimo_reconhecimento) < 2:
                nome = ultimo_nome_reconhecido
                detalhe_estado = f"{nome} reconhecido."

            estado_atual = "ativo" if nome != "Desconhecido" else "desconhecido"
            titulo_atual = f"Reconhecido: {nome}" if nome != "Desconhecido" else "Desconhecido"
            _atualizar_estado(
                estado_atual,
                titulo_atual,
                detalhe_estado
            )

            cv2.putText(
                frame,
                nome,
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                _janela_face_id,
                frame
            )

            try:
                if cv2.getWindowProperty(_janela_face_id, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except cv2.error:
                break

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        _reconhecimento_stop_event.set()
        _reconhecimento_em_execucao = False

        if camera is not None:
            try:
                camera.release()
            except Exception:
                pass

        _camera_ativa = None

        try:
            cv2.destroyWindow(_janela_face_id)
        except Exception:
            pass

        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

        _atualizar_estado(
            "parado",
            "Face ID inativo",
            "Clique no botão 'Iniciar Face ID' para voltar a iniciar o reconhecimento facial.\n"
            "Pressione Q na janela do Face ID para fechar o módulo."
        )
