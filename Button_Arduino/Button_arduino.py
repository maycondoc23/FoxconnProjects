import customtkinter as ctk
from PIL import Image, ImageTk
import os 
import threading
import serial




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
janela = ctk.CTk()
janela.title("Keyboard Test - Arduino")
janela.update_idletasks()
largura = 350
altura = 300
largura_tela = janela.winfo_screenwidth()
altura_tela = janela.winfo_screenheight()
x = (largura_tela // 2) - (largura // 2)
y = (altura_tela // 2) - (altura // 2)
janela.resizable(False, False)

janela.geometry(f"{largura}x{altura}+{x}+{y}")

for i in range(3):
    janela.grid_columnconfigure(i, weight=1)
    janela.grid_rowconfigure(i, weight=1)

img_up = ImageTk.PhotoImage(Image.open("up.png").resize((50, 50)))
img_down = ImageTk.PhotoImage(Image.open("down.png").resize((50, 50)))
img_left = ImageTk.PhotoImage(Image.open("left.png").resize((50, 50)))
img_right = ImageTk.PhotoImage(Image.open("right.png").resize((50, 50)))

cronometro_label = ctk.CTkLabel(janela, text="00:00", text_color="black", fg_color="transparent", font=("Arial", 20, "bold"))
cronometro_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

btn_up = ctk.CTkButton(janela, state="disabled", image=img_up, text="", compound="top", corner_radius=15, fg_color="white", text_color="black")
btn_down = ctk.CTkButton(janela, state="disabled", image=img_down, text="", compound="bottom", corner_radius=15, fg_color="white", text_color="white")
btn_left = ctk.CTkButton(janela, state="disabled", image=img_left, text="", compound="left", corner_radius=15, fg_color="white", text_color="black")
btn_right = ctk.CTkButton(janela, state="disabled", image=img_right, text="", compound="right", corner_radius=15, fg_color="white", text_color="white")
btn_center = ctk.CTkButton(janela, state="disabled", text="CENTER", corner_radius=15, fg_color="white", text_color="white")


btn_up.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
btn_left.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
btn_center.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
btn_right.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
btn_down.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
def atualizar_cronometro(segundos):
    if segundos >= 0:
        minutos = segundos // 60
        segundos_restantes = segundos % 60
        cronometro_label.configure(text=f"{minutos:02}:{segundos_restantes:02}")
        janela.after(1000, atualizar_cronometro, segundos - 1)
    else:
        cronometro_label.destroy()  # ou use `.configure(text="")` para apenas apagar o número





comandoenviado = False
Passed = 0
log = ""
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
            if line.upper().strip() == "DOWN=PASS":
                passed += 1
                btn_down.configure(fg_color="green", text_color="black")
                
            if line.upper().strip() == "UP=PASS":
                passed += 1
                btn_up.configure(fg_color="green", text_color="black")
            if line.upper().strip() == "LEFT=PASS":
                passed += 1
                btn_left.configure(fg_color="green", text_color="black")
            if line.upper().strip() == "RIGHT=PASS":
                passed += 1
                btn_right.configure(fg_color="green", text_color="black")
            if line.upper().strip() == "PWR=PASS":
                passed += 1
                btn_center.configure(fg_color="green", text_color="black")

            if passed == 5:
                print("Todos os botoes passaram no teste.")
                with open('PASS.txt', 'w') as f:
                    f.write(f"{log}")
                janela.destroy()
                exit()
                break


            message_buffer += line + '\n'
            if "Pronto para comandos" in line and not comandoenviado:
                threading.Thread(target=atualizar_cronometro(5), daemon=True).start()
                arduino.write(("BUTTON\n").encode())
                comandoenviado = True  # Atualiza o flag
                print("enviando comando...")

            if "Teste finalizado. Aguardando novo comando..." in line:
                with open('FAIL.txt', 'w') as f:
                    f.write(f"{log.strip()}")
                janela.destroy()
                exit()
                break
threading.Thread(target=ComunicarArduino, daemon=True).start()


janela.mainloop()
