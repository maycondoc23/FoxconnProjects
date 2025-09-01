import cv2,os

os.environ["ULTRALYTICS_HUB"] = "False"
os.environ["ULTRALYTICS_API_KEY"] = "none"
os.environ["ULTRALYTICS_OFFLINE"] = "True"
import gxipy as gx
import numpy as np
import threading, asyncio
from flask import Flask
import websockets
import queue
from collections import defaultdict
from ultralytics import YOLO
from datetime import datetime
import math, os, time
from componentes import carregar_componentes, calibrar


imagem_entrada = ""
imagem_saida = ""
imagem_atual = None
frame_queue = queue.Queue(maxsize=1)  # fila thread-safe
rpassfolder_img = defaultdict(lambda: None)
imagens_componentes = defaultdict(lambda: None)
crop_componentes = defaultdict(lambda: None)
print("Carregando modelo YOLO...")
model = YOLO(r'best_ktc.pt')
print("Modelo YOLO carregado com sucesso.")
anotacoes_IA = defaultdict(lambda: None)
anotacoes_notpass = defaultdict(lambda: None)
anotacoes_IA_notfound = defaultdict(lambda: None)
lista_passed = []
lista_test = []
lista_botao20 = []
label_imagem_botao20 = []
lista = []
hora_teste = None
serial = ""
serialnumber = ""   
processando_frame = False
componentes_esperados = carregar_componentes()
testing = False
app = Flask(__name__)
frame_atual = None
set_status = "PASS"
set_fail = 0
item_botao20_selecionado = None


def centro_box(box):
    x1, y1, x2, y2 = map(float, box)
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def distancia(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def threading_frame():
    global processando_frame, frame_atual
    device_manager = gx.DeviceManager()
    device_manager.update_device_list()
    if device_manager.get_device_number() == 0:
        raise RuntimeError("Nenhuma câmera Daheng conectada.")

    cam = device_manager.open_device_by_index(1)
    cam.stream_on()

    while True:
        try:


            raw_image = cam.data_stream[0].get_image(timeout=1000)
            if raw_image is None:
                continue

            iaok = anotacoes_IA.copy()

            rgb_image = raw_image.convert("RGB")
            frame_atual = rgb_image
            rgb_np = rgb_image.get_numpy_array()


            # Desenha as anotações de componentes detectados (iaok) em verde
            for k, v in iaok.items():
                x1, y1, x2, y2 = v["x1"], v["y1"], v["x2"], v["y2"]
                conf = v.get("conf", 0)
                label = v.get("label", "")[:5]
                cv2.rectangle(rgb_np, (x1, y1), (x2, y2), (0, 255, 0), 12)
                texto = f"{label} {conf}%"
                cv2.putText(rgb_np, texto, (x1, max(y1 - 10, 0)),
                            cv2.FONT_HERSHEY_SIMPLEX, 2.4, (0, 255, 0), 8)

            # Agora converte para bytes JPEG **após desenhar**
            # Converte de RGB para BGR antes de redimensionar para garantir cores corretas no OpenCV
            bgr_img = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2BGR)
            small_img = cv2.resize(bgr_img, (5496, 3672), interpolation=cv2.INTER_AREA)
            _, buffer = cv2.imencode('.jpg', small_img)
            frame_bytes = buffer.tobytes()

            # _, buffer = cv2.imencode('.jpg', rgb_np)
            # frame_bytes = buffer.tobytes()

            # Atualiza fila thread-safe
            if frame_queue.full():
                try:
                    frame_queue.get_nowait()
                except:
                    pass
            frame_queue.put_nowait(frame_bytes)

        except Exception as e:
            print("Erro na câmera:", e)


async def stream(websocket):
    while True:
        try:
            frame_bytes = await asyncio.to_thread(frame_queue.get)
            await websocket.send(frame_bytes)
            await asyncio.sleep(0.01)
        except websockets.exceptions.ConnectionClosedOK:
            print("Cliente desconectou de forma limpa.")
            break
        except Exception as e:
            print("Erro no WebSocket:", e)
            break


@app.route('/')
def index():
    return """<html>
        <body>
            <h1>Stream IA</h1>
            <img id="frame" >
            <script>
                let ws = new WebSocket("ws://localhost:8765");
                ws.binaryType = "arraybuffer";
                ws.onmessage = (event) => {
                    let blob = new Blob([event.data], {type:"image/jpeg"});
                    let url = URL.createObjectURL(blob);
                    document.getElementById("frame").src = url;
                };
            </script>
        </body>
    </html>"""


async def start_websocket():
    async with websockets.serve(stream, "0.0.0.0", 8765):
        print("WebSocket rodando em ws://localhost:8765")
        await asyncio.Future()  # mantém rodando

def desenhar_resultado_ia_em_tempo_real(img):
    while True:
        
        global serial, componentes_esperados, serialnumber, hora_teste, anotacoes_IA, anotacoes_notpass, anotacoes_IA_notfound
        global lista_passed, lista_test, lista_botao20, label_imagem_botao20, lista, hora_teste, imagens_componentes, crop_componentes
        global rpassfolder_img, aplicar_sharpness, testing, escrever_log, set_fail, processando_frame, model, set_status, item_botao20_selecionado
        frame = None
        if frame_atual is None:
            continue
        else:
            print("Processando frame atual...")
            frame = frame_atual.get_numpy_array()

        janelas_detectadas_atuais = set()
        if hora_teste is None:
            hora_teste = datetime.now().strftime("%H%M%S")


        detectou = False

        imagem_sem_anotacoes = frame

        
        contagem_classes = defaultdict(int)
        # print("Detectando objetos com IA...")
        cv2.imwrite("2imagem_entrada.png", img)
        results = model.predict(frame, conf=0.30, verbose=True, device="cuda")[0]
        time.sleep(0.05)
        processando_frame = False

        # print("Objetos detectados:", results.boxes.cls)
        boxes = results.boxes.xyxy
        centros_detectados = [centro_box(box) for box in boxes]
        processando_frame = False

        detectados_nome = []
        
        anotacoes_IA.clear()
        anotacoes_notpass.clear()
        # Desenhar objetos detectados pela IA
        for box, cls, conf in zip(results.boxes.xyxy, results.boxes.cls, results.boxes.conf):
            detectou = True
            x1, y1, x2, y2 = map(int, box)
            class_id = int(cls)
            label = model.names[class_id]
            # print(label)
            conf_pct = int(conf * 100)

            contagem_classes[label] += 1

            # Identificação do nome do componente detectado (ex: BOSA_BOT1, BOSA_4P_BOT1)
            for nome, info in componentes_esperados.items():
                if "DATAMATRIX" == info["classe"]:
                    detectados_nome.append(nome)
                    continue

                if info["classe"] == label:
                    pos = info["posicoes"][0]
                    cx, cy = centro_box(box)

                    # Aumenta o box da IA em 20% para verificação
                    box_w = box[2] - box[0]
                    box_h = box[3] - box[1]
                    aumento = 0.5  # 20% maior
                    box_w_maior = box_w * (1 + aumento)
                    box_h_maior = box_h * (1 + aumento)
                    raio_reduzido = min(box_w_maior, box_h_maior) * 0.8

                    if distancia(pos, (cx, cy)) < raio_reduzido:
                        detectados_nome.append(nome)



            if label.upper() == "DATAMATRIX":
                aplicar_sharpness = True

                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                texto = f"{label} {conf_pct}%"
                cv2.putText(img, texto, (x1, y1-20),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 6)

                cv2.imwrite("serial.png", img[y1:y2, x1:x2])
                recorte = imagem_sem_anotacoes[y1:y2, x1:x2]

                if label in ["Awaiting...", "", " ", "Serial:", "SN:", "Aguardando novo Serial..."] or label.strip() == "= PASS":


                    print("Lendo novo SerialNumber...")
                    testing = False
                    # serial = ler_serial(recorte)

                    # print(f"Serial lido: {serial}")
                    # labelserial.setText(f"SN:{serial}")
                    labelnova = f"SN:{serial}"
                    if not labelnova in ["Awaiting...", "", " ", "Serial:", "SN:", "Aguardando novo Serial..."]:
                        if serialnumber != serial:
                            serialnumber = serial

                            hora_teste = datetime.now().strftime("%H%M%S")
                            crop_componentes.clear()
                            imagens_componentes.clear()
                            rpassfolder_img.clear()
        
                            item_botao20_selecionado = None

                            set_fail = 0
                            set_status = "PASS"

                            aplicar_sharpness = True
                            testing = True
                            escrever_log = True

                            # class StatusThread3(QThread):
                            #     update_status3 = pyqtSignal(str, str, int)

                            #     def run(self):
                            #         update_status3.emit('DATAMATRIX1', "PASS", 100)
                                    
                            # status_thread = StatusThread3()
                            # status_thread.update_status3.connect(status_componente_botao)
                            # status_thread.start()
                            # status_thread.wait()
                            # status_thread.finished.connect(status_thread.deleteLater)

                            time.sleep(0.1)
                            
                        
                else:
                    pass
                    # print(f"Serial ja lido")
            else:
                # inputar dados no dicionario anotacoes_IA para cada componente detectado para depois fazer todas anotacoes de uma vez
                # Conta quantos já existem com esse label para criar label1, label2, etc.
                count = sum(1 for k in anotacoes_IA if k.startswith(label))
                label_nomeado = f"{label}{count + 1}"
                anotacoes_IA[label_nomeado] = {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "conf": conf_pct,
                    "label": label_nomeado
                }
                
                # cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 8)
                # texto = f"{label} {conf_pct}%"
                # cv2.putText(img, texto, (x1, y1-20),
                # cv2.FONT_HERSHEY_SIMPLEX, 2.1, (0, 255, 0), 8)


        y_offset = 60
        faltando = []
        classe_exibiba = []
        anotacoes_IA_notfound.clear()

        if testing != None:
            testing = True
        
        if not detectou:

            print("Nenhum objeto detectado")
            print("Nenhum objeto detectado")
            print("Nenhum objeto detectado")
            aplicar_sharpness = False
            testing = False
            escrever_log = True
            

            cv2.putText(img, "Nenhum objeto detectado", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)


            lista_passed.clear()
            crop_componentes.clear()
            imagens_componentes.clear()
            lista_botao20.clear()
            label_imagem_botao20.clear()
            set_fail = 0
            rpassfolder_img.clear()
            set_status = "PASS"
            
            # janelas_a_fechar = janelas_crops_abertas - janelas_detectadas_atuais
            # for janela in janelas_a_fechar:
            #     try:
            #         cv2.destroyWindow(janela)
            #     except cv2.error as e:
            #         print(f"Erro ao fechar janela {janela}: {e}")
            #     janelas_crops_abertas.discard(janela)

        if testing  and set_status != "FAIL":
            aplicar_sharpness = True


            for nome, info in componentes_esperados.items():
                classe = info["classe"]
                posicoes = info["posicoes"]
                largura, altura = info.get("tamanho", [150, 120])
                achou = any(distancia(posicoes[0], d) < 30 for d in centros_detectados)

                if not achou:
                    if info["classe"] == "DATAMATRIX":
                        continue
                    x, y = posicoes[0]
                    falt_x1 = int(x - largura // 2)
                    falt_y1 = int(y - altura // 2)
                    falt_x2 = int(x + largura // 2)
                    falt_y2 = int(y + altura // 2)
                    
                    faltando.append(nome)

                    # Adiciona ao dicionário de anotados não encontrados
                    anotacoes_IA_notfound[nome] = {
                        "x1": falt_x1,
                        "y1": falt_y1,
                        "x2": falt_x2,
                        "y2": falt_y2,
                        "label": nome
                    }

                else:
                    if item_botao20_selecionado == nome:
                        x, y = posicoes[0]
                        falt_x1 = int(x - largura)
                        falt_y1 = int(y - altura)
                        falt_x2 = int(x + largura)
                        falt_y2 = int(y + altura)
                        # Adiciona à anotacoes_notpass para uso posterior
                        anotacoes_notpass[nome] = {
                            "x1": falt_x1,
                            "y1": falt_y1,
                            "x2": falt_x2,
                            "y2": falt_y2,
                            "label": nome
                        }

                    if not classe in classe_exibiba:
                        pass
                    else:
                        texto_contagem = f"{classe}: {contagem_classes.get(classe, 0)} un."
                        cv2.putText(img, texto_contagem, (70, y_offset),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.6, (255, 219, 0 ), 8)
                        y_offset += 70

                        classe_exibiba.append(classe)



            # print(len(faltando))
            if len(faltando) == 0:
                janelas_detectadas_atuais = set()  # <- CRUCIAL: fora do loop

                for box, cls, conf in zip(results.boxes.xyxy, results.boxes.cls, results.boxes.conf):
                    class_id = int(cls)
                    label = model.names[class_id]

                    for nome, info in componentes_esperados.items():

                        if info["classe"] == label and nome in lista:
                            pos = info["posicoes"][0]
                            if distancia(pos, centro_box(box)) < 50:
                                x1, y1, x2, y2 = map(int, box)
                                crop_realtime = imagem_sem_anotacoes[y1:y2, x1:x2]
                                crop_path = os.path.join("componentes", nome, f"{nome}.bmp")

                                if os.path.exists(crop_path):
                                    crop_salvo = cv2.imread(crop_path)
                                    if crop_salvo is not None and crop_realtime.shape[:2] == crop_salvo.shape[:2]:
                                        crop_salvo_resized = crop_salvo
                                        crop_realtime_resized = crop_realtime
                                    else:
                                        crop_salvo_resized = cv2.resize(crop_salvo, (crop_realtime.shape[1], crop_realtime.shape[0]))
                                        crop_realtime_resized = crop_realtime

                                    crop_salvo_gray = cv2.cvtColor(crop_salvo_resized, cv2.COLOR_BGR2GRAY)
                                    crop_realtime_gray = cv2.cvtColor(crop_realtime_resized, cv2.COLOR_BGR2GRAY)


                                else:
                                    comparacao = None

                                parametros_janelas = {}
                                
                                if comparacao is not None:
                                    try:
                                        if len(comparacao.shape) == 2:
                                            comparacao_color = cv2.cvtColor(comparacao, cv2.COLOR_GRAY2BGR)
                                        else:
                                            comparacao_color = comparacao.copy()

                                        if len(crop_realtime_resized.shape) == 2:
                                            crop_realtime_color = cv2.cvtColor(crop_realtime_resized, cv2.COLOR_GRAY2BGR)
                                        else:
                                            crop_realtime_color = crop_realtime_resized.copy()

                                        h1, w1 = comparacao_color.shape[:2]
                                        h2, w2 = crop_realtime_color.shape[:2]

                                        comparacao_color = cv2.resize(comparacao_color, (max(w1, w2), max(h1, h2)))
                                        crop_realtime_color = cv2.resize(crop_realtime_color, (max(w1, w2), max(h1, h2)))

                                        # Empilha as imagens horizontalmente (lado a lado)
                                        imagens_empilhadas = np.hstack([comparacao_color, crop_realtime_color])

                                        h_total, w_total = imagens_empilhadas.shape[:2]
                                        comparacao_com_botao = np.zeros((h_total + 50, w_total, 3), dtype=np.uint8)
                                        comparacao_com_botao[:h_total, :, :] = imagens_empilhadas

                                        # direiconar nome do componente e foto imagens_empilhadas para  imagens_componentes = defaultdict(lambda: None)
                                        # checar  se ja existe antes de adicionar
                                        try: 
                                            del imagens_componentes[nome]
                                            del crop_componentes[nome]
                                        except Exception as e: print(e)

                                        # print(f"Adicionando {nome} a imagens_componentes")
                                        imagens_componentes[nome] = imagens_empilhadas
                                        crop_componentes[nome] = crop_realtime_resized
                                        

                                        # acionar check para saber se o componente foi adicinado ou nao
                                        # adicionar nome para lista_botao20
                                        # if not lista_botao20.findItems(nome, Qt.MatchExactly):
                                        #     lista_botao20.addItem(nome)

                                        if lista_botao20.count() == 1:
                                            lista_botao20.setCurrentRow(0)
                                            item_botao20_selecionado = nome  # Salva o nome selecionado para uso no evento de teclado
                                            label_height = label_imagem_botao20.height()
                                            if label_height > 0:
                                                scale_factor = label_height / imagens_empilhadas.shape[0]
                                                new_width = int(imagens_empilhadas.shape[1] * scale_factor)
                                                resized_img = cv2.resize(imagens_empilhadas, (new_width, label_height), interpolation=cv2.INTER_AREA)
                                                # qimg = QImage(resized_img.data, resized_img.shape[1], resized_img.shape[0], resized_img.shape[1] * 3, QImage.Format_BGR888)
                                                # pixmap = QPixmap.fromImage(qimg)
                                                # Centraliza horizontalmente
                                                # label_imagem_botao20.setPixmap(pixmap)
                                                # label_imagem_botao20.setAlignment(Qt.AlignCenter)
                                            else:
                                                pass
                                                # fallback para o código antigo se altura não estiver disponível
                                                # label_imagem_botao20.setPixmap(QPixmap.fromImage(QImage(imagens_empilhadas.data, w_total, h_total, w_total * 3, QImage.Format_BGR888)).scaled(200, 200, Qt.KeepAspectRatio))
                                            
                                        # adicionar evento de item selecioando da lista, ao trocasr o item, trocar a imagem em label_imagem_botao20
                                        # lista_botao20.currentTextChanged.connect(lambda nome: atualizar_imagem_botao20(nome))
                                    
                                    except cv2.error as e:
                                        print(f"Erro ao abrir janela para {nome}: {e}")
                                        # janelas_crops_abertas.discard(janela_nome)
                                else:
                                    if not nome in lista_passed:
                                        lista_passed.append(nome)

                                        # items = lista_botao20.findItems(nome, Qt.MatchExactly)
                                        # if items:
                                        #     row = lista_botao20.row(items[0])
                                        #     lista_botao20.takeItem(row)

                # FORA do for principal: fecha janelas cujas falhas desapareceram
                if len(lista_test) == len(lista_passed):
                    if "= PASS" in "labelserial.text()":
                        pass
                    else:

                        if escrever_log and set_status != "FAIL":

                            # datahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            # upload_dados.upload_dados(serialnumber.strip(), set_status, datahora, datahora, rpassfolder_img)

                            escrever_log = False
                            aplicar_sharpness = False


if __name__ == "__main__":
    t = threading.Thread(target=threading_frame, daemon=True)
    t.start()
    t2 = threading.Thread(target=desenhar_resultado_ia_em_tempo_real, args=(frame_atual,), daemon=True)
    t2.start()
    asyncio.run(start_websocket())
