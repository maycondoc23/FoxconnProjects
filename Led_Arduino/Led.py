import tkinter as tk
from PIL import Image, ImageTk
import random
import threading
import time
import serial
import time
import os
import random


if os.path.exists('PASS.txt'):
    os.remove('PASS.txt')
if os.path.exists('FAIL.txt'):
    os.remove('FAIL.txt')

run = True
log = ""
passed = 0
failed = 0
finalizar = False


with open ('arduinoport.ini', 'r') as f:
    porta = f.read().strip().upper()

try:
    arduino = serial.Serial(
        port=porta,
        baudrate=9600,
    )
except serial.SerialException:
    print("Erro ao conectar ao Arduino. Verifique a porta e tente novamente.")
    exit()


novocomando = True
comando = ""
comandoanterior = ""


janela = tk.Tk()
janela.title("LED KEYBOARD")
janela.geometry("650x400")
janela.configure(background="white")

for i in range(3):
    janela.columnconfigure(i, weight=1)
for i in range(1, 4):  
    janela.rowconfigure(i, weight=1)

label = tk.Label(janela, text="PRESSIONE A TECLA QUE CORRESPONDE\nÀ SEQUÊNCIA DE LEDS ACESOS MOSTRADOS NA IMAGEM",
                 background="lightgrey", font=("Arial", 12, "bold"))
label.grid(row=0, column=0, columnspan=5, pady=10, sticky="nsew")

botoes = [
    tk.Button(janela, text="", state="disabled", background="red"),     # 0
    tk.Button(janela, text="", state="disabled", background="black"),   # 1
    tk.Button(janela, text="", state="disabled", background="red"),     # 2
    tk.Button(janela, text="", state="disabled", background="blue"),    # 3
    tk.Button(janela, text="", state="disabled", background="blue"),    # 4
    tk.Button(janela, text="", state="disabled", background="black"),   # 5
]

for i in range(3):
    botoes[i].grid(row=1, column=i, padx=7, sticky="nsew")
for i in range(3, 6):
    botoes[i].grid(row=2, column=i - 3, padx=7, sticky="nsew")

for i in range(3):
    tk.Label(janela, text=str(i + 1), background="white", font=("Arial", 22, "bold")).grid(row=3, column=i, pady=10)

imagem = Image.open("key.png")
imagem = imagem.resize((200, 240), Image.Resampling.LANCZOS)
imagem_tk = ImageTk.PhotoImage(imagem)
label_imagem = tk.Label(janela, image=imagem_tk, background="white")
label_imagem.grid(row=1, column=4, rowspan=2, sticky="nsew")
label_imagem.image = imagem_tk

status_label = tk.Label(janela, text="", background="white", font=("Arial", 12))
status_label.grid(row=4, column=0, columnspan=5)

blocos = {
    1: [0, 3],  
    2: [4, 1],  
    3: [2, 5],  
}

cores_originais = [btn["background"] for btn in botoes]
bloco_atual = None

# Piscar verde

def piscar_verde(indices):
    for i in indices:
        botoes[i]["background"] = "green"
    janela.update()
    time.sleep(0.2)
    for i, cor in enumerate(cores_originais):
        botoes[i]["background"] = cor
    janela.update()

def piscar_vermelho(indices):
    for i in indices:
        botoes[i]["background"] = "orange"
    janela.update()
    time.sleep(0.2)
    for i, cor in enumerate(cores_originais):
        botoes[i]["background"] = cor
    janela.update()

# Nova rodada

def nova_rodada():
    global run
    global bloco_atual
    global comando
    global comandoanterior

    opcoes = [1, 2, 3]

    if comandoanterior in opcoes:
        opcoes.remove(comandoanterior)

    bloco_atual = random.choice(opcoes)
    comandoanterior = bloco_atual

    if bloco_atual == 1:
        comando = "LED_AV"
    elif bloco_atual == 2:
        comando = "LED_A"
    elif bloco_atual == 3:
        comando = "LED_V"
    run = True

def on_key(event):
    global log, passed, comando, failed
    tecla = event.char
    if tecla in ['1', '2', '3']:
        if int(tecla) == bloco_atual:
            passed += 1
            log = f"{log}\n{comando} : PASS\n"
            threading.Thread(target=piscar_verde, args=(blocos[bloco_atual],), daemon=True).start()
            if passed == 3:
                with open("PASS.txt", "w") as log_file:
                    log_file.write(log.strip())
                time.sleep(0.5)
                janela.destroy()
        else:
            failed += 1
            log = f"{log}\n{comando} : FAIL\n"
            threading.Thread(target=piscar_vermelho, args=(blocos[bloco_atual],), daemon=True).start()
            if failed == 3:
                with open("FAIL.txt", "w") as log_file:
                    log_file.write(log.strip())
                janela.destroy()
        threading.Thread(target=esperar_e_reiniciar, daemon=True).start()

def ComunicarArduino():
    global run
    message_buffer = ''  # Adicionado para evitar o NameError
    global comando
    print("ComunicarArduino iniciado")
    while True:
        if passed == 3:
            break
            
        line = arduino.readline().decode("utf-8").strip()
        print("Recebido:", line)
        message_buffer += line + '\n'
        print(run)

        if "Pronto para comandos" in line:
            arduino.write((f"{comando}\n").encode())
            run = False

        if "Aguardando novo comando..." in line:
            while True:
                if passed == 3:
                    break
                if run:
                    arduino.write((f"{comando}\n").encode())
                    run = False
        if passed == 3:
            break

        time.sleep(0.2)


def esperar_e_reiniciar():
    nova_rodada()

janela.bind("<Key>", on_key)

nova_rodada()

threading.Thread(target=ComunicarArduino, daemon=True).start()

# Loop principal
janela.mainloop()