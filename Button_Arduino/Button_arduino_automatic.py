import customtkinter as ctk
from PIL import Image, ImageTk
import os 
import threading
import serial
import tkinter as tk



ctk.set_appearance_mode("light")  
ctk.set_default_color_theme("blue")

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



# Cria a janela principal
root = tk.Tk()
root.title("COLOR PUZZLE")
fullscreen = True

root.attributes("-topmost", True)
root.configure(bg="black")  # fundo preto
root.attributes("-fullscreen", fullscreen)

img_up = ImageTk.PhotoImage(Image.open("up.png").resize((50, 50)))
img_down = ImageTk.PhotoImage(Image.open("down.png").resize((50, 50)))
img_left = ImageTk.PhotoImage(Image.open("left.png").resize((50, 50)))
img_right = ImageTk.PhotoImage(Image.open("right.png").resize((50, 50)))

canvas = tk.Canvas(root, bg="black", highlightthickness=0)
# canvas.grid(fill=tk.BOTH, expand=True)

btn_up = tk.Button(root, state="disabled", image=img_up, text="", compound="top")
btn_down = tk.Button(root, state="disabled", image=img_down, text="", compound="bottom")
btn_left = tk.Button(root, state="disabled", image=img_left, text="", compound="left")
btn_right = tk.Button(root, state="disabled", image=img_right, text="", compound="right")
btn_center = tk.Button(root, state="disabled", text="CENTER")

btn_up.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
btn_left.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
btn_center.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
btn_right.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
btn_down.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)




def atualizar_cronometro(segundos):
    if segundos >= 0:
        minutos = segundos // 60
        segundos_restantes = segundos % 60
    else:
        pass





comandoenviado = False
Passed = 0
log = ""
line = ""
def ComunicarArduino():
    global comandoenviado
    global message_buffer
    global passed
    global log
    message_buffer = ''  # Adicionado para evitar o NameError
    while True:
        while arduino.inWaiting() > 0:
            line = arduino.readline().decode("utf-8", errors="ignore").strip()
            print("Recebido:", line)
            log = log + line + '\n'
            if line.upper().strip() == "LEDON_PASS":
                passed += 1
                btn_down.configure(background="green")

            if line.upper().strip() == "LEDOFF_PASS":
                passed += 1
                btn_down.configure(background="green")
                
            if line.upper().strip() == "UP_PASS":
                passed += 1
                btn_up.configure(background="green")
                
            if line.upper().strip() == "DOWN_PASS":
                passed += 1
                btn_up.configure(background="green")

            if line.upper().strip() == "LEFT_PASS":
                passed += 1
                btn_left.configure(background="green")

            if line.upper().strip() == "RIGHT_PASS":
                passed += 1
                btn_right.configure(background="green")

            if line.upper().strip() == "POWER_PASS":
                passed += 1
                btn_center.configure(background="green")

            if passed == 7:
                print("Todos os botoes passaram no teste.")
                with open('PASS.txt', 'w') as f:
                    f.write(f"{log}")
                root.destroy()
                exit()
                break


            message_buffer += line + '\n'
            if "Pronto para comandos" in line and not comandoenviado:
                # threading.Thread(target=atualizar_cronometro(5), daemon=True).start()
                arduino.write(("KEYBOARDTEST\n").encode())
                comandoenviado = True  # Atualiza o flag
                print("enviando comando...")

            if "finalizado." in line:
                with open('FAIL.txt', 'w') as f:
                    f.write(f"{log.strip()}")
                root.destroy()
                exit()
                break

threading.Thread(target=ComunicarArduino, daemon=True).start()

root.mainloop()
