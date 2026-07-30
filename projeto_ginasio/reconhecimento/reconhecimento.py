import cv2
import json
import os
import threading
import time

import insightface
import numpy as np

from projeto_ginasio.config import ARQUIVO
from modulos.presencas import registar_presenca


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
    "detalhe": "Abra a página Presenças para iniciar o reconhecimento facial.",
}


def carregar_modelo():

    global modelo_face

    if modelo_face is None:
        _atualizar_estado(
            "a_iniciar",
            "A iniciar Face ID",
            "A carregar o modelo facial."
        )
        print("A carregar modelo facial...")

        modelo_face = insightface.app.FaceAnalysis()
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


def parar_reconhecimento():

    global _camera_ativa

    _reconhecimento_stop_event.set()

    if _camera_ativa is not None:
        try:
            _camera_ativa.release()
        except Exception:
            pass
        finally:
            _camera_ativa = None

    try:
        cv2.destroyWindow(_janela_face_id)
    except Exception:
        pass

    _atualizar_estado(
        "parado",
        "Face ID inativo",
        "Reconhecimento facial parado."
    )


def carregar_alunos():

    if not os.path.exists(ARQUIVO):
        return []

    try:
        with open(
            ARQUIVO,
            "r",
            encoding="utf-8"
        ) as ficheiro:
            return json.load(ficheiro)

    except Exception as erro:
        print(
            f"Erro ao carregar alunos: {erro}"
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
                "Nenhum aluno com reconhecimento facial cadastrado."
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
        _atualizar_estado(
            "ativo",
            "Face ID ativo",
            "A procurar rostos na webcam."
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
            detalhe_estado = "A procurar rostos na webcam."

            if agora - ultimo_processamento >= intervalo_ia:
                ultimo_processamento = agora

                pequeno = cv2.resize(
                    frame,
                    (320, 320)
                )
                rostos = ia.get(
                    pequeno
                )

                if rostos:
                    detalhe_estado = "Rosto detetado, a validar identidade."

                for rosto in rostos:
                    aluno = reconhecer_rosto(
                        rosto.embedding,
                        alunos
                    )

                    if aluno:
                        nome = aluno["nome"]
                        id_aluno = aluno["id"]

                        ultima = presencas_recentes.get(
                            id_aluno
                        )

                        if not ultima or agora - ultima > 60:
                            resultado = registar_presenca(
                                id_aluno
                            )
                            print(
                                f"{nome} -> {resultado}"
                            )
                            presencas_recentes[
                                id_aluno
                            ] = agora
                            if resultado == "OK":
                                detalhe_estado = f"Presença registada para {nome}."
                            elif resultado == "PRESENCA_JA_REGISTADA":
                                detalhe_estado = f"{nome} já tem presença registada hoje."
                            else:
                                detalhe_estado = f"{nome} identificado, resultado: {resultado}."
                        else:
                            detalhe_estado = f"{nome} identificado recentemente."

                        break

                if nome == "Desconhecido" and rostos:
                    detalhe_estado = "Rosto não reconhecido."

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
            "Abra a página Presenças para voltar a iniciar o reconhecimento facial."
        )
