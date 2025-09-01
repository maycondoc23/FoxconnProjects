import cv2
import numpy as np

def contar_pads_solda_por_pixel_preto_connected(imagem_path, area_minima):
    """
    Conta pads de solda pelas áreas pretas (sem inverter com findContours),
    usando rotulagem com connectedComponents.
    """
    imagem = cv2.imread(imagem_path)
    if imagem is None:
        print("Erro ao carregar a imagem.")
        return 0

    # Converter para escala de cinza
    rec_gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

    # Threshold com Otsu (pads pretos = 0, fundo branco = 255)
    _, rec_bin = cv2.threshold(rec_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Inverter para que pads (0) virem 255 → necessário para connectedComponents
    rec_bin_invertida = cv2.bitwise_not(rec_bin)

    # Rotula regiões conectadas
    num_labels, labels = cv2.connectedComponents(rec_bin_invertida)

    # Conta quantos componentes têm área maior que a mínima
    qtd_pads = 0
    for label in range(1, num_labels):  # pula o rótulo 0 (fundo)
        area = np.sum(labels == label)
        if area >= area_minima:
            qtd_pads += 1

    # Visualização (opcional)
    imagem_colorida = cv2.cvtColor(rec_bin_invertida, cv2.COLOR_GRAY2BGR)
    cv2.imshow("Imagem Invertida (para análise)", imagem_colorida)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return qtd_pads


def contarpads(imagem, area_minima, pads, nome, borda, modo):
    img = cv2.imread(imagem)

    imagem = img
    if imagem is None:
        print("Erro ao carregar a imagem.")
        return 0

    h, w = imagem.shape[:2]
    x_start = int(w * borda)
    y_start = int(h * borda)
    x_end = int(w * (1 - borda))
    y_end = int(h * (1 - borda))

    imagem_cortada = imagem[y_start:y_end, x_start:x_end]

    # Converter para escala de cinza antes do threshold
    imagem_cortada_gray = cv2.cvtColor(imagem_cortada, cv2.COLOR_BGR2GRAY)
    _, rec_bin = cv2.threshold(imagem_cortada_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    rec_bin_invertida = cv2.bitwise_not(rec_bin)

    # Aplica operação morfológica para separar pads colados
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    rec_bin_processado = None
    # print(modo)
    if modo == 1:
        rec_bin_processado = cv2.morphologyEx(rec_bin_invertida, cv2.MORPH_OPEN, kernel, iterations=1)
    elif int(modo) == 2:
        # print("Modo 2")
        rec_bin_processado = cv2.morphologyEx(rec_bin, cv2.MORPH_OPEN, kernel, iterations=1)

    # Encontrar contornos nas regiões pretas (brancas na imagem invertida processada)
    contornos, _ = cv2.findContours(rec_bin_processado, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pads_detectados = []
    for cnt in contornos:
        area = cv2.contourArea(cnt)
        if area >= area_minima:
            pads_detectados.append(cnt)

    # Para visualização, desenha os contornos na imagem cortada (opcional)
    img_resultado = imagem_cortada.copy()

    cv2.drawContours(img_resultado, pads_detectados, -1, (0, 0, 255), 1)
    if rec_bin_invertida is not None and isinstance(rec_bin_invertida, np.ndarray):
        cv2.imshow("Imagem Invertida (para análise)", rec_bin_invertida)
        cv2.waitKey(0)

    if len(pads_detectados) == pads:
        return None
    else:
        print(nome, len(pads_detectados), "pads detectados, esperado:", pads, "area:", area_minima)
        return rec_bin_processado

imagem_path = fr"bosa.bmp"
# qtd_pads = contar_pads_solda_por_pixel_preto_connected(imagem_path, area_minima=300)

comparacao = contarpads("bosa.bmp", 250, 4, 'bosa', 0.04, modo=1)

# print(f"Quantidade de pads de solda (por pixel preto, via connectedComponents): {qtd_pads}")
