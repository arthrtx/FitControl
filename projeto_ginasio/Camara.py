import cv2 as cv
import os

from projeto_ginasio.config import (
    PASTA_CAPTURAS,
    PASTA_FACES,
    PASTA_VIDEOS
)


def tirarFoto(usuario):

    os.makedirs(
        PASTA_FACES,
        exist_ok=True
    )

    camera = cv.VideoCapture(0)

    if not camera.isOpened():
        print("Erro ao abrir camera")
        return None


    while True:

        sucesso, frame = camera.read()

        if not sucesso:
            continue


        cv.imshow(
            "Registar rosto",
            frame
        )


        tecla = cv.waitKey(1) & 0xff


        if tecla == ord("p"):

            caminho = os.path.join(
                PASTA_FACES,
                f"{usuario}.jpg"
            )


            cv.imwrite(
                caminho,
                frame
            )


            camera.release()
            cv.destroyAllWindows()

            return caminho



        elif tecla == ord("q"):

            break



    camera.release()
    cv.destroyAllWindows()

    return None



def ligarCam():

    camera = cv.VideoCapture(0)


    if not camera.isOpened():

        print("Erro ao abrir camera")
        return



    while True:

        sucesso, frame = camera.read()

        if sucesso:

            cv.imshow(
                "Webcam",
                frame
            )


        if cv.waitKey(1) & 0xff == ord("q"):

            break



    camera.release()
    cv.destroyAllWindows()



def gravarVideo():

    camera = cv.VideoCapture(0)


    largura = int(
        camera.get(cv.CAP_PROP_FRAME_WIDTH)
    )

    altura = int(
        camera.get(cv.CAP_PROP_FRAME_HEIGHT)
    )


    caminho = os.path.join(
        PASTA_VIDEOS,
        "video.mp4"
    )


    out = cv.VideoWriter(
        caminho,
        cv.VideoWriter_fourcc(*"mp4v"),
        20,
        (largura, altura)
    )


    while True:

        sucesso, frame = camera.read()

        if sucesso:

            out.write(frame)

            cv.imshow(
                "Gravar",
                frame
            )


        if cv.waitKey(1) == 27:
            break


    camera.release()
    out.release()
    cv.destroyAllWindows()