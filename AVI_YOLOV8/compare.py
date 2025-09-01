import cv2
import os 
import numpy as np
from datetime import datetime

def detectar_curto_aprimorado(img_path_boa, img_path_ruim, borda, area_min):
    img_boa = cv2.imread(img_path_boa)
    img_ruim = cv2.imread(img_path_ruim)

    if img_boa is None or img_ruim is None:
        print("Erro ao carregar imagens.")
        return

    # Redimensiona para o mesmo tamanho
    if img_boa.shape != img_ruim.shape:
        img_ruim = cv2.resize(img_ruim, (img_boa.shape[1], img_boa.shape[0]))

    h, w = img_boa.shape[:2]
    x_start = int(w * borda)
    y_start = int(h * borda)
    x_end = int(w * (1 - borda))
    y_end = int(h * (1 - borda))

    canal_boa = img_boa[y_start:y_end, x_start:x_end, 1]
    canal_ruim = img_ruim[y_start:y_end, x_start:x_end, 1]

    # Suavização leve (mantendo curtos visíveis)
    canal_boa = cv2.GaussianBlur(canal_boa, (3, 3), 0)
    canal_ruim = cv2.GaussianBlur(canal_ruim, (3, 3), 0)

    diff = cv2.absdiff(canal_boa, canal_ruim)

    media = np.mean(diff)
    _, diff_thresh = cv2.threshold(diff, media + 10, 255, cv2.THRESH_BINARY)

    # Estrutura refinada (evita perder curtos pequenos)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    diff_thresh = cv2.morphologyEx(diff_thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    diff_thresh = cv2.dilate(diff_thresh, kernel, iterations=1)

    contornos, _ = cv2.findContours(diff_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    img_resultado = img_ruim.copy()
    curtos_encontrados = 0

    for cnt in contornos:
        area = cv2.contourArea(cnt)
        if area >= area_min:
            x, y, w_box, h_box = cv2.boundingRect(cnt)
            aspect_ratio = w_box / float(h_box) if h_box != 0 else 0
            hull = cv2.convexHull(cnt)
            solidity = area / cv2.contourArea(hull) if cv2.contourArea(hull) > 0 else 0

            if 0.2 < aspect_ratio < 5.0 and solidity > 0.3:
                cnt += np.array([[[x_start, y_start]]])
                cv2.drawContours(img_resultado, [cnt], -1, (0, 0, 255), 2)
                curtos_encontrados += 1

    print(f"Curto(s) detectado(s): {curtos_encontrados}")

    empilhada = np.hstack([img_boa, img_resultado])
    empilhada_zoom = cv2.resize(empilhada, None, fx=3, fy=3, interpolation=cv2.INTER_LINEAR)

    cv2.imshow("Boa | Curto Detectado", empilhada_zoom)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# Exemplo de uso
# detectar_curto_aprimorado(img_path_boa=r"debug\padrao.jpg",img_path_ruim=r"debug\ruim.jpg",borda=0.1,area_min=100)
detectar_curto_aprimorado(img_path_boa=r"C:\Users\mayconcosta\yolo-V8\testeyolo\componentes\BOSA_4P_BOT1\BOSA_4P_BOT1_1.bmp",img_path_ruim=r"curto.bmp",borda=0.1,area_min=350)


# data_atual = datetime.now().strftime("%d%m%Y")
# dataehora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
# pasta = os.path.join("log_passed", data_atual)


# serialnumber = "123456789"  # Exemplo de serial number, substitua conforme necessário
# if not os.path.exists(pasta):
#     os.makedirs(pasta, exist_ok=True)

# with open(os.path.join(pasta, f"{serialnumber.strip()}.txt"), 'w') as f:
#     f.write(f"Serial: {serialnumber.strip()}\nData/Hora: {dataehora}\n")