import cv2 as cv
import os

def ligarCam():
    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        print("Erro ao abrir a câmara.")
        return

    noir = False

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Erro ao capturar imagem.")
            break

        if noir:
            color = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        else:
            color = frame

        cv.imshow("Webcam", color)

        key = cv.waitKey(1) & 0xFF

        if key == ord('b'):
            noir = True

        elif key == ord('c'):
            noir = False

        elif key == ord('p'):
            cv.imwrite("waka.jpg", frame)
            print("Foto guardada!")

        elif key == ord('q'):
            break

    cap.release()
    cv.destroyAllWindows()


def tirarFoto(usuario):
    print("tirarFoto chamada")
    pasta = r"C:\Temp\MinhaPasta\faces"
    os.makedirs(pasta, exist_ok=True)

    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        print("Erro ao abrir a câmara.")
        return None

    print("====================================")
    print("Prima P para tirar a fotografia.")
    print("Prima Q para cancelar.")
    print("====================================")

    while True:
        ret, frame = cap.read()

        if not ret:
            continue

        cv.imshow("Webcam", frame)

        key = cv.waitKey(1) & 0xFF

        if key == ord('p') or key == ord('P'):
            caminho = os.path.join(pasta, f"{usuario}.jpg")

            if cv.imwrite(caminho, frame):
                print("Foto guardada com sucesso!")
                cap.release()
                cv.destroyAllWindows()
                return caminho
            else:
                print("Erro ao guardar a fotografia.")
                cap.release()
                cv.destroyAllWindows()
                return None

        elif key == ord('q') or key == ord('Q'):
            print("Operação cancelada.")
            cap.release()
            cv.destroyAllWindows()
            return None


def gravarVideo():
    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        print("Erro ao abrir a câmara.")
        return

    frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv.VideoWriter_fourcc(*'mp4v')

    gravar = False
    out = None

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Erro ao capturar imagem.")
            break

        cv.imshow("Camera", frame)

        key = cv.waitKey(1) & 0xFF

        if key == ord('r') and not gravar:
            out = cv.VideoWriter(
                "output.mp4",
                fourcc,
                20.0,
                (frame_width, frame_height)
            )
            gravar = True
            print("A gravar...")

        elif key == ord('s') and gravar:
            gravar = False
            out.release()
            print("Gravação terminada.")

        elif key == 27:
            break

        if gravar:
            out.write(frame)

    cap.release()

    if out is not None:
        out.release()

    cv.destroyAllWindows()

