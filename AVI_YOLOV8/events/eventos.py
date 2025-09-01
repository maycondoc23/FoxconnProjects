import subprocess
from database import SessionLocal
from controllers.auth import login, loadprojects, loadproducts, loadpartnumber, loadprograms
import subprocess
import cv2
import numpy as np
from pylibdmtx.pylibdmtx import decode
from pyzbar.pyzbar import decode as decode_pyzbar

def login_event(self, encryptar):
    usuario = self.inputuser.text()
    key = self.inputpassword.text()

    if encryptar:
        key = subprocess.run(["encrypt/encrypt.exe", key], capture_output=True, text=True).stdout.strip()

    db = SessionLocal()
    usuario = login(db, usuario, key)
    if usuario:
        return key
    else:
        return None

def carregarprojetos(self):
    dicionario = {}
    db = SessionLocal()
    projetos = loadprojects(db)
    for project in projetos:
        self.projetobox.addItem(project.Description, project.id)
        dicionario[project.id] = {"Id": project.id, "Description": project.Description}
    return dicionario

def carregarprodutos(self):
    dicionario = {}
    db = SessionLocal()
    produtos = loadproducts(db)
    for produto in produtos:
        self.produtobox.addItem(produto.Description, produto.id)
        dicionario[produto.id] = {"Id": produto.id, "IdProject": produto.IdProject, "Description": produto.Description}
    return dicionario
    

def carregarpartnumbers(self):
    dicionario = {}
    db = SessionLocal()
    partnumbers = loadpartnumber(db)
    for partnumber in partnumbers:
        dicionario[partnumber.id] = {"Id": partnumber.id, "PartNumber": partnumber.PartNumber, "IdProduct": partnumber.IdProduct}
    return dicionario

def carregarprogramas(self):
    dicionario = {}
    db = SessionLocal()
    programas = loadprograms(db)
    for programa in programas:
        dicionario[programa.id] = {"Id": programa.id, "IdProject": programa.IdProject,
                                    "IdProduct": programa.IdProduct, "Description": programa.Description}
    return dicionario



def set_dagengbtn(self):
    self.dahengbtn.setStyleSheet("""QPushButton {
                                        border-radius: 8px;
                                        padding: 5px 10px;
                                        background-color: lightgreen;
                                        border: 0.6px solid lightgrey
                                    }
                                    QPushButton:pressed {
                                        background-color: orange;
                                    }""")
    self.plugplaybtn.setStyleSheet("""QPushButton {
                                        border-radius: 8px;
                                        padding: 5px 10px;
                                        background-color: lightgrey;
                                        border: 0.6px solid lightgrey
                                    }
                                    QPushButton:pressed {
                                        background-color: orange;
                                    }""")

def set_plugplaybtn(self):
    self.plugplaybtn.setStyleSheet("""QPushButton {
                                        border-radius: 8px;
                                        padding: 5px 10px;
                                        background-color: lightgreen;
                                        border: 0.6px solid lightgrey
                                    }
                                    QPushButton:pressed {
                                        background-color: orange;
                                    }""")
    self.dahengbtn.setStyleSheet("""QPushButton {
                                        border-radius: 8px;
                                        padding: 5px 10px;
                                        background-color: lightgrey;
                                        border: 0.6px solid lightgrey
                                    }
                                    QPushButton:pressed {
                                        background-color: orange;
                                    }""")
    


def ler_serial(image_crop="testserial.jpg"):

    if isinstance(image_crop, str):
        image_crop = cv2.imread(image_crop)
        if image_crop is None:
            print(f"Error: Unable to load image from path '{image_crop}'")
            return None

    rec_zoom = cv2.resize(image_crop, None, fx=4.0, fy=4.0, interpolation=cv2.INTER_CUBIC)
    rec_gray = cv2.cvtColor(rec_zoom, cv2.COLOR_BGR2GRAY)
    _, rec_bin = cv2.threshold(rec_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # salvar foto
    cv2.imwrite("rec_bin.png", rec_bin)
    # cv2.imshow("image_crop.png", image_crop)
    cv2.imwrite("zoom.png", rec_zoom)
    decoded_objects = decode(rec_bin, timeout=500, max_count=4)
    
    for obj in decoded_objects:
        valor = obj.data.decode("utf-8")
        print(f"Datamatrix NORMAL: {valor}")
        if valor.startswith("[)>"):
            valor = valor[8:]
            valor = valor[:12]
            
        return valor  # Retorna o primeiro valor lido com sucesso

    print("lendo sem bin")
    decoded_objects = decode(rec_zoom, timeout=500, max_count=4)
    
    for obj in decoded_objects:
        valor = obj.data.decode("utf-8")
        print(f"Datamatrix NORMAL: {valor}")
        if valor.startswith("[)>"):
            valor = valor[8:]
            valor = valor[:12]
            
        return valor  # Retorna o primeiro valor lido com sucesso

    decoded_objects = decode_pyzbar(rec_bin)
    if decoded_objects:
        for obj in decoded_objects:
            valor = obj.data.decode("utf-8")
            print(f"[{valor}")

    print("Falha de leitura do serial")
    return None  # ou None, dependendo do que preferir tratar fora
