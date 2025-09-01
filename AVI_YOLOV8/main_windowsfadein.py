import sys
from database import Base, engine, SessionLocal
from models.tables import users
from controllers.auth import login
from events import eventos
from PyQt5 import QtWidgets, QtCore, uic

class MinhaJanela(QtWidgets.QDialog):
    global login
class MinhaJanela(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui/login.ui", self)

        self.pushButton.clicked.connect(self.logar)
        self.pushButton_2.clicked.connect(lambda: self.close())

        # animação na opacidade da janela inteira
        self.animation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(2000)  # 2 segundos
        self.setWindowOpacity(0)  # começa invisível

    def showEvent(self, event):
        super().showEvent(event)
        QtCore.QTimer.singleShot(10, self.start_fade_in)

    def start_fade_in(self):
        self.animation.stop()
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def logar(self):
        eventos.acao_botao(self)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    janela = MinhaJanela()
    janela.show()
    sys.exit(app.exec_())
