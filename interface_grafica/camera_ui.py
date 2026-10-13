"""Leitura da câmara num thread e visor dentro da própria janela.

Antes o Face ID e o registo de fotos abriam janelas do OpenCV à parte
(e com o cv2.imshow chamado fora do thread principal). Agora a imagem
aparece dentro da aplicação."""

import threading
import time
import tkinter as tk

import cv2
from PIL import Image, ImageDraw, ImageFont, ImageTk

from interface_grafica.arte import fluido
from interface_grafica.constants import TEMA
from projeto_ginasio import Camara


def _rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


_fontes = {}


def _fonte(tamanho):
    # carregar o TTF é demorado: guarda-se por tamanho (chamava-se a cada frame)
    fonte = _fontes.get(tamanho)
    if fonte is None:
        for nome in ("segoeuib.ttf", "seguisb.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
            try:
                fonte = ImageFont.truetype(nome, tamanho)
                break
            except OSError:
                continue
        if fonte is None:
            fonte = ImageFont.load_default()
        _fontes[tamanho] = fonte
    return fonte


_leitores = []


def libertar_camera(exceto=None):
    """Só um componente pode usar a câmara de cada vez: pára o Face ID e
    as outras pré-visualizações antes de a abrir de novo."""
    for leitor in list(_leitores):
        if leitor is not exceto:
            leitor.parar()

    from interface_grafica import face_id
    reconhecimento = face_id.modulo()
    if reconhecimento is None:
        return

    if reconhecimento.reconhecimento_ativo() or reconhecimento._reconhecimento_em_execucao:
        reconhecimento.parar_reconhecimento()
        limite = time.time() + 3
        while reconhecimento._reconhecimento_em_execucao and time.time() < limite:
            time.sleep(0.05)


class LeitorCamera:
    """Lê frames sem bloquear a interface. Com detetar=True marca os
    rostos (detetor rápido do OpenCV, só para guiar o enquadramento)."""

    def __init__(self, indice=None, detetar=True):
        self.indice = indice
        self.detetar = detetar
        self.erro = None
        self.a_correr = False
        self._parar = threading.Event()
        self._lock = threading.Lock()
        self._frame = None
        self._rostos = []
        self._n = 0
        self._thread = None

    def iniciar(self):
        if self.a_correr:
            return
        libertar_camera(exceto=self)
        if self not in _leitores:
            _leitores.append(self)
        self._parar.clear()
        self.erro = None
        self.a_correr = True
        self._thread = threading.Thread(target=self._ciclo, daemon=True)
        self._thread.start()

    def parar(self):
        self._parar.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.a_correr = False
        if self in _leitores:
            _leitores.remove(self)

    def obter(self):
        with self._lock:
            return self._n, self._frame, list(self._rostos)

    def _ciclo(self):
        camera = Camara.abrir_captura(self.indice)
        if not camera.isOpened():
            self.erro = "Não foi possível abrir a câmara."
            self.a_correr = False
            return

        rostos = []
        ultima_deteccao = 0.0
        try:
            while not self._parar.is_set():
                sucesso, frame = camera.read()
                if not sucesso:
                    time.sleep(0.03)
                    continue
                # a deteção é o passo caro: no máximo 4 por segundo (antes
                # corria a cada 5 frames, ou seja, 6 por segundo, à resolução total)
                agora = time.time()
                if self.detetar and agora - ultima_deteccao >= 0.25:
                    ultima_deteccao = agora
                    rostos = [
                        {"caixa": [int(x), int(y), int(x + w), int(y + h)], "nome": "", "conhecido": True}
                        for (x, y, w, h) in Camara.detetar_rostos(frame)
                    ]
                with self._lock:
                    self._frame = frame
                    self._rostos = rostos
                    self._n += 1
        finally:
            camera.release()
            with self._lock:
                self._frame = None
                self._n += 1
            self.a_correr = False


class VisorCamera(tk.Canvas):
    """Mostra os frames de uma 'fonte' (função que devolve (n, frame, rostos))."""

    def __init__(self, master, fonte=None, espelho=True, texto_vazio="Câmara desligada"):
        super().__init__(master, highlightthickness=0, bd=0, bg=TEMA["surface_alt"])
        self.fonte = fonte
        self.espelho = espelho
        self.texto_vazio = texto_vazio
        self._ultimo = -1
        self._foto = None
        self._job = None
        self._vazio = True
        self._foto_video = None
        self._tamanho_video = None
        self.ultimo_frame = None
        self._vazio_job = None
        self.bind("<Configure>", self._agendar_vazio)
        self.after(50, self._desenhar_vazio)

    def _agendar_vazio(self, _evento=None):
        if not self._vazio:
            return
        if self._vazio_job:
            self.after_cancel(self._vazio_job)
        self._vazio_job = self.after(70, self._desenhar_vazio)

    def ligar(self, fonte):
        self.fonte = fonte
        self._ultimo = -1
        if not self._job:
            self._atualizar()

    def desligar(self, texto=None):
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        if texto:
            self.texto_vazio = texto
        self.fonte = None
        self.ultimo_frame = None
        self._desenhar_vazio()

    def congelar(self):
        """Pára de atualizar mas mantém a última imagem."""
        if self._job:
            self.after_cancel(self._job)
            self._job = None

    def _atualizar(self):
        self._job = None
        if not self.winfo_exists() or self.fonte is None:
            return
        n, frame, rostos = self.fonte()
        if n != self._ultimo:
            self._ultimo = n
            if frame is None:
                if not self._vazio:
                    self._desenhar_vazio()
            else:
                self.ultimo_frame = frame
                self._mostrar(frame, rostos)
        self._job = self.after(33, self._atualizar)

    def _mostrar(self, frame, rostos):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20 or h < 20:
            return
        self._vazio = False
        fh, fw = frame.shape[:2]
        # preencher o visor sem deformar (corta o que sobra); o OpenCV
        # redimensiona bem mais depressa do que o PIL
        escala = max(w / fw, h / fh)
        nw, nh = max(int(fw * escala), w), max(int(fh * escala), h)
        dx, dy = (nw - w) // 2, (nh - h) // 2
        reduzido = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)[dy:dy + h, dx:dx + w]
        if self.espelho:
            reduzido = cv2.flip(reduzido, 1)
        img = Image.fromarray(cv2.cvtColor(reduzido, cv2.COLOR_BGR2RGB))

        if rostos:
            d = ImageDraw.Draw(img)
            for rosto in rostos:
                x1, y1, x2, y2 = [v * escala for v in rosto["caixa"]]
                x1, x2 = x1 - dx, x2 - dx
                y1, y2 = y1 - dy, y2 - dy
                if self.espelho:
                    x1, x2 = w - x2, w - x1
                cor = _rgb(TEMA["accent"]) if rosto.get("conhecido", True) else _rgb(TEMA["amber"])
                self._cantos(d, x1, y1, x2, y2, cor)
                if rosto.get("nome"):
                    fonte = _fonte(14)
                    texto = rosto["nome"]
                    tw = d.textlength(texto, font=fonte)
                    d.rounded_rectangle((x1, y1 - 30, x1 + tw + 20, y1 - 6), radius=10, fill=cor)
                    d.text((x1 + 10, y1 - 27), texto, font=fonte, fill=(10, 10, 12))

        # reaproveita a mesma imagem (criar uma PhotoImage nova a cada frame pesa)
        if self._foto_video is not None and self._tamanho_video == (w, h):
            self._foto_video.paste(img)
        else:
            self._foto_video = ImageTk.PhotoImage(img)
            self._tamanho_video = (w, h)
            self.delete("all")
            self.create_image(0, 0, image=self._foto_video, anchor="nw", tags="video")

    def _cantos(self, d, x1, y1, x2, y2, cor):
        t = max(14, (x2 - x1) * 0.22)
        for (ax, ay, sx, sy) in ((x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1), (x2, y2, -1, -1)):
            d.line([(ax, ay + sy * t), (ax, ay), (ax + sx * t, ay)], fill=cor, width=4, joint="curve")

    def _desenhar_vazio(self):
        self._vazio = True
        self._foto_video = None
        self._tamanho_video = None
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20 or h < 20:
            return
        arte = fluido(w, h, [TEMA["violet"], TEMA["accent"], TEMA["magenta"]], TEMA["surface_alt"],
                      semente=3, grao=True)
        fundo = Image.blend(Image.new("RGBA", (w, h), _rgb(TEMA["surface_alt"]) + (255,)), arte, 0.35)
        self._foto = ImageTk.PhotoImage(fundo)
        self.delete("all")
        self.create_image(0, 0, image=self._foto, anchor="nw")
        self.create_text(w / 2, h / 2, text=self.texto_vazio, fill=TEMA["text"],
                         font=("Segoe UI", 12, "bold"), width=w - 40, justify="center")
