import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

# Configuração de áudio
CHUNK = 1024  # Tamanho do bloco
FORMAT = pyaudio.paInt16  # Formato de áudio
CHANNELS = 1  # Número de canais
RATE = 44100  # Taxa de amostragem

# Inicializa a captura de áudio
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

# Configuração da interface Tkinter
root = tk.Tk()
root.title("Monitor de Áudio em Tempo Real")

fig, ax = plt.subplots()
x = np.arange(0, 2 * CHUNK, 2)
line, = ax.plot(x, np.random.rand(CHUNK))

ax.set_ylim(-30000, 30000)
ax.set_xlim(0, CHUNK)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

def update_waveform():
    data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
    line.set_ydata(data)
    canvas.draw()
    root.after(10, update_waveform)

# Inicia a atualização da onda de áudio
update_waveform()

# Inicia o loop principal do Tkinter
root.mainloop()

# Finaliza a captura de áudio ao fechar a janela
stream.stop_stream()
stream.close()
p.terminate()
