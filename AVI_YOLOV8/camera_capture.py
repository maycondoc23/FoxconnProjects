
import os
os.environ["ULTRALYTICS_HUB"] = "False"
os.environ["ULTRALYTICS_API_KEY"] = "none"
os.environ["ULTRALYTICS_OFFLINE"] = "True"

from ultralytics import YOLO
from collections import defaultdict
import math
from componentes import carregar_componentes, calibrar
import sys, cv2
import threading
import json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QThread
import os
import sys
from ctypes import cdll
from datetime import datetime
import requests
import xmltodict
from buscar_cor_pixel import mostrar_cor_pixel, verificar_pixels_na_imagem
import threading
import messagebox
import warnings
import upload_dados
warnings.filterwarnings("error")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller extract path
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Carregar a DLL:
dll_path = resource_path("libdmtx-64.dll")
cdll.LoadLibrary(dll_path)

from ler_serial import ler_serial

import sys
import os

import cv2
import gxipy as gx
import numpy as np
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap

from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtCore import Qt
import time


format = QSurfaceFormat()
format.setRenderableType(QSurfaceFormat.OpenGL)
format.setProfile(QSurfaceFormat.CoreProfile)
format.setVersion(3, 3)  # ou outra versão compatível
QSurfaceFormat.setDefaultFormat(format)


def aprender(model):
    model.train(
        data=r'dataset.yaml',
        epochs=100,
        imgsz=2600,
        batch=4,
        device='0',
        workers=0,
        freeze=10,
        lr0=0.0005
    )

# model = YOLO(r'C:\Users\mayconcosta\yolo-V8\runs\detect\train33\weights\best.pt')
model = YOLO(r'best_ktc.pt')

# model.export(format="onnx")

# exit()
# aprender(model)
# exit()
componentes_esperados = carregar_componentes()



def centro_box(box):
    x1, y1, x2, y2 = map(float, box)
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def distancia(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


imagem_entrada = ""
imagem_saida = ""
imagem_atual = None

class ItemFrame(QFrame):
    def __init__(self, nome, callback_selecao, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nome = nome
        self.callback_selecao = callback_selecao

    def mousePressEvent(self, event):
        self.callback_selecao(self.nome, self)  # chama a função que lida com a seleção
        super().mousePressEvent(event)


class Principal(QMainWindow):
    def __init__(self):
        global imagem_saida
        super().__init__()
        self.lista = []
        self.exibir_macara = False
        self.testing = False
        self.exibir_resultado = True
        self.janelas_crops_abertas = set()
        self.item_selecionado = None
        self.item_selecionado_nome = None
        self.larg_img = None
        self.escrever_log = True
        self.lista_passed = []
        self.lista_test = []
        self.serialnumber = "RY2570033359"
        self.modo = "setup"
        self.processando_frame = False
        self.componentes = {}
        self.aplicar_sharpness = False
        self.item_botao20_selecionado = None
        self.hora_teste = None
        self.set_fail = 0
        self.set_status = "PASS"
        self.anotacoes_IA = {}
        self.anotacoes_IA_notfound = {}
        self.anotacoes_notpass = {}
        self.frameatual = None
        self.atualizando_gui = False
        # criar dicionario capaz de guardar imagens e nome de componente
        self.rpassfolder_img = defaultdict(lambda: None)
        self.imagens_componentes = defaultdict(lambda: None)
        self.crop_componentes = defaultdict(lambda: None)
        
        for componente, info in componentes_esperados.items():
            if info["Compare"] == True:
                self.lista_test.append(componente)

        self.setWindowTitle("AVI TEST")
        # self.resize(1400, 800)
    
        self.caminho_json = "setup_componentes.json"

        # Use um QWidget como central e layouts para alinhar corretamente
        central = QWidget()
        layout_principal = QHBoxLayout(central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        self.layout_imagem_botoes = QVBoxLayout()
        self.layout_imagem_botoes.setContentsMargins(0, 0, 0, 0)
        self.layout_imagem_botoes.setSpacing(0)

        # Cria um layout horizontal para os labels de status e serial
        status_layout = QHBoxLayout()

        self.labelserial = QPushButton("SN:")

        # alinhar texto a esquerda
        self.labelserial.setStyleSheet("font-size: 30px; text-align: left; padding-left: 15px; font-weight: bold")
        self.labelserial.setMinimumHeight(70)
        self.labelserial.setMaximumHeight(70)
        self.labelserial.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.labelstatus = QPushButton("Awaiting")
        self.labelstatus.setStyleSheet("font-size: 30px; background-color: dark; font-weight: bold; color: white;")
        self.labelstatus.setEnabled(False)
        self.labelstatus.setMinimumHeight(70)
        self.labelstatus.setMaximumHeight(70)
        self.labelstatus.setMinimumWidth(300)
        self.labelstatus.setMaximumWidth(300)

        status_layout.addWidget(self.labelserial)
        status_layout.addWidget(self.labelstatus)
        

        self.label_imagem = QLabel()
        self.label_imagem.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label_imagem.setAlignment(Qt.AlignCenter)

        self.layout_imagem_botoes.addLayout(status_layout)
        self.layout_imagem_botoes.addWidget(self.label_imagem)

        # Layout horizontal para dividir o espaço do botao_20
        layout_botao20 = QHBoxLayout()

        # Lista no canto esquerdo ocupando 30% da altura do botao_20
        self.lista_botao20 = QListWidget()
        # Ajusta a largura para 30% do botao_20
        self.lista_botao20.setStyleSheet("background-color: lightgrey; border: 1px solid black;border-radius: 5px; color: black; font-weight: bold; font-size: 20px")
        self.lista_botao20.setMaximumWidth(int(self.width() * 0.3))
        self.lista_botao20.currentTextChanged.connect(self.atualizar_imagem_botao20)

        # Label de imagem no canto direito ocupando o restante
        self.label_imagem_botao20 = QLabel()
        self.label_imagem_botao20.setAlignment(Qt.AlignCenter)
        self.label_imagem_botao20.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label_imagem_botao20.setStyleSheet("background-color: lightgrey; border: 1px solid black;border-radius: 5px;")

        layout_botao20.addWidget(self.lista_botao20, 3)
        layout_botao20.addWidget(self.label_imagem_botao20, 7)

        # Widget container para altura fixa
        widget_botao20 = QWidget()
        widget_botao20.setLayout(layout_botao20)
        screen_height = QApplication.primaryScreen().size().height()
        widget_botao20.setStyleSheet("background-color: lightgrey;")
        widget_botao20.setMinimumHeight(int(screen_height * 0.30))
        widget_botao20.setMaximumHeight(int(screen_height * 0.30))

        self.layout_imagem_botoes.addWidget(widget_botao20)

        layout_botoes = QHBoxLayout()

        btnmask = QPushButton("DEFINIR MASCARA PADRAO")
        btnmask.setStyleSheet("background-color: blue; font-weight: bold")
        btnmask.setMinimumHeight(30)
        self.btnmask = btnmask
        self.btnmask.clicked.connect(self.definirmask)  
        self.btnmask.setVisible(True)  # Desabilita o botão até que a máscara seja definida

        btn1 = QPushButton("AREA DE AJUSTES  >")
        btn1.setStyleSheet("background-color: blue; font-weight: bold")
        btn1.setMinimumHeight(30)
        self.btn1 = btn1
        self.btn1.clicked.connect(self.mudar_modo)  
        self.btn1.setVisible(False)

        self.layout_imagem_botoes.addLayout(layout_botoes)
            
        self.layout_lista_widget = QWidget()
        self.layout_lista_widget.setVisible(False)  # Inicialmente invisível
        layout_lista = QVBoxLayout(self.layout_lista_widget)
        layout_lista.setContentsMargins(0, 0, 0, 0)
        layout_lista.setSpacing(0)

        # ➕ TÍTULO DO FRAME
        self.labelmodo = QPushButton("TEST AREA")
        self.labelmodo.setStyleSheet("font-size: 30px; background-color: lightgrey; font-weight: bold; color: black;")
        self.labelmodo.setEnabled(False)
        self.labelmodo.setMinimumHeight(100)
        self.labelmodo.setMaximumHeight(100)

        layout_lista.addWidget(self.labelmodo)
        # hide em layout_lista.addStretch()
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("background-color: lightgrey;")

        self.scroll_area.setWidgetResizable(True)
        self.lista_widget = QWidget()
        self.lista_layout = QVBoxLayout()
        self.lista_widget.setLayout(self.lista_layout)
        self.scroll_area.setWidget(self.lista_widget)
        layout_lista.addWidget(self.scroll_area)

        mover_layout = QHBoxLayout()
        self.combo_direcao = QComboBox()
        self.combo_direcao.setStyleSheet("background-color: rgb(73, 73, 185); font-weight: bold")
        self.combo_direcao.addItems(["esquerda", "direita", "cima", "baixo"])
        mover_layout.addWidget(self.combo_direcao)
        self.combo_direcao.setVisible(True)
    

        btn_mover = QPushButton("Mover")
        self.mover = btn_mover
        btn_mover.clicked.connect(self.mover_componentes_direcao)
        btn_mover.setStyleSheet("background-color: blue; font-weight: bold")
        mover_layout.addWidget(btn_mover)
        btn_mover.setVisible(True)

        layout_lista.addLayout(mover_layout)

        layout_lista.addWidget(btnmask)
        layout_lista.addWidget(btn1)

    

        layout_toggle = QVBoxLayout()
        layout_toggle.setContentsMargins(0, 0, 0, 0)
        layout_toggle.setSpacing(0)
        layout_toggle.addStretch()

        # Adicione widgets ao layout principal com proporções fixas
        layout_principal.addLayout(self.layout_imagem_botoes, 7)
        layout_principal.addLayout(layout_toggle, 0)
        layout_principal.addWidget(self.layout_lista_widget, 3)

        self.setCentralWidget(central)

        self.carregar_dados_json()

        # Inicializa câmera Daheng
        self.device_manager = gx.DeviceManager()
        self.device_manager.update_device_list()
        if self.device_manager.get_device_number() == 0:
            raise RuntimeError("Nenhuma câmera Daheng conectada.")

        self.cam = self.device_manager.open_device_by_index(1)

        self.cam.stream_on()

        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_frame)
        self.timer.start()
        

        # threading.Thread(target=self.atualizar_frame, args=(), daemon=True).start()
        threading.Thread(target=self.threading_frame, args=(), daemon=True).start()

        self.label_imagem.setStyleSheet("background-color: lightgrey;")

    def mudar_modo(self):
        if self.modo == "teste":
            self.modo = "setup"
            self.labelmodo.setText("SETUP AREA")
            self.btn1.setText("< AREA DE TESTE")
            self.btnmask.setVisible(True)  # Habilita o botão de definir máscara
            self.mover.setVisible(True)  # Habilita o botão de mover componentes
            self.combo_direcao.setVisible(True)  # Habilita o combo de direção
            
        else:
            self.modo = "teste"
            self.labelmodo.setText("TEST AREA")
            self.btn1.setText("AREA DE AJUSTES >")
            self.btnmask.setVisible(False)  # Desabilita o botão de definir máscara
            self.mover.setVisible(False)
            self.combo_direcao.setVisible(False)  # Desabilita o combo de direção
        self.carregar_dados_json()

    def toggle_Compare(self, nome, botao):
        if nome in self.componentes:
            novo_estado = not self.componentes[nome].get("Compare", False)
            if novo_estado == True:
                self.lista.append(nome)
            else:
                self.lista.remove(nome)
            self.componentes[nome]["Compare"] = novo_estado
            self.atualizar_cor_botao(botao, novo_estado)
            self.salvar_componentes()
            print(self.lista)
            # self.carregar_dados_json()

    def editar_nome_componente(self, nome_antigo):
        if nome_antigo not in self.componentes:
            return

        novo_nome, ok = QInputDialog.getText(self, "Editar Nome do Componente", "Nome do Componente:", text=nome_antigo)

        if ok and novo_nome and novo_nome != nome_antigo:
            if novo_nome in self.componentes:
                QMessageBox.warning(self, "Erro", f"O nome '{novo_nome}' já existe.")
                return
            self.componentes[novo_nome] = self.componentes.pop(nome_antigo)

        # Atualiza o nome também em componentes_esperados, se necessário
        for nome, info in list(componentes_esperados.items()):
            if nome == nome_antigo:
                componentes_esperados[novo_nome] = componentes_esperados.pop(nome_antigo)
                info = componentes_esperados[novo_nome]

        # Pergunta e salva nova área
        if novo_nome in componentes_esperados:
            area = componentes_esperados[novo_nome].get("area", 100)
            nova_area, ok = QInputDialog.getText(self, "Editar Area de Comparação", "Area (Numero Inteiro):", text=str(area))
            if ok and nova_area.isdigit():
                nova_area_int = int(nova_area)
                componentes_esperados[novo_nome]["area"] = nova_area_int
                if novo_nome in self.componentes:
                    self.componentes[novo_nome]["area"] = nova_area_int
                    
        #  pergunta nova quantidade de pads
        if novo_nome in componentes_esperados:
            pads = componentes_esperados[novo_nome].get("pads", 4)
            novo_pad, ok = QInputDialog.getText(self, "Editar Qty de Pads/Terminais", "Pads (Numero Inteiro):", text=str(pads))
            if ok and novo_pad.isdigit():
                novo_pad_int = int(novo_pad)
                componentes_esperados[novo_nome]["pads"] = novo_pad_int
                if novo_nome in self.componentes:
                    self.componentes[novo_nome]["pads"] = novo_pad_int

        #  pergunta nova quantidade de pads
        if novo_nome in componentes_esperados:
            modo = componentes_esperados[novo_nome].get("compare_mode", 1)
            novo_modo, ok = QInputDialog.getText(self, "Editar Modo de comparação", "modo de comparação (Numero Inteiro):", text=str(modo))
            if ok and novo_modo.isdigit() and int(novo_modo) in [1, 2]:
                novo_modo_int = int(novo_modo)
                componentes_esperados[novo_nome]["compare_mode"] = novo_modo_int
                if novo_nome in self.componentes:
                    self.componentes[novo_nome]["compare_mode"] = novo_modo_int

        self.salvar_componentes()
        self.carregar_dados_json()
            
    def definirmask(self):
        return
        global componentes_esperados
        calibrar(model, imagem_entrada)
        self.carregar_dados_json()
        componentes_esperados = carregar_componentes()
        QMessageBox.information(self, "Done", f"Nova Mascara de teste definida")
        
    def mover_componentes_direcao(self):
        global componentes_esperados

        print(self.item_selecionado_nome)
        direcao = self.combo_direcao.currentText()
        deslocamento =5
        if self.item_selecionado_nome == None:
            print("Nenhum item selecionado. Movendo todos os componentes.")
            for nome, info in self.componentes.items():
                pos = info.get("posicoes", [[0, 0]])[0]

                if direcao == "direita":
                    pos[0] += deslocamento
                elif direcao == "esquerda":
                    print(pos)
                    pos[0] -= deslocamento
                    print(f"Movendo {nome} para a esquerda")
                elif direcao == "cima":
                    pos[1] -= deslocamento
                elif direcao == "baixo":
                    pos[1] += deslocamento

                info["posicoes"][0] = pos
        else:
            print(f"Movendo {self.item_selecionado_nome} para {direcao}")
            for nome, info in self.componentes.items():
                if nome == self.item_selecionado_nome:
                    pos = info.get("posicoes", [[0, 0]])[0]

                    if direcao == "direita":
                        pos[0] += deslocamento
                    elif direcao == "esquerda":
                        print(pos)
                        pos[0] -= deslocamento
                        print(f"Movendo {nome} para a esquerda")
                    elif direcao == "cima":
                        pos[1] -= deslocamento
                    elif direcao == "baixo":
                        pos[1] += deslocamento

                    info["posicoes"][0] = pos

        self.salvar_componentes()
        componentes_esperados = carregar_componentes()

        with open(self.caminho_json, 'r') as f:
            self.componentes = json.load(f)
        

    def carregar_dados_json(self):
        self.lista.clear()
        
        if not os.path.exists(self.caminho_json):
            return

        with open(self.caminho_json, 'r') as f:
            self.componentes = json.load(f)

        while self.lista_layout.count():
            item = self.lista_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        for nome, dados in self.componentes.items():
            if "Compare" not in dados:
                dados["Compare"] = False

            if "area" not in dados:
                dados["area"] = 200

            if "compare_mode" not in dados:
                dados["compare_mode"] = 1

            if "pads" not in dados:
                dados["pads"] = 4

            if dados["Compare"] == True:
                self.lista.append(nome)
            if self.modo == "setup":
                item_frame = ItemFrame(nome, self.selecionar_item)
            else:
                item_frame = ItemFrame(nome, lambda n, f: None)
            item_layout = QHBoxLayout(item_frame)

            nome_label = QLabel(nome)
            nome_label.setStyleSheet("font-weight: bold")
            nome_label.setFixedWidth(160)
            if self.modo == "setup":

                # Botão Comparar
                btn_short = QPushButton("Comparar")
                btn_short.setCheckable(True)
                btn_short.setChecked(dados["Compare"])
                btn_short.setObjectName(nome)
                self.atualizar_cor_botao(btn_short, dados["Compare"])
                btn_short.clicked.connect(lambda _, n=nome, b=btn_short: self.toggle_Compare(n, b))
                self.selecionar_item(nome, item_frame)
                # Botão Editar
                btn_edit = QPushButton("Editar")
                btn_edit.setStyleSheet("font-weight: bold; background-color: dark")
                btn_edit.clicked.connect(lambda _, n=nome: self.editar_nome_componente(n))

                # Botão Excluir
                btn_excluir = QPushButton("Excluir")
                btn_excluir.setStyleSheet("font-weight: bold; background-color: dark")
                btn_excluir.clicked.connect(lambda _, n=nome: self.excluir_componente(n))

                item_layout.addWidget(nome_label)
                item_layout.addWidget(btn_short)
                item_layout.addWidget(btn_edit)
                item_layout.addWidget(btn_excluir)
            elif self.modo == "teste":
                btn_teste = QProgressBar()
                # colocar texto no centro do botão
                btn_teste.setFormat("awaiting")
                btn_teste.setValue(0)
                
                btn_teste.setStyleSheet("font-size: 12px; background-color: dark; font-weight: bold; color: white;")

                btn_teste.setMinimumHeight(35)
                btn_teste.setMaximumHeight(35)
                btn_teste.setEnabled(False)  # Desativa o botão para deixar claro que é só informativo
                item_layout.addWidget(nome_label)
                item_layout.addWidget(btn_teste)

            self.lista_layout.addWidget(item_frame)

        print(self.lista)
        self.salvar_componentes()
        

    def status_componente_botao(self, nome, status, value):
        
        if self.atualizando_gui:
            print("Atualização de GUI em andamento, ignorando nova atualização.")
            return
        self.atualizando_gui = True

        print(f"Atualizando status do componente {nome} para {status} com valor {value}")
        cor = "green" if status == "PASS" else "dark"


        if nome is None or nome == "" or nome == "":
            print("Nome do componente não fornecido.")
            for i in range(self.lista_layout.count()):
                item = self.lista_layout.itemAt(i).widget()
                if isinstance(item, ItemFrame):
                    for bar in item.findChildren(QProgressBar):
                        bar.setFormat(status)
                        bar.setValue(value)
                        # Use QProgressBar::chunk to set the fill color
                        bar.setStyleSheet(
                            f"""
                            QProgressBar {{
                                font-size: 12px;
                                font-weight: bold;
                                color: white;
                                background-color: #222;
                                border: 1px solid #555;
                                border-radius: 5px;
                                text-align: center;
                            }}
                            QProgressBar::chunk {{
                                background-color: {cor};
                            }}
                            """
                        )

            self.atualizando_gui = False
            return
            
        elif nome == "Testing...":
            for i in range(self.lista_layout.count()):
                item = self.lista_layout.itemAt(i).widget()
                if item.nome in self.lista_test:
                    if isinstance(item, ItemFrame):
                        for bar in item.findChildren(QProgressBar):
                            if bar.text() in ["PASS", "Testing..."]:
                                continue
                            bar.setFormat(status)
                            bar.setValue(value)
                            # Use QProgressBar::chunk to set the fill color
                            bar.setStyleSheet(
                                f"""
                                QProgressBar {{
                                    font-size: 12px;
                                    font-weight: bold;
                                    color: white;
                                    background-color: #222;
                                    border: 1px solid #555;
                                    border-radius: 5px;
                                    text-align: center;
                                }}
                                QProgressBar::chunk {{
                                    background-color: {cor};
                                }}
                                """
                            )
                else:
                    if isinstance(item, ItemFrame):
                        for bar in item.findChildren(QProgressBar):
                            if bar.text() in ["PASS", "Testing..."]:
                                continue
                            bar.setFormat("PASS")
                            bar.setValue(100)
                            # Use QProgressBar::chunk to set the fill color
                            bar.setStyleSheet(
                                f"""
                                QProgressBar {{
                                    font-size: 12px;
                                    font-weight: bold;
                                    color: white;
                                    background-color: #222;
                                    border: 1px solid #555;
                                    border-radius: 5px;
                                    text-align: center;
                                }}
                                QProgressBar::chunk {{
                                    background-color: green;
                                }}
                                """
                            )
            self.atualizando_gui = False

            return


        for i in range(self.lista_layout.count()):
            item = self.lista_layout.itemAt(i).widget()
            if isinstance(item, ItemFrame) and item.nome == nome:
                for bar in item.findChildren(QProgressBar):
                    bar.setFormat(status)
                    bar.setValue(value)
                    # Use QProgressBar::chunk to set the fill color
                    bar.setStyleSheet(
                        f"""
                        QProgressBar {{
                            font-size: 12px;
                            font-weight: bold;
                            color: white;
                            background-color: #222;
                            border: 1px solid #555;
                            border-radius: 5px;
                            text-align: center;
                        }}
                        QProgressBar::chunk {{
                            background-color: {cor};
                        }}
                        """
                    )
                break
            # Removido código de QPainter manual para evitar travamentos e recursão de repaint
        self.atualizando_gui = False
            
    def selecionar_item(self, nome, frame):
        if self.item_selecionado_nome == nome:
            self.item_selecionado.setStyleSheet("")
            for label in self.item_selecionado.findChildren(QLabel):
                label.setStyleSheet("color: black; font-weight: bold;")

            self.item_selecionado = None
            self.item_selecionado_nome = None
            print(f"Item {nome} desmarcado")
            return

        self.item_selecionado_nome = nome

        if self.item_selecionado:
            self.item_selecionado.setStyleSheet("")
            for btn in self.item_selecionado.findChildren(QPushButton):
                nome_btn = btn.objectName()
                if nome_btn and nome_btn in self.componentes:
                    if self.componentes[nome_btn].get("Compare", False):
                        # Botão 'Comparar' ativo fica verde, com texto preto e bold
                        btn.setStyleSheet("background-color: lightgreen; color: black; font-weight: bold;")
                    else:
                        # Outros botões ficam branco e font normal
                        btn.setStyleSheet("color: white; font-weight: bold; background-color: dark;")
                else:
                    btn.setStyleSheet("color: white; font-weight: bold; background-color: dark;")
            for label in self.item_selecionado.findChildren(QLabel):
                # Label volta para fonte normal e cor branca
                label.setStyleSheet("color: black; font-weight: bold;")

        # Atualiza o item selecionado
        self.item_selecionado = frame
        frame.setStyleSheet("background-color: rgb(100, 100, 255);")

        # Ajusta os botões do item selecionado
        for btn in frame.findChildren(QPushButton):
            if btn.objectName() == nome and btn.isChecked():
                btn.setStyleSheet("background-color: lightgreen; color: black; font-weight: bold;")
            else:
                btn.setStyleSheet("font-weight: bold; color: white; background-color: dark;")
        
        # Ajusta os labels do item selecionado para bold e preto
        for label in frame.findChildren(QLabel):
            label.setStyleSheet("color: white; font-weight: bold; background-color: dark;")

        print(f"Item selecionado: {nome}")


    def limpar_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)


    def atualizar_frame(self):
        if self.processando_frame:
            # print("Aguardando processamento do frame atual...")
            return  
        if self.frameatual is None:
            return

        # print("Processando frame...")
        self.processando_frame = True

        global imagem_entrada
        global imagem_atual
        # raw_image = self.cam.data_stream[0].get_image()
        # # horario da imagem:

        # if raw_image is None:
        #     return
        # # raw_image.defective_pixel_correct()
        # rgb_image = raw_image.convert("RGB")
        self.frame = self.frameatual
        if self.aplicar_sharpness:
            try:
                self.frame.sharpen(1)  
            except Warning as w:
                print("Warning ao aplicar sharpness:", w)
            except Exception as e:
                print("Erro ao aplicar sharpness:", e)
            # pass
            # print("Aplicando sharpness")
        
        rgb_image = self.frame.get_numpy_array()

        # PRINTAR O TAMANHO DO ARRAY 
        # print("Tamanho do array RGB:", rgb_image.shape)
        # exibir tamanho do array em megabytes
        tamanho_mb = rgb_image.nbytes / (1024 * 1024)
        print(f"Tamanho do array RGB: {tamanho_mb:.2f} MB")

        imagem_atual = self.frame
        imagem_entrada = imagem_atual

        if self.exibir_resultado:
            
            thread = threading.Thread(target=self.desenhar_resultado_ia_em_tempo_real, args=(rgb_image,), daemon=True)
            thread.start()

            print("Resultado IA desenhado em tempo real")
            # print("Resultado IA desenhado em tempo real")
            
            # self.desenhar_resultado_ia_em_tempo_real(rgb_image)
            self.atualizar_imagem_botao20(self.item_botao20_selecionado)

        
    def recarregarimagem(self):
        self.exibir_macara = False
  
    def excluir_componente(self, nome):
        global componentes_esperados
        if nome in self.componentes:
            resposta = QMessageBox.question(
                self,
                "Confirmar Exclusão",
                f"Tem certeza que deseja excluir o componente '{nome}'?",
                QMessageBox.Yes | QMessageBox.No
            )

            if resposta == QMessageBox.Yes:
                del self.componentes[nome]
                self.salvar_componentes()
                self.carregar_dados_json()
                componentes_esperados = carregar_componentes()


    def atualizar_cor_botao(self, botao, ativado):
        if ativado:
            botao.setStyleSheet("background-color: lightgreen; font-weight: bold; color:black")
        else:
            botao.setStyleSheet("")  # Volta ao estilo padrão

    def desenhar_retangulo(self, centro, tamanho):
        global imagem_atual
        x, y = centro
        w, h = tamanho
        x1 = int(x - w / 2)
        y1 = int(y - h / 2)

        
        imagem_copia = imagem_atual.copy()

        painter = QPainter(imagem_copia)
        pen = QPen(Qt.green, 5)
        painter.setPen(pen)
        painter.drawRect(QRect(x1, y1, w, h))
        painter.end()

        self.pixmap_exibida = imagem_copia.scaledToWidth(980, Qt.SmoothTransformation)
        self.label_imagem.setPixmap(self.pixmap_exibida)

    def salvar_componentes(self):
        try:
            with open(self.caminho_json, 'w') as f:
                json.dump(self.componentes, f, indent=4)
            print("Componentes salvos com sucesso.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao salvar JSON: {str(e)}")


    def closeEvent(self, event):
        # self.timer.stop()
        self.cam.stream_off()
        self.cam.close_device()
        # event.accept()

    def desenhar_resultado_ia_em_tempo_real(self, img):
        # return
        global serial, componentes_esperados
        janelas_detectadas_atuais = set()

        if self.larg_img == None:
            self.larg_img = self.label_imagem.width()
        if self.hora_teste is None:
            self.hora_teste = datetime.now().strftime("%H%M%S")

        detectou = False

        imagem_sem_anotacoes = img

        
        contagem_classes = defaultdict(int)
        # print("Detectando objetos com IA...")
        cv2.imwrite("imagem_entrada.png", img)
        results = model.predict(img, conf=0.40, verbose=False)[0]


        # print("Objetos detectados:", results.boxes.cls)
        boxes = results.boxes.xyxy
        centros_detectados = [centro_box(box) for box in boxes]
        self.processando_frame = False

        detectados_nome = []
        
        self.anotacoes_IA.clear()
        self.anotacoes_notpass.clear()
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
                self.aplicar_sharpness = True

                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                texto = f"{label} {conf_pct}%"
                cv2.putText(img, texto, (x1, y1-20),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 6)

                cv2.imwrite("serial.png", img[y1:y2, x1:x2])
                recorte = imagem_sem_anotacoes[y1:y2, x1:x2]
                label = self.labelserial.text()

                if label in ["Awaiting...", "", " ", "Serial:", "SN:", "Aguardando novo Serial..."] or label.strip() == "= PASS":
                    label = self.labelserial.text()


                    print("Lendo novo SerialNumber...")
                    self.testing = False
                    self.lista_passed.clear()
                    serial = ler_serial(recorte)

                    # print(f"Serial lido: {serial}")
                    # self.labelserial.setText(f"SN:{serial}")
                    labelnova = f"SN:{serial}"
                    if not labelnova in ["Awaiting...", "", " ", "Serial:", "SN:", "Aguardando novo Serial..."]:
                        if self.serialnumber != serial:
                            self.serialnumber = serial
                            self.labelserial.setText(f"SN:{serial}")

                            self.hora_teste = datetime.now().strftime("%H%M%S")
                            self.lista_passed.clear()
                            self.crop_componentes.clear()
                            self.imagens_componentes.clear()
                            self.rpassfolder_img.clear()
        
                            self.item_botao20_selecionado = None

                            self.lista_botao20.clear()
                            self.label_imagem_botao20.clear()
                            self.set_fail = 0
                            self.set_status = "PASS"

                            self.aplicar_sharpness = True
                            self.testing = True
                            self.escrever_log = True

                            # class StatusThread3(QThread):
                            #     update_status3 = pyqtSignal(str, str, int)

                            #     def run(self):
                            #         self.update_status3.emit('DATAMATRIX1', "PASS", 100)
                                    
                            # self.status_thread = StatusThread3()
                            # self.status_thread.update_status3.connect(self.status_componente_botao)
                            # self.status_thread.start()
                            # self.status_thread.wait()
                            # self.status_thread.finished.connect(self.status_thread.deleteLater)

                            time.sleep(0.1)
                            
                        
                else:
                    pass
                    # print(f"Serial ja lido")
            else:
                # inputar dados no dicionario self.anotacoes_IA para cada componente detectado para depois fazer todas anotacoes de uma vez
                # Conta quantos já existem com esse label para criar label1, label2, etc.
                count = sum(1 for k in self.anotacoes_IA if k.startswith(label))
                label_nomeado = f"{label}{count + 1}"
                self.anotacoes_IA[label_nomeado] = {
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
        self.anotacoes_IA_notfound.clear()

        if self.testing != None:
            self.testing = True
        
        if not detectou:
            self.labelserial.setText("Aguardando novo Serial...")

            print("Nenhum objeto detectado")
            print("Nenhum objeto detectado")
            print("Nenhum objeto detectado")
            self.aplicar_sharpness = False
            self.testing = False
            self.escrever_log = True
            

            cv2.putText(img, "Nenhum objeto detectado", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            if self.labelstatus.text() != "Awaiting...":
                self.labelstatus.setText("Awaiting...")
                self.labelstatus.setStyleSheet("font-size: 30px; background-color: dark; font-weight: bold; color: white;")

                # thread = threading.Thread(target=self.status_componente_botao, args=(None, "Awaiting...", 0), daemon=True)
                # thread.start()
                # thread.join()

                # class StatusThread2(QThread):
                #     update_status2 = pyqtSignal(str, str, int)

                #     def run(self):
                #         self.update_status2.emit(None, "Awaiting...", 0)
                        
                # self.status_thread = StatusThread2()
                # self.status_thread.update_status2.connect(self.status_componente_botao)
                # self.status_thread.start()
                # self.status_thread.wait()
                # self.status_thread.finished.connect(self.status_thread.deleteLater)
                # self.status_componente_botao(None, value=0, status="Awaiting...")

            self.lista_passed.clear()
            self.crop_componentes.clear()
            self.imagens_componentes.clear()
            self.lista_botao20.clear()
            self.label_imagem_botao20.clear()
            self.set_fail = 0
            self.rpassfolder_img.clear()
            self.set_status = "PASS"
            
            # janelas_a_fechar = self.janelas_crops_abertas - janelas_detectadas_atuais
            # for janela in janelas_a_fechar:
            #     try:
            #         cv2.destroyWindow(janela)
            #     except cv2.error as e:
            #         print(f"Erro ao fechar janela {janela}: {e}")
            #     self.janelas_crops_abertas.discard(janela)

        if self.testing  and self.set_status != "FAIL":
            self.aplicar_sharpness = True

            if self.labelstatus.text() != "Testing..." and self.labelstatus.text() != "PASS":
                self.labelstatus.setText("Testing...")

                # Usando QThread para atualizar status_componente_botao sem problemas de repaint

                # class StatusThread(QThread):
                #     update_status = pyqtSignal(str, str, int)

                #     def run(self):
                #         self.update_status.emit("Testing...", "Testing...", 50)

                # self.status_thread = StatusThread()
                # self.status_thread.update_status.connect(self.status_componente_botao)
                # self.status_thread.start()
                # self.status_thread.wait()
                # self.status_thread.finished.connect(self.status_thread.deleteLater)
                # self.status_componente_botao("Testing...", value=50, status="Testing...")

                # self.labelstatus.setStyleSheet("font-size: 30px; background-color: darkblue; font-weight: bold; color: white;")

            # checar se labelstatus já está definido para testing, se ja tiver, nao executar novmaente status_componente_botao


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
                    self.anotacoes_IA_notfound[nome] = {
                        "x1": falt_x1,
                        "y1": falt_y1,
                        "x2": falt_x2,
                        "y2": falt_y2,
                        "label": nome
                    }

                else:
                    if self.item_botao20_selecionado == nome:
                        x, y = posicoes[0]
                        falt_x1 = int(x - largura)
                        falt_y1 = int(y - altura)
                        falt_x2 = int(x + largura)
                        falt_y2 = int(y + altura)
                        # Adiciona à anotacoes_notpass para uso posterior
                        self.anotacoes_notpass[nome] = {
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

                        if info["classe"] == label and nome in self.lista:
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

                                    comparacao = self.contarpads(crop_realtime_gray, info["area"], info["pads"], nome, 0.04, info["compare_mode"])

                                else:
                                    comparacao = None

                                self.parametros_janelas = {}
                                
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

                                        # direiconar nome do componente e foto imagens_empilhadas para  self.imagens_componentes = defaultdict(lambda: None)
                                        # checar  se ja existe antes de adicionar
                                        try: 
                                            del self.imagens_componentes[nome]
                                            del self.crop_componentes[nome]
                                        except Exception as e: print(e)

                                        # print(f"Adicionando {nome} a imagens_componentes")
                                        self.imagens_componentes[nome] = imagens_empilhadas
                                        self.crop_componentes[nome] = crop_realtime_resized
                                        

                                        # acionar check para saber se o componente foi adicinado ou nao
                                        # adicionar nome para self.lista_botao20
                                        if not self.lista_botao20.findItems(nome, Qt.MatchExactly):
                                            self.lista_botao20.addItem(nome)

                                        if self.lista_botao20.count() == 1:
                                            self.lista_botao20.setCurrentRow(0)
                                            self.item_botao20_selecionado = nome  # Salva o nome selecionado para uso no evento de teclado
                                            label_height = self.label_imagem_botao20.height()
                                            if label_height > 0:
                                                scale_factor = label_height / imagens_empilhadas.shape[0]
                                                new_width = int(imagens_empilhadas.shape[1] * scale_factor)
                                                resized_img = cv2.resize(imagens_empilhadas, (new_width, label_height), interpolation=cv2.INTER_AREA)
                                                qimg = QImage(resized_img.data, resized_img.shape[1], resized_img.shape[0], resized_img.shape[1] * 3, QImage.Format_BGR888)
                                                pixmap = QPixmap.fromImage(qimg)
                                                # Centraliza horizontalmente
                                                self.label_imagem_botao20.setPixmap(pixmap)
                                                self.label_imagem_botao20.setAlignment(Qt.AlignCenter)
                                            else:
                                                # fallback para o código antigo se altura não estiver disponível
                                                self.label_imagem_botao20.setPixmap(QPixmap.fromImage(QImage(imagens_empilhadas.data, w_total, h_total, w_total * 3, QImage.Format_BGR888)).scaled(200, 200, Qt.KeepAspectRatio))
                                            
                                        # adicionar evento de item selecioando da lista, ao trocasr o item, trocar a imagem em self.label_imagem_botao20
                                        # self.lista_botao20.currentTextChanged.connect(lambda nome: self.atualizar_imagem_botao20(nome))
                                    
                                    except cv2.error as e:
                                        print(f"Erro ao abrir janela para {nome}: {e}")
                                        # self.janelas_crops_abertas.discard(janela_nome)
                                else:
                                    try:
                                        if self.labelstatus.text() != "PASS":
                                            if not nome in self.lista_passed:
                                                class StatusThread2(QThread):
                                                    update_status3 = pyqtSignal(str, str, int)

                                                    def run(self):
                                                        self.update_status3.emit(nome, "PASS", 100)
                                                        
                                                # self.status_thread = StatusThread2()
                                                # self.status_thread.update_status3.connect(self.status_componente_botao)
                                                # self.status_thread.start()
                                                # self.status_thread.wait()
                                                # self.status_thread.finished.connect(self.status_thread.deleteLater)
                                            else:
                                                print("Componente já passou:", nome, "Nao atualizando status Novamente.")
                                            # self.status_componente_botao(nome, value=100, status="PASS")

                                    except Exception as e:
                                        print(e)

                                    if not nome in self.lista_passed:
                                        self.lista_passed.append(nome)
                                        items = self.lista_botao20.findItems(nome, Qt.MatchExactly)
                                        if items:
                                            row = self.lista_botao20.row(items[0])
                                            self.lista_botao20.takeItem(row)

                # FORA do for principal: fecha janelas cujas falhas desapareceram
                janelas_a_fechar = self.janelas_crops_abertas - janelas_detectadas_atuais
                for janela in janelas_a_fechar:
                    try:
                        cv2.destroyWindow(janela)
                    except cv2.error as e:
                        print(f"Erro ao fechar janela {janela}: {e}")
                    self.janelas_crops_abertas.discard(janela)

                # print(self.lista_passed)
                # print(self.lista_test)
                if len(self.lista_test) == len(self.lista_passed):
                    if "= PASS" in self.labelserial.text():
                        pass
                    else:
                        self.labelstatus.setText(f"PASS")
                        self.labelstatus.setStyleSheet("font-size: 30px; background-color: green; font-weight: bold; color: white;")


                        if self.escrever_log and self.set_status != "FAIL":
                            self.enviar_log()

                            datahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            upload_dados.upload_dados(self.serialnumber.strip(), self.set_status, datahora, datahora, self.rpassfolder_img)

                            self.escrever_log = False
                            self.aplicar_sharpness = False
                            self.labelserial.setText("Aguardando novo Serial...")


                            


    def atualizar_imagem_botao20(self, nome):
        """
        Atualiza a imagem exibida em self.label_imagem_botao20 de acordo com o item selecionado na lista_botao20.
        """
        
        # print("Atualizando imagem do botão 20 para:", nome)
        self.item_botao20_selecionado = nome  # Salva o nome selecionado para uso no evento de teclado
        imagem = self.imagens_componentes.get(nome)

        if imagem is not None:
            label_height = self.label_imagem_botao20.height()
            if label_height > 0:
                scale_factor = label_height / imagem.shape[0]
                new_width = int(imagem.shape[1] * scale_factor)
                resized_img = cv2.resize(imagem, (new_width, label_height), interpolation=cv2.INTER_AREA)
                qimg = QImage(resized_img.data, resized_img.shape[1], resized_img.shape[0], resized_img.shape[1] * 3, QImage.Format_BGR888)
                pixmap = QPixmap.fromImage(qimg)
                self.label_imagem_botao20.setPixmap(pixmap)
                self.label_imagem_botao20.setAlignment(Qt.AlignCenter)
            else:
                h, w = imagem.shape[:2]
                qimg = QImage(imagem.data, w, h, w * 3, QImage.Format_BGR888)
                self.label_imagem_botao20.setPixmap(QPixmap.fromImage(qimg).scaled(200, 200, Qt.KeepAspectRatio))
        else:
            self.label_imagem_botao20.clear()



    def enviar_log(self):
        # messagebox.showinfo("Info", f"Enviando log para {self.serialnumber.strip()}")
        self.escrever_log = False
        self.item_botao20_selecionado = None

        try:
            data_atual = datetime.now().strftime("%d%m%Y")
            dataehora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            pasta = os.path.join("log_passed", data_atual)

            # horaminutosegundo
            horario = datetime.now().strftime("%H%M%S")
            if not os.path.exists(pasta):
                os.makedirs(pasta, exist_ok=True)
            
            with open(os.path.join(pasta, f"{self.serialnumber.strip()}_{horario}.txt"), 'w') as f:
                f.write(f"Serial: {self.serialnumber.strip()}\nData/Hora: {dataehora}\nSTATUS: {self.set_status}")

            logout_code, logout_message = self.logout_cmc(str(self.serialnumber)).replace('(','').replace("'","").replace(')','').strip().split(',')
            self.hora_teste = None
            
            if str(logout_code.strip()) != '0':
                messagebox.showinfo("Erro", f"{self.serialnumber} FORA DE ROTA\n{logout_message}")               



        except Exception as e:
            messagebox.showinfo("Erro", f"{self.serialnumber} FORA DE ROTA\n{e}")               
            
    def contarpads(self, imagem, area_minima, pads, nome, borda, modo):
        if nome in self.lista_passed:
            return None
        if imagem is None:
            print("Erro ao carregar a imagem.")
            return 0

        h, w = imagem.shape[:2]     
        x_start = int(w * borda)
        y_start = int(h * borda)
        x_end = int(w * (1 - borda))
        y_end = int(h * (1 - borda))

        imagem_cortada = imagem[y_start:y_end, x_start:x_end]

        _, rec_bin = cv2.threshold(imagem_cortada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
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
        
        if len(pads_detectados) == pads:
            return None
        else:
            print("\n", nome, len(pads_detectados), "pads detectados, esperado:", pads, "area:", area_minima, "\n")
            return rec_bin_processado

    def comparar(self, img_boa, img_comparar, borda, area_min, path_boas, nome):
        if nome in self.lista_passed:
            return None

        if img_comparar is None:
            print("Imagem de comparação inválida.")
            return

        try:
            lista_boas = [os.path.join(path_boas, f) for f in os.listdir(path_boas)
                        if f.lower().endswith((".bmp", ".jpg", ".png"))]
        except Exception as e:
            print(f"Erro ao ler imagens do diretório '{path_boas}': {e}")
            return

        for path_img_boa in lista_boas:
            print(path_img_boa)
            img_boa = cv2.imread(path_img_boa)
            if img_boa is None:
                print(f"Falha ao carregar imagem: {path_img_boa}")
                continue

            # Redimensiona
            if img_boa.shape != img_comparar.shape:
                img_comparar_resized = cv2.resize(img_comparar, (img_boa.shape[1], img_boa.shape[0]))
            else:
                img_comparar_resized = img_comparar.copy()

            h, w = img_boa.shape[:2]
            x_start = int(w * borda)
            y_start = int(h * borda)
            x_end = int(w * (1 - borda))
            y_end = int(h * (1 - borda))

            canal_boa = img_boa[y_start:y_end, x_start:x_end, 1]
            canal_ruim = img_comparar_resized[y_start:y_end, x_start:x_end, 1]

            canal_boa = cv2.GaussianBlur(canal_boa, (3, 3), 0)
            canal_ruim = cv2.GaussianBlur(canal_ruim, (3, 3), 0)

            diff = cv2.absdiff(canal_boa, canal_ruim)
            media = np.mean(diff)
            _, diff_thresh = cv2.threshold(diff, media + 10, 255, cv2.THRESH_BINARY)

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            diff_thresh = cv2.morphologyEx(diff_thresh, cv2.MORPH_OPEN, kernel, iterations=2)
            diff_thresh = cv2.dilate(diff_thresh, kernel, iterations=1)

            contornos, _ = cv2.findContours(diff_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            diferencas = 0
            for cnt in contornos:
                area = cv2.contourArea(cnt)
                if area >= area_min:
                    x, y, w_box, h_box = cv2.boundingRect(cnt)
                    aspect_ratio = w_box / float(h_box) if h_box != 0 else 0
                    hull = cv2.convexHull(cnt)
                    solidity = area / cv2.contourArea(hull) if cv2.contourArea(hull) > 0 else 0

                    if 0.2 < aspect_ratio < 5.0 and solidity > 0.3:
                        diferencas += 1
                        break  # já podemos interromper, essa imagem tem falha

            # Se essa imagem "boa" não encontrou diferença, a comparação é compatível
            if diferencas == 0:
                # print(f"Imagem compatível encontrada: {os.path.basename(path_img_boa)}")
                # self.lista_passed.append(nome)
                return None  # Não é falha, uma imagem boa bateu

        # Se chegou aqui, todas tinham diferenças
        # print("Todas as imagens boas apresentaram diferenças.")
        img_resultado = img_comparar_resized.copy()
        for cnt in contornos:
            area = cv2.contourArea(cnt)
            if area >= area_min:
                x, y, w_box, h_box = cv2.boundingRect(cnt)
                aspect_ratio = w_box / float(h_box) if h_box != 0 else 0
                hull = cv2.convexHull(cnt)
                solidity = area / cv2.contourArea(hull) if cv2.contourArea(hull) > 0 else 0

                if 0.2 < aspect_ratio < 5.0 and solidity > 0.3:
                    cnt += np.array([[[x_start, y_start]]])  # volta para coord original
                    cv2.drawContours(img_resultado, [cnt], -1, (0, 0, 255), 2)

        empilhada = np.hstack([img_boa, img_resultado])
        return empilhada
            
    def salvar_crop_como_valido(self, nome, imagem):
        pasta = os.path.join("componentes", nome)
        os.makedirs(pasta, exist_ok=True)
        i = 1
        while True:
            caminho = os.path.join(pasta, f"{nome}_{i}.bmp")
            if not os.path.exists(caminho):
                cv2.imwrite(caminho, imagem)
                print(f"Imagem marcada como válida e salva em: {caminho}")
                break
            i += 1

        
        try:
            class StatusThread3(QThread):
                update_status3 = pyqtSignal(str, str, int)

                def run(self):
                    self.update_status3.emit(nome, "PASS", 100)
                    
            # self.status_thread = StatusThread3()
            # self.status_thread.update_status3.connect(self.status_componente_botao)
            # self.status_thread.start()
            # self.status_thread.wait()
            # self.status_thread.finished.connect(self.status_thread.deleteLater)

            # self.status_componente_botao(nome, value=100, status="PASS")
        except Exception as e:
            print(e)

    def on_pass_click(self, event, x, y, flags, param):

        if event == cv2.EVENT_LBUTTONDOWN:
            nome, crop_realtime_resized, altura = param

            if y >= altura:  # Qualquer clique abaixo da imagem
                # self.status_componente_botao(nome, value=100, status="PASS")

                data_atual = datetime.now().strftime("%d%m%Y")
                pasta = os.path.join("Logs", data_atual)

                os.makedirs(os.path.join(pasta, self.serialnumber.strip()), exist_ok=True)
                # Salvar crop
                cv2.imwrite(os.path.join(pasta, self.serialnumber.strip(), f"{nome}.bmp"), crop_realtime_resized)

                self.lista_passed.append(nome)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

        elif event.key() == Qt.Key_F8:
            self.layout_lista_widget.setVisible(not self.layout_lista_widget.isVisible())

        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.item_botao20_selecionado and self.item_botao20_selecionado != "":
                print(self.item_botao20_selecionado)
                # print(f"Enter pressionado para {self.item_botao20_selecionado}")
                self.on_enter_pass(self.item_botao20_selecionado)
                self.set_status = "RPASS"

        # verifiacao se a tecla pressionada foi delete ( alterado para tecla Insert ou 0 ) 
        elif event.key() == Qt.Key_Insert or event.key() == Qt.Key_0:
            self.set_fail += 1

            print("Delete ou Backspace pressionado")

            if self.lista_botao20.count() > 0 and self.item_botao20_selecionado and self.set_fail == 3:
                self.set_status = "FAIL"
                self.testing = None
                self.labelstatus.setText("FAIL")
                self.labelstatus.setStyleSheet("font-size: 30px; background-color: red; font-weight: bold; color: white;")

                # Salvar todos os crops restantes como FAIL
                data_atual = datetime.now().strftime("%d%m%Y")
                pasta = os.path.join("Logs", data_atual)
                os.makedirs(os.path.join(pasta, f"{self.serialnumber.strip()}_{self.hora_teste}"), exist_ok=True)

                for i in range(self.lista_botao20.count()):
                    item = self.lista_botao20.item(i)
                    nome = item.text()
                    crop = self.crop_componentes.get(nome)
                    if crop is not None:
                        fail_path = os.path.join(pasta, f"{self.serialnumber.strip()}_{self.hora_teste}", f"{nome}_FAIL.bmp")
                        cv2.imwrite(fail_path, crop)
                        self.rpassfolder_img[nome] = {
                            "imagem": fail_path,
                            "status": "FAIL"
                        }

                datahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                upload_dados.upload_dados(self.serialnumber.strip(), self.set_status, datahora, datahora, self.rpassfolder_img)

                self.lista_botao20.clear()
                self.imagens_componentes.clear()
                self.crop_componentes.clear()
                self.rpassfolder_img.clear()

                self.labelserial.setText("Aguardando novo Serial...")


        elif event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            # Verifica se há um item selecionado na lista_botao20
            try:
                self.item_botao20_selecionado = self.lista_botao20.currentItem().text()
                print(f"Tecla pressionada: {event.key()} - Item selecionado: {self.item_botao20_selecionado} para lista {self.lista_botao20.currentItem().text()}")
                
            except Exception as e:
                print(f"Erro ao obter item selecionado: {e}")

    def on_enter_pass(self, nome):
        """
        Evento para aceitar o crop atual como válido ao pressionar ENTER.
        """

        crop = self.crop_componentes.get(nome)
        # self.status_componente_botao(nome, value=100, status="PASS")

        data_atual = datetime.now().strftime("%d%m%Y")
        pasta = os.path.join("Logs", data_atual)

        os.makedirs(os.path.join(pasta, f"{self.serialnumber.strip()}_{self.hora_teste}"), exist_ok=True)
        cv2.imwrite(os.path.join(pasta, f"{self.serialnumber.strip()}_{self.hora_teste}", f"{nome}.bmp"), crop)

        # self.rpassfolder_img[nome] = os.path.join(pasta, f"{self.serialnumber.strip()}_{self.hora_teste}", f"{nome}.bmp")

        self.rpassfolder_img[nome] = {
            "imagem": os.path.join(pasta, f"{self.serialnumber.strip()}_{self.hora_teste}", f"{nome}.bmp"),
            "status": "PASS"
        }

        self.lista_passed.append(nome)
        items = self.lista_botao20.findItems(nome, Qt.MatchExactly)
        if items:
            row = self.lista_botao20.row(items[0])
            self.lista_botao20.takeItem(row)

        # remover dados de {nome} de self.crop_componentes[nome] = crop_realtime_resized e self.imagens_componentes[nome] = imagens_empilhadas
        try:
            del self.crop_componentes[nome]
            del self.imagens_componentes[nome]
        except Exception as e:
            print(f"Erro ao remover crop ou imagem de {nome}: {e}")
                                


    def logout_cmc(self, serial, customer="HUAWEI", level="L06"):
        
        resultado = ','
        url = f"http://10.8.2.50:88/WebServiceTest.asmx"  # URL correta com http://

        headers = {
            "Content-Type": "application/soap+xml;charset=UTF-8",
            "SOAPAction": "http://foxconn/fbrla/webservice/test/SFIS_LOGOUT",
            "X-Customer": f"{customer}",
            "X-Type": f"{level}"
        }

        soap_body = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:test="http://foxconn/fbrla/webservice/test">
            <soap:Header/>
            <soap:Body>
                <test:SFIS_LOGOUT>
                    <test:motherBoardSerialNumber>{serial}</test:motherBoardSerialNumber>
                    <test:operatorId>TEST</test:operatorId>
                    <test:productionLine>TEST</test:productionLine>
                    <test:stationGroup>AVITU</test:stationGroup>
                    <test:hostname>AVITU01</test:hostname>
                    <test:statusCode>0</test:statusCode>
                </test:SFIS_LOGOUT>
            </soap:Body>
            </soap:Envelope>"""

        response = requests.post(url, headers=headers, data=soap_body)
        
        if response.status_code == 200:
            response_dict = xmltodict.parse(response.content)

            result_code = response_dict['soap:Envelope']['soap:Body']['SFIS_LOGOUTResponse']['SFIS_LOGOUTResult']['StatusCode']

            if str(result_code).strip() == '0':
                result_message = 'PASS'
            else:
                result_message = response_dict['soap:Envelope']['soap:Body']['SFIS_LOGOUTResponse']['SFIS_LOGOUTResult']['ErrorMessage']

            resultado = f'{result_code,result_message}'
            # print(resultado)
            return resultado
        else:
            print(f"Erro na requisição: {response.status_code} - {response.text}")
            return '1,Erro na requisição'


    # criar funcao que vai executar ia em threading
    def threading_ia(self):
        while True:
            if self.exibir_resultado:
                self.atualizar_frame()
            time.sleep(0.1)

            
    def threading_frame(self):
        while True:
            try:
                self.iaok = self.anotacoes_IA.copy()
                self.ianok = self.anotacoes_IA_notfound.copy()

                
                raw_image = self.cam.data_stream[0].get_image()
                # horario da imagem:
                if raw_image is None:
                    continue

                # raw_image.defective_pixel_correct()
                # Converte para RGB e reduz a qualidade para algo próximo de JPG (compressão)
                rgb_image = raw_image.convert("RGB")
                del raw_image

                self.frameatual = rgb_image

                rgb_np = rgb_image.get_numpy_array()
                del rgb_image

                
                # Antes de exibir a imagem, desenha as anotações da IA (retângulos e textos)
                annotated_img = rgb_np.copy()
                # Desenha as anotações de componentes detectados (iaok) em verde
                for k, v in self.iaok.items():
                    x1, y1, x2, y2 = v["x1"], v["y1"], v["x2"], v["y2"]
                    conf = v.get("conf", 0)
                    label = v.get("label", "")[:5]
                    cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (0, 255, 0), 12)
                    texto = f"{label} {conf}%"
                    cv2.putText(annotated_img, texto, (x1, max(y1 - 10, 0)),
                                cv2.FONT_HERSHEY_SIMPLEX, 2.4, (0, 255, 0), 8)

                # Desenha as anotações de componentes não encontrados (ianok) em vermelho
                for k, v in self.ianok.items():
                    x1, y1, x2, y2 = v["x1"], v["y1"], v["x2"], v["y2"]
                    label = v.get("label", "")[:5]
                    cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (255, 0, 0), 12)
                    texto = f"{k}"
                    cv2.putText(annotated_img, texto, (x1, max(y1 - 10, 0)),
                                cv2.FONT_HERSHEY_SIMPLEX, 2.4, (255, 0, 0), 8)

                # Desenha as anotações de componentes em anotacoes_notpass em vermelho
                for k, v in self.anotacoes_notpass.items():
                    x1, y1, x2, y2 = v["x1"], v["y1"], v["x2"], v["y2"]
                    label = v.get("label", "")[:5]
                    cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (255, 0, 0), 12)
                    texto = f"{k}"
                    cv2.putText(annotated_img, texto, (x1, max(y1 - 10, 0)),
                                cv2.FONT_HERSHEY_SIMPLEX, 2.4, (255, 0, 0), 8)

                h, w, ch = annotated_img.shape
                bytes_per_line = ch * w
                qimg = QImage(annotated_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.label_imagem.setPixmap(QPixmap.fromImage(qimg).scaled(self.label_imagem.size(), Qt.KeepAspectRatio))

                del rgb_np

            except Exception as e:
                    self.cam.stream_off()
                    time.sleep(1)
                    self.cam.stream_on()
                    # exit()
                    print(f"Erro ao capturar imagem: {e}")
            # print("Aplicando sharpness")


def aplicar_tema_escuro(app):
    dark_palette = QPalette()

    dark_palette.setColor(QPalette.Window, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.WindowText, Qt.black)
    dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Highlight, QColor(100, 100, 255))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(dark_palette)
    app.setStyle("Fusion")

# aprender(model)
# exit()
if __name__ == '__main__':
    app = QApplication(sys.argv)
    janela = Principal()
    janela.showMaximized()
    aplicar_tema_escuro(app)
    sys.exit(app.exec_())
