import cv2 as cv
import os
import json
from datetime import datetime

from projeto_ginasio.config import (
    PASTA_CAPTURAS,
    PASTA_FACES,
    PASTA_VIDEOS,
)

# Ajusta este caminho para uma pasta de dados/config que já exista no teu projeto
CAMINHO_CONFIG_CAMERA = os.path.join(os.path.dirname(PASTA_FACES), "camera_config.json")

_CASCADE_PATH = cv.data.haarcascades + "haarcascade_frontalface_default.xml"
_face_cascade = cv.CascadeClassifier(_CASCADE_PATH)


# ---------- Configuração persistente ----------

def carregar_config_camera():
    padrao = {"indice": 0, "largura": 640, "altura": 480}
    if not os.path.exists(CAMINHO_CONFIG_CAMERA):
        return padrao
    try:
        with open(CAMINHO_CONFIG_CAMERA, "r", encoding="utf-8") as f:
            dados = json.load(f)
        padrao.update(dados)
        return padrao
    except Exception:
        return padrao


def guardar_config_camera(indice=None, largura=None, altura=None):
    config = carregar_config_camera()
    if indice is not None:
        config["indice"] = indice
    if largura is not None:
        config["largura"] = largura
    if altura is not None:
        config["altura"] = altura

    os.makedirs(os.path.dirname(CAMINHO_CONFIG_CAMERA), exist_ok=True)
    with open(CAMINHO_CONFIG_CAMERA, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return config


def obter_indice_camera():
    return carregar_config_camera()["indice"]


# ---------- Deteção de câmaras disponíveis ----------

def listar_cameras(max_indices=5):
    disponiveis = []
    for i in range(max_indices):
        try:
            cam = cv.VideoCapture(i, cv.CAP_DSHOW)
            if cam.isOpened():
                disponiveis.append(i)
            cam.release()
        except Exception:
            pass
    return disponiveis


def abrir_captura(indice_camera=None, largura=None, altura=None):
    config = carregar_config_camera()
    indice = indice_camera if indice_camera is not None else config["indice"]
    largura = largura if largura is not None else config["largura"]
    altura = altura if altura is not None else config["altura"]

    camera = cv.VideoCapture(indice, cv.CAP_DSHOW)
    if camera.isOpened():
        camera.set(cv.CAP_PROP_FRAME_WIDTH, largura)
        camera.set(cv.CAP_PROP_FRAME_HEIGHT, altura)
    return camera


# ---------- Deteção de rosto (guia visual) ----------

def detetar_rostos(frame):
    cinza = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    return _face_cascade.detectMultiScale(cinza, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))


def desenhar_moldura_rosto(frame, cor=(0, 200, 0)):
    rostos = detetar_rostos(frame)
    for (x, y, w, h) in rostos:
        cv.rectangle(frame, (x, y), (x + w, y + h), cor, 2)
    return frame, len(rostos) > 0


# ---------- Registo de aluno (foto para Face ID) ----------

def tirarFoto(usuario, indice_camera=None):
    os.makedirs(PASTA_FACES, exist_ok=True)
    camera = abrir_captura(indice_camera)

    if not camera.isOpened():
        print("Erro ao abrir camera")
        return None

    caminho_final = None
    while True:
        sucesso, frame = camera.read()
        if not sucesso:
            continue

        exibir, tem_rosto = desenhar_moldura_rosto(frame.copy())
        cv.putText(
            exibir,
            "Rosto detetado - Pressione P" if tem_rosto else "Centre o rosto na camara",
            (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7,
            (0, 200, 0) if tem_rosto else (0, 0, 255), 2,
        )
        cv.imshow("Registar rosto", exibir)

        tecla = cv.waitKey(1) & 0xFF
        if tecla == ord("p"):
            caminho = os.path.join(PASTA_FACES, f"{usuario}.jpg")
            cv.imwrite(caminho, frame)
            caminho_final = caminho
            break
        elif tecla == ord("q"):
            break

    camera.release()
    cv.destroyAllWindows()
    return caminho_final


# ---------- Face ID de presenças ----------

def registarPresenca(usuario, indice_camera=None):
    """Captura uma foto para validar/registar a presença de um aluno."""
    os.makedirs(PASTA_CAPTURAS, exist_ok=True)
    camera = abrir_captura(indice_camera)

    if not camera.isOpened():
        print("Erro ao abrir camera")
        return None

    caminho_final = None
    while True:
        sucesso, frame = camera.read()
        if not sucesso:
            continue

        exibir, tem_rosto = desenhar_moldura_rosto(frame.copy())
        cv.putText(
            exibir,
            "Pressione P para confirmar presenca" if tem_rosto else "A procurar rosto...",
            (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7,
            (0, 200, 0) if tem_rosto else (0, 0, 255), 2,
        )
        cv.imshow("Registo de Presença", exibir)

        tecla = cv.waitKey(1) & 0xFF
        if tecla == ord("p") and tem_rosto:
            nome = f"{usuario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            caminho = os.path.join(PASTA_CAPTURAS, nome)
            cv.imwrite(caminho, frame)
            caminho_final = caminho
            break
        elif tecla == ord("q"):
            break

    camera.release()
    cv.destroyAllWindows()
    return caminho_final


# ---------- Webcam / gravação genéricas ----------

def ligarCam(indice_camera=None, deteta_rosto=True):
    camera = abrir_captura(indice_camera)
    if not camera.isOpened():
        print("Erro ao abrir camera")
        return

    while True:
        sucesso, frame = camera.read()
        if sucesso:
            if deteta_rosto:
                frame, _ = desenhar_moldura_rosto(frame)
            cv.imshow("Webcam", frame)
        if cv.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv.destroyAllWindows()


def gravarVideo(indice_camera=None, pasta_destino=None):
    camera = abrir_captura(indice_camera)
    if not camera.isOpened():
        print("Erro ao abrir camera")
        return

    largura = int(camera.get(cv.CAP_PROP_FRAME_WIDTH))
    altura = int(camera.get(cv.CAP_PROP_FRAME_HEIGHT))

    pasta_destino = pasta_destino or PASTA_VIDEOS
    os.makedirs(pasta_destino, exist_ok=True)
    nome = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    caminho = os.path.join(pasta_destino, nome)

    out = cv.VideoWriter(caminho, cv.VideoWriter_fourcc(*"mp4v"), 20, (largura, altura))

    gravando = True
    while True:
        sucesso, frame = camera.read()
        if sucesso:
            if gravando:
                out.write(frame)
            exibir = frame.copy()
            cv.putText(
                exibir, "REC" if gravando else "PAUSA",
                (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.8,
                (0, 0, 255) if gravando else (0, 200, 0), 2,
            )
            cv.imshow("Gravar", exibir)

        tecla = cv.waitKey(1) & 0xFF
        if tecla == ord("s"):
            gravando = False
        elif tecla == ord("r"):
            gravando = True
        elif tecla == 27:
            break

    camera.release()
    out.release()
    cv.destroyAllWindows()
    return caminho