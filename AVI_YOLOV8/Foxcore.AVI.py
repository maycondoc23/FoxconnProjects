import sys, os
from events import eventos
from PyQt5 import QtWidgets, QtCore, uic, QtGui
from PyQt5.QtGui import QImage, QPixmap
import configparser
import numpy as np
import time, os
import gxipy as gx
from ultralytics import YOLO        
import threading
from io import StringIO
import cv2
import shutil

config = configparser.ConfigParser()

if not os.path.exists('config.ini'):
    with open('config.ini', 'w') as configfile:
        config.add_section('settings')  # Add the 'settings' section
        config.set('settings', 'rememberuser', 'True')
        config.write(configfile)  # Save the changes to the file

config.read('config.ini')
config_check_usuario = config.get('settings', 'rememberuser', fallback=False)
config_check_senha = config.get('settings', 'password', fallback="")
config_set_camera = config.get('settings', 'camera', fallback='1')
classe_selecionada = None
forma_selecionada = None
ultima_execucao = None

class LoginForm(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui/login.ui", self)
        self.setFixedSize(self.size())
        self.encryptar = False

        self.check_lembrar.setChecked(config_check_usuario == 'True')
        if config_check_usuario == 'True':
            self.inputuser.setText(config.get('settings', 'username', fallback=""))
            self.inputpassword.setText(config_check_senha)

        self.pushButton.clicked.connect(self.logar)
        self.pushButton_2.clicked.connect(lambda: self.close())
        self.check_lembrar.stateChanged.connect(self.atualizar_config)
        self.inputpassword.textChanged.connect(lambda: setattr(self, 'encryptar', True))
    

    def atualizar_config(self, state):
        config.set('settings', 'rememberuser', 'True' if state == 2 else 'False') ; config.write(open('config.ini', 'w'))

    def logar(self):    
        login = eventos.login_event(self, self.encryptar)
        
        if login is not None:
            if self.check_lembrar.isChecked():
                config.set('settings', 'username', self.inputuser.text())
                config.set('settings', 'password', login)
                config.set('settings', 'ambiente', self.ambientebox.currentText())
                config.write(open('config.ini', 'w'))
            self.close()
            self.loading = LoadForm()
            self.loading.show()


class LoadForm(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui/load.ui", self)
        self.setFixedSize(self.size())

        self.products = eventos.carregarprodutos(self)
        self.projects = eventos.carregarprojetos(self)
        self.partnumbers = eventos.carregarpartnumbers(self)
        self.programas = eventos.carregarprogramas(self)

        self.projetobox.currentTextChanged.connect(self.atualizarprodutos)
        self.produtobox.currentTextChanged.connect(self.atualizarpartnumbers)
        self.pnbox.currentTextChanged.connect(self.atualizarprogramas)
        self.submitbtn.clicked.connect(self.submitprogram)
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.WindowMinimizeButtonHint |  # mantém minimizar
            QtCore.Qt.WindowCloseButtonHint       # mantém fechar
        )
        
        if config_set_camera == '1':
            self.set_dageng()
        elif config_set_camera == '2':
            self.set_plugplay()

        self.dahengbtn.pressed.connect(lambda: self.set_dageng())
        self.plugplaybtn.pressed.connect(lambda: self.set_plugplay())

    def submitprogram(self):
        self.close()
        self.loading = LoadingWindow()
        self.loading.show()
            
    def atualizarprodutos(self):
        self.produtobox.clear()
        current_project_id = self.projetobox.currentData()
        for produto_id, produto in self.products.items():
            if produto["IdProject"] == current_project_id:
                self.produtobox.addItem(produto["Description"], produto_id)

    def atualizarpartnumbers(self):
        self.pnbox.clear()
        current_product_id = self.produtobox.currentData()
        for partnumber_id, partnumber in self.partnumbers.items():
            if partnumber["IdProduct"] == current_product_id:
                self.pnbox.addItem(partnumber["PartNumber"], partnumber_id)
        self.atualizarprogramas()

    def atualizarprogramas(self):
        self.prgbox.clear()
        current_product_id = self.produtobox.currentData()
        for programa_id, programa in self.programas.items():
            if programa["IdProduct"] == current_product_id:
                self.prgbox.addItem(programa["Description"], programa_id)

    def set_dageng(self):
        config.set('settings', 'camera', '1') ; config.write(open('config.ini', 'w'))
        eventos.set_dagengbtn(self)

    def set_plugplay(self):
        config.set('settings', 'camera', '2') ; config.write(open('config.ini', 'w'))
        eventos.set_plugplaybtn(self)

class LoadingWindow(QtWidgets.QDialog):
    def __init__(self):
        global config
        self.config = config
        super().__init__()
        uic.loadUi("gui/loading.ui", self)
        self.setFixedSize(self.size())
        self.animation = QtCore.QPropertyAnimation(self, b"windowOpacity") ; self.animation.setDuration(1000)  # 2 segundos
        self.setWindowOpacity(0)  # começa invisível
        self.setWindowFlags( QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint )

        self.progressBar.setMinimum(0) ; self.progressBar.setMaximum(0)  
        self.dahengfolder = config.get('settings', 'dagengfolder', fallback=None)
        
    def showEvent(self, event):
        super().showEvent(event)
        QtCore.QTimer.singleShot(5, self.start_fade_in)
        QtCore.QTimer.singleShot(100, self.abrir_dialogo)

    def abrir_dialogo(self):
        if self.dahengfolder is not None:
            self.startlabel.setText("Conclua as configurações da câmera usando o GalaxyView.")
            self.process = QtCore.QProcess(self)
            self.process.finished.connect(lambda: (QtCore.QTimer.singleShot(1000, self.close), self.startlabel.setText("Fechando o programa e seguindo para proxima etapa...")))
            self.process.start(self.dahengfolder, [])
            return
            
        folder, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Selecione o GalaxyView.exe", "", "Executáveis (*.exe)" )
        if folder:
            self.startlabel.setText("Conclua as configurações da câmera usando o GalaxyView.")
            self.dahengfolder = folder
            self.config.set('settings', 'dagengfolder', self.dahengfolder) ; self.config.write(open('config.ini', 'w'))
            self.process = QtCore.QProcess(self)
            self.process.finished.connect(lambda: (QtCore.QTimer.singleShot(1000, self.close), self.startlabel.setText("Fechando o programa e seguindo para proxima etapa...")))
            self.process.start(self.dahengfolder, [])
            return

        else:
            self.startlabel.setText("Nenhuma pasta selecionada. Fechando o programa.")
            QtCore.QTimer.singleShot(2000, self.close)  # fecha de vez só se quiser

    def start_fade_in(self):
        self.animation.stop()
        self.animation.setStartValue(0) 
        self.animation.setEndValue(1)
        self.animation.start()
class SetupWindow(QtWidgets.QMainWindow):
    def __init__(self):
        global config
        super().__init__()
        uic.loadUi("gui/setuparea.ui", self)

        self.labelimg.setScaledContents(False)
        self.pixmap = QtGui.QPixmap(r"C:\ProgramData\Galaxy\userdata\ImagesAndVideos\old\huawei.bmp")
        self.installEventFilter(self)
        self.scale_factor = 1.0
        self.offset = QtCore.QPoint(0, 0)
        self.last_mouse_pos = None
        self.testarcodigo = False

        self.sharpness = config.getfloat('settings', 'sharpness', fallback=0.0)
        self.contrast = config.getint('settings', 'contrast', fallback=0)
        

        self.sharpvalue.setValue(float(self.sharpness))
        self.contrastvalue.setValue(int(self.contrast))

        self.sharpvalue.valueChanged.connect(lambda val: (setattr(self, 'sharpness', val), config.set('settings', 'sharpness', f"{val:.1f}"), config.write(open('config.ini', 'w'))))
        self.contrastvalue.valueChanged.connect(lambda val: (setattr(self, 'contrast', val), config.set('settings', 'contrast', f"{val}"), config.write(open('config.ini', 'w'))))
        
        self.labelimg.installEventFilter(self)
        self.testcodebtn.clicked.connect(self.testcode)

        self.framebtn.clicked.connect(self.daheng_frame)
        # Seleção retangular
        self.selecting = False
        self.selection_start = None
        self.selection_end = None
        self.crop = None  # Pixmap do crop final

        self.labelimg.installEventFilter(self)
        self.center_image()
        
    def testcode(self):
        self.testarcodigo = not self.testarcodigo
        if self.testarcodigo:
            self.testcodebtn.setText("Marque o Serial")        
        else:
            self.testcodebtn.setText("Testar Leitura de Serial")

    def update_pixmap(self):
        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(
                self.pixmap.size() * self.scale_factor,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )

            canvas = QtGui.QPixmap(self.labelimg.size())
            canvas.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(canvas)
            # desenha a imagem no offset atual (coords da label)
            painter.drawPixmap(self.offset, scaled)

            # desenha retângulo de seleção (se existir), em coords da label
            if self.selection_start and self.selection_end:
                rect = QtCore.QRect(self.selection_start, self.selection_end).normalized()
                pen = QtGui.QPen(QtGui.QColor(255, 0, 0))
                pen.setWidth(1)
                pen.setStyle(QtCore.Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(QtGui.QColor(255, 0, 0, 50))
                painter.drawRect(rect)

            painter.end()
            self.labelimg.setPixmap(canvas)

    def center_image(self):
        if self.pixmap.isNull():
            return

        label_size = self.labelimg.size()
        pixmap_size = self.pixmap.size()

        scale_x = label_size.width() / pixmap_size.width()
        scale_y = label_size.height() / pixmap_size.height()
        self.scale_factor = min(scale_x, scale_y)  # zoom inicial para caber na label

        scaled_size = self.pixmap.size() * self.scale_factor
        x = (label_size.width() - scaled_size.width()) // 2
        y = (label_size.height() - scaled_size.height()) // 2
        self.offset = QtCore.QPoint(x, y)

        self.update_pixmap()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.WindowStateChange:
            self.center_image()

        if source == self.labelimg:
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                self.center_image()
                return True

            if event.type() == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.LeftButton:
                pos = event.pos()  # já é em coords da label
                if self.testarcodigo:
                    # seleção
                    self.selecting = True
                    self.selection_start = pos
                    self.selection_end = pos
                else:
                    # pan
                    self.last_mouse_pos = pos
                return True

            if event.type() == QtCore.QEvent.MouseMove:
                pos = event.pos()  # coords da label
                if self.selecting:
                    self.selection_end = pos
                    self.update_pixmap()
                    return True
                if self.last_mouse_pos is not None:
                    delta = pos - self.last_mouse_pos
                    self.offset += delta
                    self.last_mouse_pos = pos
                    self.update_pixmap()
                    return True

            if event.type() == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton:
                if self.selecting:
                    self.selection_end = event.pos()
                    self.selecting = False
                    self.create_crop()
                self.last_mouse_pos = None
                return True

        return super().eventFilter(source, event)


    def wheelEvent(self, event: QtGui.QWheelEvent):
        if self.labelimg.underMouse():
            old_pos = self.labelimg.mapFromGlobal(QtGui.QCursor.pos())
            rel_x = (old_pos.x() - self.offset.x()) / (self.pixmap.width() * self.scale_factor)
            rel_y = (old_pos.y() - self.offset.y()) / (self.pixmap.height() * self.scale_factor)

            if event.angleDelta().y() > 0:
                self.scale_factor *= 1.1
            else:
                self.scale_factor /= 1.1

            self.scale_factor = max(0.1, min(5.0, self.scale_factor))

            new_scaled_w = self.pixmap.width() * self.scale_factor
            new_scaled_h = self.pixmap.height() * self.scale_factor
            self.offset = QtCore.QPoint(
                old_pos.x() - int(rel_x * new_scaled_w),
                old_pos.y() - int(rel_y * new_scaled_h)
            )
            self.update_pixmap()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if self.labelimg.underMouse():
            if event.button() == QtCore.Qt.LeftButton:
                print(self.testarcodigo)
                # Se Shift pressionado → seleção retangular
                if self.testarcodigo:
                    self.selecting = True
                    self.selection_start = event.pos()
                    self.selection_end = event.pos()
                else:
                    # Pan
                    self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.selecting:
            self.selection_end = event.pos()
            self.update_pixmap()
        elif self.last_mouse_pos is not None:
            delta = event.pos() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = event.pos()
            self.update_pixmap()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if self.selecting:
            self.selection_end = event.pos()
            self.selecting = False
            self.create_crop()
        self.last_mouse_pos = None

    def create_crop(self):
        """Cria crop da área selecionada em relação à imagem original"""
        if self.selection_start and self.selection_end and not self.pixmap.isNull():
            # pega coordenadas da seleção na label
            x1 = self.selection_start.x()
            y1 = self.selection_start.y()
            x2 = self.selection_end.x()
            y2 = self.selection_end.y()
            x1, x2 = sorted([x1, x2])
            y1, y2 = sorted([y1, y2])

            offset_x = self.offset.x() ; offset_y = self.offset.y()

            img_x1 = int((x1 - offset_x) / self.scale_factor) ; img_y1 = int((y1 - offset_y) / self.scale_factor) ; img_x2 = int((x2 - offset_x) / self.scale_factor) ; img_y2 = int((y2 - offset_y) / self.scale_factor)
            img_x1 = max(0, min(self.pixmap.width(), img_x1)) ; img_y1 = max(0, min(self.pixmap.height(), img_y1)) ; img_x2 = max(0, min(self.pixmap.width(), img_x2)) ; img_y2 = max(0, min(self.pixmap.height(), img_y2))

            w = img_x2 - img_x1 ; h = img_y2 - img_y1

            if w > 0 and h > 0:
                self.crop = self.pixmap.copy(img_x1, img_y1, w, h)
                # salvar crop
                self.crop.save("testserial.jpg", "JPG")
                time.sleep(0.3)  # espera salvar
                
                serial = eventos.ler_serial()
                if serial is not None:
                    self.readsn = ReadSn(serial, self.crop)
                    self.readsn.exec_()
                else:
                    self.readsn = ReadSn("Não Indetificado", self.crop)
                    self.readsn.exec_()
            
            else:
                print("Seleção inválida")

            # limpa seleção
            self.selection_start = None ; self.selection_end = None ;self.selecting = False ; self.testarcodigo = False
            self.testcodebtn.setText("Testar Leitura de Serial")
            self.update_pixmap()


    def showEvent(self, event):
        super().showEvent(event)
        self.daheng_frame()
        QtCore.QTimer.singleShot(50, self.center_image)

    def daheng_frame(self):
        self.device_manager = gx.DeviceManager()
        self.device_manager.update_device_list()
        if self.device_manager.get_device_number() == 0:
            raise RuntimeError("Nenhuma câmera Daheng conectada.")
        self.cam = self.device_manager.open_device_by_index(1)
        self.cam.stream_on()
                
        raw_image = self.cam.data_stream[0].get_image()
        # horario da imagem:
        if raw_image is None:
            return

        # raw_image.defective_pixel_correct()
        # Converte para RGB e reduz a qualidade para algo próximo de JPG (compressão)
        rgb_image = raw_image.convert("RGB")

        if self.sharpness > 0.0:
            rgb_image.sharpen(self.sharpness)
        if self.contrast > 0:
            rgb_image.contrast(int(self.contrast))  # range -100 a 100

         # libera memória

        del raw_image

        self.frameatual = rgb_image

        rgb_np = rgb_image.get_numpy_array()

        h, w, ch = rgb_np.shape
        bytes_per_line = ch * w
        
        qimg = QImage(rgb_np.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.pixmap = QPixmap.fromImage(qimg)
        # self.piclabel.setPixmap(QtGui.QPixmap(qimg))
        del rgb_image
        self.cam.stream_off()
        self.cam.close_device()
        self.update_pixmap()
        
class ReadSn(QtWidgets.QDialog):
    def __init__(self, serial, crop):
        super().__init__()
        uic.loadUi("gui/readsn.ui", self)
        self.setFixedSize(self.size())
        self.setWindowFlags( QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint )
        self.seriallabel.setText(f"{serial}")
        self.piclabel.setPixmap(QtGui.QPixmap(crop))
        self.piclabel.setScaledContents(True)
        self.closebtn.clicked.connect(lambda: self.close())

        
class Treinamento(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        global config
        self.config = config
        uic.loadUi("gui/treinamento.ui", self)
        self.offset = QtCore.QPoint(0, 0)  # Initialize offset
        self.labelimg.setScaledContents(False)
        self.installEventFilter(self)
        self.scale_factor = 1.0
        self.offset = QtCore.QPoint(0, 0)
        self.last_mouse_pos = None
        # Seleção retangular
        self.selecting = False
        self.selection_start = None
        self.selection_end = None
        self.crop = None  # Pixmap do crop final
        self.testarcodigo = False
        self.labelimg.installEventFilter(self)
        self.annotation_index = 0
        self.anotacoes_list = []
        self.desenhar = False
        self.moving_annotation = None  # Annotation being moved
        self.resizing_annotation = None  # Annotation being resized
        self.resize_start_pos = None  # Starting position of the resize
        self.resize_handle_index = None  # Index of the handle being resized
        self.move_start_pos = None  # Starting position of the move
        self.ultima_classe = None
        self.filename = None
        self.find_opened = False
        self.folder_image = None
        self.pixmap = QtGui.QPixmap(self.folder_image)
        self.folder = r"C:\ProgramData\Galaxy\userdata\ImagesAndVideos\old"
        # path_imagestofind = "C:\ProgramData\Galaxy\userdata\ImagesAndVideos\old"
        self.modelo = None

        self.cameraatual = self.config.get('settings', 'camera', fallback="1")
        if self.cameraatual == '1':
            self.plugplayframebtn.setEnabled(False)
        else:
            self.framebtn.setEnabled(False)
            
        self.anotacao_selecionada = None
        self.folder_trainimage = fr"{self.folder}\images\train"
        self.folder_trainlabel = fr"{self.folder}\labels\train"

        self.listaimagens.addItems([f for f in os.listdir(self.folder_trainimage) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
        self.carregarimgbtn.clicked.connect(self.Dialogoimagem)
        self.carregarmodelobtn.clicked.connect(self.Dialogomodelo)
        self.inspecionarbtn.clicked.connect(self.inspecionar)
        
        self.listaimagens.setCurrentRow(0)
        self.lista_classes = self.load_classes()

        self.listaimagens.currentTextChanged.connect(lambda: (self.carregar_imagem_atual(), self.center_image()))
        self.listaanotacoes.currentTextChanged.connect(lambda: (setattr(self, 'anotacao_selecionada', self.listaanotacoes.currentRow()), self.update_pixmap()))
        self.treinarbtn.clicked.connect(self.carregar_treinamento)
        self.desenharbtn.clicked.connect(self.ToggleDrawMode)
        self.framebtn.clicked.connect(self.daheng_frame)
        self.excluirbtn.clicked.connect(self.excluirimagem)
        self.dahengconfigbtn.clicked.connect(self.abrir_dahengconfig)
        self.avancarbtn.clicked.connect(self.ConfigurarTestplan)
        self.carregar_imagem_atual()
        self.center_image()
        # Ajusta a largura da barra de rolagem do QListWidget
        imagenscrollbar = self.listaimagens.verticalScrollBar()
        anotacoesscrollbar = self.listaanotacoes.verticalScrollBar()
        imagenscrollbar.setStyleSheet("QScrollBar:vertical { width: 4px; border-radius:50px }")
        anotacoesscrollbar.setStyleSheet("QScrollBar:vertical { width: 4px; border-radius:50px }")

        anotacoesscrollbarh = self.listaanotacoes.horizontalScrollBar()
        anotacoesscrollbarh.setStyleSheet("QScrollBar:horizontal { height: 4px; border-radius:50px; background:  #f8c66a}")
    def ConfigurarTestplan(self):
        self.close()
        janela = TestplanConfig()
        janela.exec_()

    def abrir_dahengconfig(self):
        janela = ConfigNovaImagem()
        janela.exec_()


    def excluirimagem(self):
        if self.filename is None:
            return
        reply = QtWidgets.QMessageBox.question(self, 'Confirmação', f"Tem certeza que deseja excluir a imagem {self.filename} e sua anotação?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            img_path = os.path.join(self.folder_trainimage, self.filename)
            label_filename = os.path.splitext(self.filename)[0] + ".txt"
            label_path = os.path.join(self.folder_trainlabel, label_filename)

            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
                if os.path.exists(label_path):
                    os.remove(label_path)
                # Remove da lista
                current_row = self.listaimagens.currentRow()
                self.listaimagens.takeItem(current_row)
                # Carrega próxima imagem
                if self.listaimagens.count() > 0:
                    next_row = min(current_row, self.listaimagens.count() - 1)
                    self.listaimagens.setCurrentRow(next_row)
                else:
                    self.filename = None
                    self.pixmap = QtGui.QPixmap()
                    self.labelimg.clear()
                    self.anotacoes_list.clear()
                    self.listaanotacoes.clear()
                    self.update_pixmap()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao excluir arquivos: {e}")

    def Encontrar_padroes(self, threshold=0.7, max_detections=20, min_dist=10):
        """
        Busca padrões semelhantes à anotação selecionada na imagem atual.
        Usa template matching em grayscale (igual ao on_mouse_up).
        Adiciona as detecções como novas anotações YOLO e salva no arquivo.
        Impede que adicione novas marcações uma acima da outra (sobreposição).
        Sempre salva o crop do template na pasta ImagesToFind.
        Agora salva apenas 1 imagem por classe, com nome igual ao da classe.
        Se forma_selecionada não for None, usa o crop da pasta ImagesToFind.
        """
        global forma_selecionada

        if self.pixmap.isNull() or (self.anotacao_selecionada is None and forma_selecionada is None):
            return []

        # Converte QPixmap para numpy (BGR)
        qimage = self.pixmap.toImage()
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        arr = np.array(ptr).reshape(height, width, 4)  # RGBA
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        images_to_find_dir = os.path.join(self.folder, "ImagesToFind")
        os.makedirs(images_to_find_dir, exist_ok=True)

        # Se forma_selecionada está definida, usa o crop da pasta
        if forma_selecionada is not None:
            crop_path = os.path.join(images_to_find_dir, forma_selecionada)
            if not os.path.exists(crop_path):
                print(f"Arquivo de forma selecionada não encontrado: {crop_path}")
                return []
            template_bgr = cv2.imread(crop_path)
            if template_bgr is None:
                print(f"Erro ao ler o arquivo de forma: {crop_path}")
                return []
            template = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
            # Tenta obter o class_id pelo nome do arquivo (sem extensão)
            class_name = os.path.splitext(forma_selecionada)[0]
            if class_name in self.lista_classes:
                class_id = self.lista_classes.index(class_name)
            else:
                # Se não existir, adiciona à lista de classes
                self.lista_classes.append(class_name)
                with open(os.path.join(self.folder_trainlabel, "classes.txt"), "a") as f:
                    f.write(f"{class_name}\n")
                class_id = self.lista_classes.index(class_name)
        else:
            # Pega anotação selecionada (YOLO format → pixels)
            class_id, x_center, y_center, w_norm, h_norm = self.anotacoes_list[self.anotacao_selecionada]
            img_w, img_h = width, height
            x1 = int((x_center - w_norm / 2) * img_w)
            y1 = int((y_center - h_norm / 2) * img_h)
            x2 = int((x_center + w_norm / 2) * img_w)
            y2 = int((y_center + h_norm / 2) * img_h)
            # Limita bordas
            x1 = max(0, min(x1, img_w - 1))
            x2 = max(0, min(x2, img_w - 1))
            y1 = max(0, min(y1, img_h - 1))
            y2 = max(0, min(y2, img_h - 1))
            if x2 <= x1 or y2 <= y1:
                print("Seleção inválida para template.")
                return []
            template = img_gray[y1:y2, x1:x2]
            if template.size == 0:
                print("Template vazio.")
                return []
            # Salva o crop do template na pasta ImagesToFind
            class_name = self.lista_classes[class_id] if class_id < len(self.lista_classes) else str(class_id)
            crop_filename = f"{class_name}.png"
            crop_path = os.path.join(images_to_find_dir, crop_filename)
            crop_bgr = img_bgr[y1:y2, x1:x2]
            if crop_bgr.size > 0:
                crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
                cv2.imwrite(crop_path, crop_rgb)

        # Matching
        result = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= threshold)

        detections = []
        added_points = []
        count = 0

        # Função para checar sobreposição com anotações existentes
        def overlaps_existing(rx1, ry1, rx2, ry2):
            for ann in self.anotacoes_list:
                _, xc, yc, wn, hn = ann
                ax1 = int((xc - wn / 2) * width)
                ay1 = int((yc - hn / 2) * height)
                ax2 = int((xc + wn / 2) * width)
                ay2 = int((yc + hn / 2) * height)
                # Calcula interseção
                inter_x1 = max(rx1, ax1)
                inter_y1 = max(ry1, ay1)
                inter_x2 = min(rx2, ax2)
                inter_y2 = min(ry2, ay2)
                if inter_x1 < inter_x2 and inter_y1 < inter_y2:
                    return True
            return False

        for pt in zip(*loc[::-1]):
            # Evita detecções muito próximas (duplicadas)
            skip = False
            for added in added_points:
                if np.linalg.norm(np.array(pt) - np.array(added)) < min_dist:
                    skip = True
                    break
            if skip:
                continue

            rx1, ry1 = pt
            rx2, ry2 = pt[0] + template.shape[1], pt[1] + template.shape[0]

            # Impede sobreposição com anotações existentes
            if overlaps_existing(rx1, ry1, rx2, ry2):
                continue

            count += 1
            if count > max_detections:
                print(f"[!] Limite de {max_detections} detecções atingido. Parando a busca.")
                break

            added_points.append(pt)
            detections.append((rx1, ry1, rx2, ry2))

            # Converte para YOLO
            det_x_center = ((rx1 + rx2) / 2) / width
            det_y_center = ((ry1 + ry2) / 2) / height
            det_w_norm = (rx2 - rx1) / width
            det_h_norm = (ry2 - ry1) / height

            # Adiciona anotação
            self.anotacoes_list.append((class_id, det_x_center, det_y_center, det_w_norm, det_h_norm))

        # Salva todas as anotações no arquivo
        annotation_file = os.path.join(self.folder_trainlabel, f"{os.path.splitext(self.filename)[0]}.txt")
        with open(annotation_file, "w") as f:
            for annotation in self.anotacoes_list:
                cid, xc, yc, wn, hn = annotation
                f.write(f"{cid} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}\n")

        # Atualiza interface
        self.CarregarAnotacoes()
        self.update_pixmap()
        print(f"[✔] {len(detections)} novos padrões detectados e salvos.")
        if forma_selecionada is not None:
            print(f"[✔] Usando crop da forma: {crop_path}")
        else:
            print(f"[✔] Crop do template salvo em: {crop_path}")
        return detections

    def centro_box(self, box):
        x1, y1, x2, y2 = map(float, box)
        return ((x1 + x2) / 2, (y1 + y2) / 2)
        
    def inspecionar(self):
        # Convert QPixmap to QImage, then to numpy array, then to BGR for YOLO
        qimage = self.pixmap.toImage().convertToFormat(QtGui.QImage.Format_RGB888)
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        arr = np.array(ptr).reshape(height, width, 3)  # RGB
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

        results = YOLO(self.modelo).predict(img_bgr, conf=0.3, verbose=True)[0]

        boxes = results.boxes.xyxy
        classes = results.boxes.cls.cpu().numpy().astype(int)
        nomes_classes = results.names if hasattr(results, "names") else {}

        img_w, img_h = width, height
        for i, box in enumerate(boxes):
            # printar nome da classe pegando do resultado da ia
            print(classes[i], nomes_classes.get(int(classes[i]), f"class_{int(classes[i])}"))

            x1, y1, x2, y2 = box.cpu().numpy()
            class_id = int(classes[i])

            # Tenta obter o nome da classe pelo dicionário de nomes do modelo
            class_name = nomes_classes.get(class_id, f"class_{class_id}")

            # Se o nome da classe não estiver em self.lista_classes, adiciona e salva no arquivo
            if class_name not in self.lista_classes:
                self.lista_classes.append(class_name)
                with open(os.path.join(self.folder_trainlabel, "classes.txt"), "a") as f:
                    f.write(f"{class_name.upper()}\n")
            # O índice da classe é o índice na lista atualizada
            class_index = self.lista_classes.index(class_name)

            # YOLO format: normalized center x, center y, width, height
            x_center = ((x1 + x2) / 2) / img_w
            y_center = ((y1 + y2) / 2) / img_h
            w_norm = (x2 - x1) / img_w
            h_norm = (y2 - y1) / img_h

            self.anotacoes_list.append((class_index, x_center, y_center, w_norm, h_norm))

        # Save all annotations to file
        annotation_file = os.path.join(self.folder_trainlabel, f"{os.path.splitext(self.filename)[0]}.txt")
        with open(annotation_file, "w") as f:
            for annotation in self.anotacoes_list:
                class_id, x_center, y_center, w_norm, h_norm = annotation
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")

        self.CarregarAnotacoes()
        self.update_pixmap()

    def ToggleDrawMode(self):
        self.desenhar = not self.desenhar
        if self.desenhar:
            self.desenharbtn.setText("Desenhando...")
        else:
            self.desenharbtn.setText("Desenhar")

    def Dialogomodelo(self):
        # Abre diálogo para selecionar um modelo já treinado (.pt)
        self.modelo, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Selecione o modelo já treinado",
            "",
            "Modelos (*.pt)"
        )
        if self.modelo:
            self.inspecionarbtn.setEnabled(True)

    def Dialogoimagem(self):
        # Abre diálogo para selecionar múltiplas imagens com extensões permitidas
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Selecione as imagens",
            self.folder,
            "Imagens (*.jpg *.jpeg *.bmp)"
        )
        if files:
            self.folder_trainimage = fr"{self.folder}\images\train"
            self.folder_trainlabel = fr"{self.folder}\labels\train"
            os.makedirs(self.folder_trainimage, exist_ok=True)
            os.makedirs(self.folder_trainlabel, exist_ok=True)

            # Copia as imagens selecionadas para a pasta de treino
            for src in files:
                dst = os.path.join(self.folder_trainimage, os.path.basename(src))
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)

            self.listaimagens.clear()
            self.listaimagens.addItems([f for f in os.listdir(self.folder_trainimage) if f.lower().endswith(('.jpg', '.jpeg', '.bmp'))])


            self.listaimagens.setCurrentRow(0)
            self.carregar_imagem_atual()
            self.center_image()

    def carregar_treinamento(self):
        with open("dataset.yaml", "w") as f:
            f.write(f"train: {self.folder_trainimage}\n")
            f.write(f"val: {self.folder_trainimage}\n\n")
            f.write(f"nc: {len(self.lista_classes)}\n")
            f.write(f"names: {self.lista_classes}\n")

            
        self.treinando = TreinandoIa()
        self.treinando.exec_()

    def carregar_imagem_atual(self):
        if self.listaimagens.count() == 0:
            return
        self.filename = self.listaimagens.currentItem().text() if self.listaimagens.currentItem() else ""
        self.annotation_index = 0
        self.anotacoes_list.clear()

        print(self.anotacao_selecionada)

        if os.path.exists(os.path.join(self.folder_trainimage, self.filename)):
            self.folder_image = os.path.join(self.folder_trainimage, self.filename)            


        self.CarregarAnotacoes()

        self.pixmap = QtGui.QPixmap(self.folder_image)
        self.update_pixmap()
        # self.center_image()

    def CarregarAnotacoes(self):
        self.listaanotacoes.clear()
        if os.path.exists(os.path.join(self.folder_trainlabel, self.filename.rsplit('.', 1)[0] + '.txt')):
            with open(os.path.join(self.folder_trainlabel, self.filename.rsplit('.', 1)[0] + '.txt'), 'r') as f:
                self.anotacoes_list.clear()
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        class_id = int(parts[0])
                        x_center = float(parts[1])
                        y_center = float(parts[2])
                        w_norm = float(parts[3])
                        h_norm = float(parts[4])
                        self.anotacoes_list.append((class_id, x_center, y_center, w_norm, h_norm))

        if self.anotacoes_list is not None:
            formatted_annotations = [
                (self.lista_classes[annotation[0]],) + tuple(round(coord, 2) for coord in annotation[1:])
                for annotation in self.anotacoes_list
            ]
            for item in formatted_annotations:
                if str(item).strip() == "":
                    continue
                class_name = item[0]
                coordinates = ", ".join(map(str, item[1:]))
                self.listaanotacoes.addItem(f"{class_name} ({coordinates})")
        self.update_pixmap()

    def load_classes(self):
        if not os.path.exists(os.path.join(self.folder_trainlabel, f"classes.txt")):
            with open(os.path.join(self.folder_trainlabel, f"classes.txt"), "w") as f:
                pass
        with open(os.path.join(self.folder_trainlabel, f"classes.txt"), "r") as f:
            return [line.strip() for line in f.readlines()]

    def update_pixmap(self):
        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(
                self.pixmap.size() * self.scale_factor,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )

            canvas = QtGui.QPixmap(self.labelimg.size())
            canvas.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(canvas)
            # desenha a imagem no offset atual (coords da label)
            painter.drawPixmap(self.offset, scaled)

            # desenha retângulo de seleção (se existir), em coords da label
            if self.selection_start and self.selection_end:
                rect = QtCore.QRect(self.selection_start, self.selection_end).normalized()
                pen = QtGui.QPen(QtGui.QColor(255, 0, 0))
                pen.setWidth(1)
                pen.setStyle(QtCore.Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(QtGui.QColor(255, 0, 0, 50))
                painter.drawRect(rect)

            # desenha coordenadas salvas em self.anotacoes_list
            for annotation in self.anotacoes_list:
                class_id, x_center, y_center, w_norm, h_norm = annotation
                img_w, img_h = self.pixmap.width(), self.pixmap.height()

                # calcula coordenadas absolutas
                x1 = int((x_center - w_norm / 2) * img_w * self.scale_factor + self.offset.x())
                y1 = int((y_center - h_norm / 2) * img_h * self.scale_factor + self.offset.y())
                x2 = int((x_center + w_norm / 2) * img_w * self.scale_factor + self.offset.x())
                y2 = int((y_center + h_norm / 2) * img_h * self.scale_factor + self.offset.y())

                rect = QtCore.QRect(QtCore.QPoint(x1, y1), QtCore.QPoint(x2, y2))
                if self.anotacao_selecionada is not None and self.anotacoes_list.index(annotation) == self.anotacao_selecionada:
                    pen = QtGui.QPen(QtGui.QColor("yellow"))
                else:   
                    pen = QtGui.QPen(QtGui.QColor(0, 255, 0))

                pen.setWidth(3)
                painter.setPen(pen)
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawRect(rect)

                # desenha o texto da classe
                painter.setPen(QtGui.QColor(0, 255, 0))
                painter.drawText(rect.topLeft() - QtCore.QPoint(0, 7), f"{self.lista_classes[class_id]}")

                # desenha bolinhas nas extremidades para redimensionamento
                handle_radius = 7
                handle_color = QtGui.QColor(255, 0, 0)
                handle_points = [
                    QtCore.QPoint(x1, y1),  # Top-left
                    QtCore.QPoint(x2, y1),  # Top-right
                    QtCore.QPoint(x1, y2),  # Bottom-left
                    QtCore.QPoint(x2, y2),  # Bottom-right
                ]

                for point in handle_points:
                    painter.setBrush(handle_color)
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.drawEllipse(point, handle_radius, handle_radius)

            painter.end()
            self.labelimg.setPixmap(canvas)

    def delete_annotation(self, index):
        """Exclui uma anotação da lista e do arquivo."""
        if 0 <= index < len(self.anotacoes_list):
            # Remove the annotation from the list
            del self.anotacoes_list[index]

            # Atualiza o arquivo de anotações
            annotation_file = os.path.join(self.folder_trainlabel, f"{os.path.splitext(self.filename)[0]}.txt")
            if os.path.exists(annotation_file):
                with open(annotation_file, "w") as f:
                    for annotation in self.anotacoes_list:
                        class_id, x_center, y_center, w_norm, h_norm = annotation
                        f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")

        self.carregar_imagem_atual()
        # self.update_pixmap()

    def eventFilter(self, source, event):
        global forma_selecionada, ultima_execucao
        if event.type() == QtCore.QEvent.WindowStateChange:
            self.center_image()
            
        if source == self.labelimg:
            
            if event.type() == QtCore.QEvent.MouseButtonDblClick and event.button() == QtCore.Qt.RightButton:
                self.center_image()
                return True

            if event.type() == QtCore.QEvent.MouseButtonDblClick and event.button() == QtCore.Qt.LeftButton:
                pos = event.pos()
                for i, annotation in enumerate(self.anotacoes_list):
                    if self.is_point_in_annotation(pos, annotation):
                        self.rename_annotation(i)
                        return True

            if event.type() == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.LeftButton:
                pos = event.pos()  # já é em coords da label
                if self.desenhar:
                    # seleção
                    self.selecting = True
                    self.selection_start = pos
                    self.selection_end = pos
                else:
                    # check if clicking on an annotation
                    for i, annotation in enumerate(self.anotacoes_list):
                        handle_index = self.is_point_near_handle(pos, annotation)
                        if handle_index is not None:
                            self.resizing_annotation = i
                            self.resize_handle_index = handle_index
                            self.resize_start_pos = pos
                            break
                        elif self.is_point_in_annotation(pos, annotation):
                            self.moving_annotation = i
                            self.move_start_pos = pos
                            self.anotacao_selecionada = i  # Store the last clicked annotation
                            self.update_pixmap()
                            self.listaanotacoes.setCurrentRow(i)
                            break
                    else:
                        # pan
                        self.last_mouse_pos = pos
                return True

            if event.type() == QtCore.QEvent.MouseMove:
                pos = event.pos()  # coords da label
                if self.selecting:
                    self.selection_end = pos
                    self.update_pixmap()
                    return True
                if self.moving_annotation is not None:
                    self.move_annotation(pos)
                    return True
                if self.resizing_annotation is not None:
                    self.resize_annotation(pos)
                    return True
                if self.last_mouse_pos is not None:
                    delta = pos - self.last_mouse_pos
                    self.offset += delta
                    self.last_mouse_pos = pos
                    self.update_pixmap()
                    return True

            if event.type() == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton:
                if self.selecting:
                    self.selection_end = event.pos()
                    self.selecting = False
                    class_id = None
                    classe = None
                    if self.ultima_classe is None:
                        classe = self.lista_classes[0] if self.lista_classes else None
                    else:
                        classe = self.ultima_classe

                    dialog = ClasseCreate(classe, self.lista_classes)

                    if dialog.exec_() == QtWidgets.QDialog.Accepted:
                        global classe_selecionada
                        self.ultima_classe = classe_selecionada
                        if self.ultima_classe is not None:
                            print(f"Classe selecionada: {self.ultima_classe}")
                            
                            
                            if self.ultima_classe not in self.lista_classes:
                                self.lista_classes.append(self.ultima_classe)
                                with open(os.path.join(self.folder_trainlabel, f"classes.txt"), "a") as f:
                                    f.write(f"{self.ultima_classe}\n")

                        self.createannotation(self.lista_classes.index(self.ultima_classe))

                    else:
                        class_id = None

                self.moving_annotation = None
                self.resizing_annotation = None
                self.resize_handle_index = None
                self.last_mouse_pos = None
                return True

        if isinstance(event, QtGui.QKeyEvent):
            if event.key() == QtCore.Qt.Key_Delete:
                print("Delete key pressed")
                if hasattr(self, 'anotacao_selecionada') and self.anotacao_selecionada is not None:
                    self.delete_annotation(self.anotacao_selecionada)
                    self.anotacao_selecionada = None
                    self.update_pixmap()
                return True

            if event.modifiers() & QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_C:
                print("Control+C pressed")
                self.copied_annotation = None
                if hasattr(self, 'anotacao_selecionada') and self.anotacao_selecionada is not None:
                    self.copied_annotation = self.anotacoes_list[self.anotacao_selecionada]
                return True
            if event.modifiers() & QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_D:

                current_time = time.time()
                if not hasattr(self, 'last_detect_time') or (current_time - self.last_detect_time > 1):  # 0.5 seconds threshold
                    # limit = QtWidgets.QInputDialog.getInt(self, "Limite de Detecção", "Limite de detecções:")
                    self.last_detect_time = current_time
                    forma_selecionada = None  
                    print("Control+D pressed")
                    self.Encontrar_padroes()
                return True

            if event.modifiers() & QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_F:
                forma_selecionada = None
                print("Control+F pressed")

                if ultima_execucao is None:
                    formas = ListaFormas(f"{self.folder}\\ImagesToFind")
                    formas.exec_()
                    
                elif ultima_execucao is not None and (time.time() - ultima_execucao) > 1:
                    formas = ListaFormas(f"{self.folder}\\ImagesToFind")
                    formas.exec_()
                
                if forma_selecionada is not None:
                    self.Encontrar_padroes()

                return True

            if event.modifiers() & QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_V:
                current_time = time.time()
                if not hasattr(self, 'last_paste_time') or (current_time - self.last_paste_time > 0.5):  # 0.5 seconds threshold
                    self.last_paste_time = current_time
                    print("Control+V pressed")
                    if hasattr(self, 'copied_annotation') and self.copied_annotation is not None:
                        class_id, x_center, y_center, w_norm, h_norm = self.copied_annotation
                        x_center = min(1.0, x_center + 0.05)
                        y_center = min(1.0, y_center + 0.05)
                        self.anotacoes_list.append((class_id, x_center, y_center, w_norm, h_norm))
                        self.finalize_move_annotation()  # Save the new annotation to the file
                        self.update_pixmap()
                return True

        return super().eventFilter(source, event)

    def rename_annotation(self, index):
        """Open the ClasseCreate dialog to rename the class ID of an annotation."""
        class_id, x_center, y_center, w_norm, h_norm = self.anotacoes_list[index]
        current_class_name = self.lista_classes[class_id] if class_id < len(self.lista_classes) else ""
        dialog = ClasseCreate(current_class_name, self.lista_classes)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            global classe_selecionada
            if classe_selecionada is not None:
                if classe_selecionada not in self.lista_classes:
                    self.lista_classes.append(classe_selecionada)
                    with open(os.path.join(self.folder_trainlabel, "classes.txt"), "a") as f:
                        f.write(f"{str(classe_selecionada).upper()}\n")
                new_class_id = self.lista_classes.index(classe_selecionada)
                self.anotacoes_list[index] = (new_class_id, x_center, y_center, w_norm, h_norm)
                self.finalize_move_annotation()
                self.update_pixmap()

    def is_point_near_handle(self, point, annotation):
        """Check if a point is near one of the resize handles of an annotation."""
        class_id, x_center, y_center, w_norm, h_norm = annotation
        img_w, img_h = self.pixmap.width(), self.pixmap.height()

        x1 = int((x_center - w_norm / 2) * img_w * self.scale_factor + self.offset.x())
        y1 = int((y_center - h_norm / 2) * img_h * self.scale_factor + self.offset.y())
        x2 = int((x_center + w_norm / 2) * img_w * self.scale_factor + self.offset.x())
        y2 = int((y_center + h_norm / 2) * img_h * self.scale_factor + self.offset.y())

        handle_radius = 10
        handle_points = [
            QtCore.QPoint(x1, y1),  # Top-left
            QtCore.QPoint(x2, y1),  # Top-right
            QtCore.QPoint(x1, y2),  # Bottom-left
            QtCore.QPoint(x2, y2),  # Bottom-right
        ]

        for i, handle in enumerate(handle_points):
            if (point - handle).manhattanLength() <= handle_radius:
                return i
        return None

    def is_point_in_annotation(self, point, annotation):
        """Check if a point is inside an annotation rectangle."""
        class_id, x_center, y_center, w_norm, h_norm = annotation
        img_w, img_h = self.pixmap.width(), self.pixmap.height()

        x1 = int((x_center - w_norm / 2) * img_w * self.scale_factor + self.offset.x())
        y1 = int((y_center - h_norm / 2) * img_h * self.scale_factor + self.offset.y())
        x2 = int((x_center + w_norm / 2) * img_w * self.scale_factor + self.offset.x())
        y2 = int((y_center + h_norm / 2) * img_h * self.scale_factor + self.offset.y())

        rect = QtCore.QRect(QtCore.QPoint(x1, y1), QtCore.QPoint(x2, y2))
        return rect.contains(point)

    def is_point_near_edge(self, point, annotation):
        """Check if a point is near the edge of an annotation rectangle."""
        class_id, x_center, y_center, w_norm, h_norm = annotation
        img_w, img_h = self.pixmap.width(), self.pixmap.height()

        x1 = int((x_center - w_norm / 2) * img_w * self.scale_factor + self.offset.x())
        y1 = int((y_center - h_norm / 2) * img_h * self.scale_factor + self.offset.y())
        x2 = int((x_center + w_norm / 2) * img_w * self.scale_factor + self.offset.x())
        y2 = int((y_center + h_norm / 2) * img_h * self.scale_factor + self.offset.y())

        edge_margin = 10  # Margin in pixels to consider as "near edge"
        rect = QtCore.QRect(QtCore.QPoint(x1 - edge_margin, y1 - edge_margin), QtCore.QPoint(x2 + edge_margin, y2 + edge_margin))
        return rect.contains(point) and not QtCore.QRect(QtCore.QPoint(x1 + edge_margin, y1 + edge_margin), QtCore.QPoint(x2 - edge_margin, y2 - edge_margin)).contains(point)

    def move_annotation(self, pos):
        """Move an annotation based on mouse movement."""
        if self.moving_annotation is not None and self.move_start_pos is not None:
            delta = pos - self.move_start_pos
            class_id, x_center, y_center, w_norm, h_norm = self.anotacoes_list[self.moving_annotation]

            img_w, img_h = self.pixmap.width(), self.pixmap.height()
            dx = delta.x() / (img_w * self.scale_factor)
            dy = delta.y() / (img_h * self.scale_factor)

            x_center += dx
            y_center += dy

            # Ensure the annotation stays within bounds
            x_center = max(0, min(1, x_center))
            y_center = max(0, min(1, y_center))

            self.anotacoes_list[self.moving_annotation] = (class_id, x_center, y_center, w_norm, h_norm)
            self.move_start_pos = pos
            self.update_pixmap()
            self.finalize_move_annotation()

    def finalize_move_annotation(self):
        """Save the updated annotation coordinates to the file."""
        annotation_file = os.path.join(self.folder_trainlabel, f"{os.path.splitext(self.filename)[0]}.txt")
        if os.path.exists(annotation_file):
            with open(annotation_file, "w") as f:
                for annotation in self.anotacoes_list:
                    class_id, x_center, y_center, w_norm, h_norm = annotation
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")
            print(f"Updated annotation saved to file: {annotation_file}")
            self.CarregarAnotacoes()

    def resize_annotation(self, pos):
        """Resize an annotation based on mouse movement."""
        if self.resizing_annotation is not None and self.resize_start_pos is not None:
            class_id, x_center, y_center, w_norm, h_norm = self.anotacoes_list[self.resizing_annotation]

            img_w, img_h = self.pixmap.width(), self.pixmap.height()
            delta_x = (pos.x() - self.resize_start_pos.x()) / (img_w * self.scale_factor)
            delta_y = (pos.y() - self.resize_start_pos.y()) / (img_h * self.scale_factor)

            if self.resize_handle_index == 0:  # Top-left
                x_center += delta_x / 2
                y_center += delta_y / 2
                w_norm -= delta_x
                h_norm -= delta_y
            elif self.resize_handle_index == 1:  # Top-right
                x_center += delta_x / 2
                y_center += delta_y / 2
                w_norm += delta_x
                h_norm -= delta_y
            elif self.resize_handle_index == 2:  # Bottom-left
                x_center += delta_x / 2
                y_center += delta_y / 2
                w_norm -= delta_x
                h_norm += delta_y
            elif self.resize_handle_index == 3:  # Bottom-right
                x_center += delta_x / 2
                y_center += delta_y / 2
                w_norm += delta_x
                h_norm += delta_y

            # Ensure the annotation stays within bounds
            w_norm = max(0, min(1, w_norm))
            h_norm = max(0, min(1, h_norm))
            x_center = max(0, min(1, x_center))
            y_center = max(0, min(1, y_center))

            self.anotacoes_list[self.resizing_annotation] = (class_id, x_center, y_center, w_norm, h_norm)
            self.resize_start_pos = pos
            self.finalize_move_annotation()
            self.CarregarAnotacoes()
            # self.carregar_imagem_atual()

    def wheelEvent(self, event: QtGui.QWheelEvent):
        if self.pixmap.isNull():
            return

        if self.labelimg.underMouse():
            if event.modifiers() & QtCore.Qt.ControlModifier:
                # Zoom in/out with Ctrl + Mouse Wheel
                old_pos = self.labelimg.mapFromGlobal(QtGui.QCursor.pos())
                rel_x = (old_pos.x() - self.offset.x()) / (self.pixmap.width() * self.scale_factor)
                rel_y = (old_pos.y() - self.offset.y()) / (self.pixmap.height() * self.scale_factor)

                if event.angleDelta().y() > 0:
                    self.scale_factor *= 1.1
                else:
                    self.scale_factor /= 1.1

                self.scale_factor = max(0.1, min(5.0, self.scale_factor))

                new_scaled_w = self.pixmap.width() * self.scale_factor
                new_scaled_h = self.pixmap.height() * self.scale_factor
                self.offset = QtCore.QPoint(
                    old_pos.x() - int(rel_x * new_scaled_w),
                    old_pos.y() - int(rel_y * new_scaled_h)
                )
                self.update_pixmap()
            else:
                # Move the image up/down or left/right based on Shift key
                delta = event.angleDelta().y()
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    # Move left/right with Shift + Mouse Wheel
                    self.offset.setX(self.offset.x() + (delta // 2))
                else:
                    # Move up/down with Mouse Wheel
                    self.offset.setY(self.offset.y() + (delta // 2))
                self.update_pixmap()

    def createannotation(self, class_id: int = 0):
        """Cria anotação YOLO para a imagem atual e salva em um arquivo único."""
        if self.selection_start and self.selection_end and not self.pixmap.isNull():
            # pega coordenadas da seleção na label
            x1 = self.selection_start.x()
            y1 = self.selection_start.y()
            x2 = self.selection_end.x()
            y2 = self.selection_end.y()
            x1, x2 = sorted([x1, x2])
            y1, y2 = sorted([y1, y2])

            offset_x, offset_y = self.offset.x(), self.offset.y()

            # converter para coordenadas na imagem original
            img_x1 = int((x1 - offset_x) / self.scale_factor)
            img_y1 = int((y1 - offset_y) / self.scale_factor)
            img_x2 = int((x2 - offset_x) / self.scale_factor)
            img_y2 = int((y2 - offset_y) / self.scale_factor)

            # limitar para não ultrapassar bordas
            img_x1 = max(0, min(self.pixmap.width(), img_x1))
            img_y1 = max(0, min(self.pixmap.height(), img_y1))
            img_x2 = max(0, min(self.pixmap.width(), img_x2))
            img_y2 = max(0, min(self.pixmap.height(), img_y2))

            w = img_x2 - img_x1
            h = img_y2 - img_y1

            if w > 0 and h > 0:
                # calcula anotação YOLO (normalizada)
                img_w, img_h = self.pixmap.width(), self.pixmap.height()
                x_center = (img_x1 + w / 2) / img_w
                y_center = (img_y1 + h / 2) / img_h
                w_norm = w / img_w
                h_norm = h / img_h

                # cria ou abre o arquivo de anotações para a imagem atual
                annotation_file = os.path.join(self.folder_trainlabel, f"{os.path.splitext(self.filename)[0]}.txt")
                with open(annotation_file, "a") as f:
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")

                print(f"Anotação adicionada ao arquivo: {annotation_file}")
                # adicionar em anotacoes_list o que foi anotado para ficar exibindo na tela
                self.anotacoes_list.append((class_id, x_center, y_center, w_norm, h_norm))

            # limpa seleção
            self.selection_start = None
            self.selection_end = None
            self.selecting = False
            self.desenhar = False

            self.desenharbtn.setChecked(False)
            self.desenharbtn.setText("Desenhar")
            self.carregar_imagem_atual()
            self.CarregarAnotacoes()

    def center_image(self):
        if self.listaimagens.count() == 0:
            return
        if self.pixmap.isNull():
            return
        label_size = self.labelimg.size()
        pixmap_size = self.pixmap.size()

        scale_x = label_size.width() / pixmap_size.width()
        scale_y = label_size.height() / pixmap_size.height()
        self.scale_factor = min(scale_x, scale_y)  # zoom inicial para caber na label

        scaled_size = self.pixmap.size() * self.scale_factor
        x = (label_size.width() - scaled_size.width()) // 2
        y = (label_size.height() - scaled_size.height()) // 2
        self.offset = QtCore.QPoint(x, y)

        self.update_pixmap()

    def showEvent(self, event):
        QtCore.QTimer.singleShot(300, self.center_image)
        super().showEvent(event)
        self.setWindowState(QtCore.Qt.WindowMaximized)

    def daheng_frame(self):
        self.device_manager = gx.DeviceManager()
        self.device_manager.update_device_list()
        if self.device_manager.get_device_number() == 0:
            raise RuntimeError("Nenhuma câmera Daheng conectada.")
        self.cam = self.device_manager.open_device_by_index(1)
        self.cam.stream_on()
                
        raw_image = self.cam.data_stream[0].get_image()
        # horario da imagem:
        if raw_image is None:
            return

        # raw_image.defective_pixel_correct()
        # Converte para RGB e reduz a qualidade para algo próximo de JPG (compressão)
        rgb_image = raw_image.convert("RGB")

        # if self.sharpness > 0.0:
        #     rgb_image.sharpen(self.sharpness)
        # if self.contrast > 0:
        #     rgb_image.contrast(int(self.contrast))  # range -100 a 100

         # libera memória

        del raw_image

        self.frameatual = rgb_image

        rgb_np = rgb_image.get_numpy_array()

        if not os.path.exists(self.folder_trainimage):
            os.makedirs(self.folder_trainimage, exist_ok=True)

        img_filename = f"captura_{int(time.time())}.jpg"

        img_path = os.path.join(self.folder_trainimage, img_filename)

        cv2.imwrite(img_path, cv2.cvtColor(rgb_np, cv2.COLOR_RGB2BGR))
        
        del rgb_image, rgb_np
        self.cam.stream_off()
        self.cam.close_device()

        self.listaimagens.clear()
        # Ordena as imagens do mais recente para o mais antigo
        imagens = [f for f in os.listdir(self.folder_trainimage) if f.lower().endswith(('.jpg', '.jpeg', '.bmp'))]
        imagens.sort(key=lambda f: os.path.getmtime(os.path.join(self.folder_trainimage, f)), reverse=True)
        self.listaimagens.addItems(imagens)
        self.listaimagens.setCurrentRow(0)


class ClasseCreate(QtWidgets.QDialog):
    def __init__(self, classe, lista_classes):
        super().__init__()

        global classe_selecionada

        self.classe = classe
        uic.loadUi("gui/classecreate.ui", self)
        self.setFixedSize(self.size())
        self.setWindowFlags( QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint )

        if self.classe is not None:
            self.classeinput.setText(self.classe)
        if lista_classes is not None:
            for item in lista_classes:
                if item.strip() == "":
                    continue
                self.classelista.addItem(item)
            self.classelista.itemClicked.connect(self.fill_input_from_list)
            self.classelista.itemDoubleClicked.connect(lambda: self.set_classe_selecionada(self.classeinput.text(), True))

        self.definirbtn.clicked.connect(lambda: self.set_classe_selecionada(self.classeinput.text(), True))
        self.cancelarbtn.clicked.connect(lambda: self.set_classe_selecionada(None, False))
        self.classeinput.returnPressed.connect(lambda: self.set_classe_selecionada(self.classeinput.text(), True))
        
    def showEvent(self, event):
        super().showEvent(event)
        self.classeinput.setText(self.classe)
        self.classeinput.setFocus()

    def set_classe_selecionada(self, value, accept):
        global classe_selecionada
        classe_selecionada = value
        if accept:
            self.accept()
        else:
            self.reject()

    def fill_input_from_list(self):
        global classe_selecionada
        selected_item = self.classelista.currentItem()
        if selected_item:
            self.classeinput.setText(selected_item.text())
            classe_selecionada = selected_item.text()

class TreinandoIa(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        global classe_selecionada

        uic.loadUi("gui/treinandoia.ui", self)
        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.cancelarbtn.clicked.connect(lambda: self.close())
        self.finalizarbtn.clicked.connect(lambda: self.close())
        self.model = YOLO(r'best.pt')

    def showEvent(self, event):
        super().showEvent(event)
        self.run_training()  # Chama o treinamento ao abrir a janela

    def run_training(self):
        class EmittingStream(StringIO):
            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            def write(self, text):
                super().write(text)
                # Quebra o texto em linhas e envia cada uma separadamente
                for line in text.splitlines():
                    if line.strip():
                        self.callback(line)

        def append_output(text):
            # Atualiza o QTextEdit na thread principal
            QtCore.QMetaObject.invokeMethod(
                self.outputtext,
                "append",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, text.rstrip())
            )

        def training_thread():
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = EmittingStream(append_output)
            sys.stderr = EmittingStream(append_output)
            try:
                self.aprender()
                self.finalizarbtn.setEnabled(True)
                self.finalizarbtn.setEnabled(True)
                self.cancelarbtn.setEnabled(False)
                self.progressBar.setMaximum(1)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        threading.Thread(target=training_thread, daemon=True).start()

    def aprender(self):
        destino = r"meu_best.pt"

        # Treinamento do zero: não usar pesos pré-treinados, não congelar camadas
        results = YOLO(model="yolo11n.pt").train(
            data=r'dataset.yaml',
            epochs=100,
            imgsz=1900,
            batch=2,
            lr0=0.0005,
            device='cuda',
            workers=0,
            freeze=0,            # não congela nenhuma camada
            pretrained=False,    # não usar pesos pré-treinados
            project=r"treinos_temp",
            name="treino_serial_zero",
            exist_ok=True)

        best_model_path = results.save_dir / "weights" / "best.pt"

        shutil.copy(best_model_path, destino)

class ListaFormas(QtWidgets.QDialog):
    def __init__(self, path_imagestofind):
        super().__init__()
        global classe_selecionada, forma_selecionada, ultima_execucao
        forma_selecionada = None
        uic.loadUi("gui/listaformas.ui", self)
        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint)

        # Limpa o conteúdo anterior do scrollArea
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)

        for item in os.listdir(path_imagestofind):
            if item.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                btn = QtWidgets.QPushButton(item)
                btn.setIcon(QtGui.QIcon(os.path.join(path_imagestofind, item)))
                btn.textAlign = QtCore.Qt.AlignHCenter
                btn.setMaximumSize(QtCore.QSize(111111, 130))
                btn.setIconSize(QtCore.QSize(120, 120))
                layout.addWidget(btn)
                # Conecta o clique do botão a uma função lambda que captura o nome da forma e seta forma_selecionada
                btn.clicked.connect(lambda checked, name=item: self.set_forma_selecionada(name))

        # Cria um widget para ser o conteúdo do scrollArea
        content_widget = QtWidgets.QWidget()
        content_widget.setLayout(layout)
        self.scrollArea.setWidget(content_widget)

    def set_forma_selecionada(self, value):
        global forma_selecionada
        forma_selecionada = value
        self.accept()

    def accept(self):
        global ultima_execucao
        ultima_execucao = time.time()
        return super().accept()
    def reject(self):
        global ultima_execucao
        ultima_execucao = time.time()
        return super().reject()
    def close(self):
        global ultima_execucao
        ultima_execucao = time.time()
        print("Fechando janela de seleção de formas.")
        return super().close()

class ConfigNovaImagem(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        global config
        uic.loadUi("gui/confignovaimagem.ui", self)
        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint)

        # pegar configurações atuais e setar self.variacaoluz (spinboxint)
        self.variacao = None
        if config.has_option('settings', 'variacaoluz'):
            self.variacao = config.getint('settings', 'variacaoluz')
        else:
            config.set('settings', 'variacaoluz', '10')
            self.variacao = 10

        self.variacaoluz.valueChanged.connect(lambda val: (config.set('settings', 'variacaoluz', str(val)), config.write(open('config.ini', 'w'))))
        self.variacaoluz.setValue(int(self.variacao))

class TestplanConfig(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        global config
        uic.loadUi("gui/testplanconfig.ui", self)
        self.voltarbtn.clicked.connect(self.Voltaraotreinamento)
        self.testes = ["CAPACITOR", "TECLADO", "PLACA", "MOTOR", "MONITOR", "FONTE", "MOUSE", "MONITOR", "FONTE", "MOUSE", "MONITOR", "FONTE", "MOUSE", "MOUSE", "MONITOR", "FONTE", "MOUSE", "MONITOR", "FONTE", "MOUSE", "MOUSE", "MONITOR", "FONTE", "MOUSE", "MONITOR", "FONTE", "MOUSE"]
        self.setWindowState(QtCore.Qt.WindowMaximized)
        # adicionar botoes de maximizar minimizar e fechar
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowCloseButtonHint)
        # Adiciona os botões diretamente ao layout do scrollAreaWidgetContents

        scroll_widget = self.scrollArea.widget()

        if scroll_widget is not None:
            layout_layout = scroll_widget.layout()
            if layout_layout is not None:
                for item in self.testes:
                    btn = QtWidgets.QPushButton(item)
                    btn.setIcon(QtGui.QIcon("gui/logo.png"))
                    btn.setMaximumSize(QtCore.QSize(111111, 130))
                    btn.setIconSize(QtCore.QSize(120, 45))
                    btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                    btn.setStyleSheet("""QPushButton {
                                            border: 1px solid lightgrey ; 
                                            border-radius:10px;
                                            background:#aad9ff;
                                            margin-bottom:4px;
                                            font-size:12px;
                                            text-align: left;
                                            }    
                                        QPushButton:hover {
                                            background:#f8c66a
                                            }
                                        QPushButton:pressed {
                                            background:orange
                                            }""")

                    layout_layout.addWidget(btn)
                    btn.clicked.connect(lambda checked, name=item: print(f"Clicou no botão: {name}"))
        #  alterar largura do scrollbar vertical 

        scrollbararea = self.scrollArea.verticalScrollBar()
        scrollbararea.setStyleSheet("QScrollBar:vertical { width: 4px; border-radius:50px }")

    def Voltaraotreinamento(self):
        self.close()
        janela = Treinamento()
        janela.show()
        
    def showEvent(self, event):
        super().showEvent(event)
        self.setWindowState(QtCore.Qt.WindowMaximized)




if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    janela = Treinamento()
    janela.show()
    sys.exit(app.exec_())
