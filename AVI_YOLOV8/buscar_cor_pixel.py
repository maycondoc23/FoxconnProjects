import cv2
import numpy as np
import json
import os

SETUP_PATH = "setup_componentes.json"
CHAVE_SETUP = "BOSA_BOT1"
DISTANCIA_MINIMA = 10  # px

def carregar_setup():
    if os.path.exists(SETUP_PATH):
        with open(SETUP_PATH, "r") as f:
            return json.load(f)
    return {}

def salvar_setup(data):
    # Salva JSON com listas inline (sem quebras)
    class CompactJSONEncoder(json.JSONEncoder):
        pass  # Use default implementation

    with open(SETUP_PATH, "w") as f:
        json.dump(data, f, indent=4, cls=CompactJSONEncoder)
        
def mostrar_cor_pixel(self, imagem_path):
    imagem_original = cv2.imread(imagem_path)
    if imagem_original is None:
        print("Erro ao carregar a imagem.")
        return

    setup_data = carregar_setup()
    if CHAVE_SETUP not in setup_data:
        setup_data[CHAVE_SETUP] = {}

    # Garante que pixel_compare exista
    setup_data[CHAVE_SETUP]["pixel_compare"] = []

    escala = [1.0, 1.0]  # (escala_x, escala_y)

    def redimensionar_imagem():
        nonlocal escala
        h_win, w_win = cv2.getWindowImageRect("Imagem")[3], cv2.getWindowImageRect("Imagem")[2]
        h_img, w_img = imagem_original.shape[:2]
        escala_x = w_win / w_img
        escala_y = h_win / h_img
        escala = [escala_x, escala_y]
        nova_img = cv2.resize(imagem_original, (w_win, h_win), interpolation=cv2.INTER_LINEAR)
        return nova_img

    def desenhar_pontos(imagem_redimensionada):
        img_com_pontos = imagem_redimensionada.copy()
        for ponto in setup_data[CHAVE_SETUP]["pixel_compare"]:
            x, y = ponto["coord"]
            x_resized = int(x * escala[0])
            y_resized = int(y * escala[1])
            cv2.circle(img_com_pontos, (x_resized, y_resized), radius=4, color=(0, 0, 255), thickness=-1)
        return img_com_pontos

    def on_mouse_click(event, x, y, flags, param):
        nonlocal imagem_exibida

        # Converte ponto da imagem exibida para coordenada original
        x_img = int(x / escala[0])
        y_img = int(y / escala[1])

        if event == cv2.EVENT_LBUTTONDOWN:
            if len(setup_data[CHAVE_SETUP]["pixel_compare"]) == 0:
                if 0 <= y_img < imagem_original.shape[0] and 0 <= x_img < imagem_original.shape[1]:
                    b, g, r = imagem_original[y_img, x_img]
                    rgb = [int(r), int(g), int(b)]

                    print(f"Coordenadas: ({x_img}, {y_img}) - RGB: {rgb}")

                    setup_data[CHAVE_SETUP]["pixel_compare"] = [{"coord": [x_img, y_img], "rgb": rgb}]
                    salvar_setup(setup_data)

                    imagem_redimensionada = redimensionar_imagem()
                    imagem_exibida = desenhar_pontos(imagem_redimensionada)
                    cv2.imshow("Imagem", imagem_exibida)

        elif event == cv2.EVENT_RBUTTONDOWN:
            ponto_remover = None
            min_dist = float('inf')
            for ponto in setup_data[CHAVE_SETUP]["pixel_compare"]:
                px, py = ponto["coord"]
                dist = np.hypot(px - x_img, py - y_img)
                if dist < min_dist and dist < DISTANCIA_MINIMA:
                    min_dist = dist
                    ponto_remover = ponto

            if ponto_remover:
                setup_data[CHAVE_SETUP]["pixel_compare"].remove(ponto_remover)
                salvar_setup(setup_data)
                imagem_redimensionada = redimensionar_imagem()
                imagem_exibida = desenhar_pontos(imagem_redimensionada)
                cv2.imshow("Imagem", imagem_exibida)

    # Cria janela redimensionável
    cv2.namedWindow("Imagem", cv2.WINDOW_NORMAL)
    imagem_redimensionada = redimensionar_imagem()
    imagem_exibida = desenhar_pontos(imagem_redimensionada)
    cv2.imshow("Imagem", imagem_exibida)
    cv2.setMouseCallback("Imagem", on_mouse_click)

    while True:
        key = cv2.waitKey(100)
        if key == 27:  # ESC
            break
        nova_imagem = redimensionar_imagem()
        imagem_exibida = desenhar_pontos(nova_imagem)
        cv2.imshow("Imagem", imagem_exibida)

    cv2.destroyAllWindows()


def verificar_pixels_na_imagem(self, imagem_path, tolerancia=10):
    imagem = cv2.imread(imagem_path)
    if imagem is None:
        print("Erro ao carregar a imagem.")
        return False

    setup_data = carregar_setup()
    if CHAVE_SETUP not in setup_data or "pixel_compare" not in setup_data[CHAVE_SETUP]:
        print(f"Nenhum dado de comparação encontrado em '{CHAVE_SETUP}'.")
        return False

    pixels = setup_data[CHAVE_SETUP]["pixel_compare"]

    for idx, pixel in enumerate(pixels):
        x, y = pixel["coord"]
        rgb_esperado = pixel["rgb"]

        if y >= imagem.shape[0] or x >= imagem.shape[1]:
            print(f"Pixel {idx} fora dos limites da imagem: {pixel}")
            continue

        b, g, r = imagem[y, x]
        rgb_atual = [r, g, b]

        diferenca = np.abs(np.array(rgb_esperado) - np.array(rgb_atual))
        if all(diferenca <= tolerancia):
            print(f"[OK] Pixel {idx} em {x},{y} | RGB esperado: {rgb_esperado} | Encontrado: {rgb_atual}")
            return True
        else:
            print(f"Pixel configurado nao encontrado para {CHAVE_SETUP}")
            return False

# Caminho da imagem
# imagem_path = r"C:\Users\mayconcosta\Downloads\asus2.bmp"

# mostrar_cor_pixel(None, imagem_path)

# passed = verificar_pixels_na_imagem(None, imagem_path, tolerancia=20)
