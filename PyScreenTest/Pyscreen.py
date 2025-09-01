import tkinter as tk
import random
import os
pixel_size = 20


with open("count.ini", "r") as file:
    count = file.read().strip()

acertos_necessarios = int(count)
erros_maximos = int(count)

acertos = 0
erros = 0

if os.path.exists("pass.txt"):
    os.remove("pass.txt")
if os.path.exists("fail.txt"):
    os.remove("fail.txt")

# Dicionário simples: cor hex → nome
cores_disponiveis = {
    "#FF0000": "Vermelho",
    "#0000FF": "Azul",
    "#008000": "Verde",
    "#FFFFFF": "Branco"
}

# Variável para controlar a cor correta do momento
cor_certa = None

def gerar_quadrantes():
    """Distribui as 4 cores nos quadrantes aleatoriamente"""
    cor_lista = list(cores_disponiveis.keys())
    random.shuffle(cor_lista)
    return {
        "top_left": cor_lista[0],
        "top_right": cor_lista[1],
        "bottom_left": cor_lista[2],
        "bottom_right": cor_lista[3]
    }

def desenhar_quadrantes(quadrantes):
    canvas.delete("all")
    width = canvas.winfo_width()
    height = canvas.winfo_height()

    for y in range(0, height, pixel_size):
        for x in range(0, width, pixel_size):
            if x < width / 2 and y < height / 2:
                cor_hex = quadrantes["top_left"]
            elif x >= width / 2 and y < height / 2:
                cor_hex = quadrantes["top_right"]
            elif x < width / 2 and y >= height / 2:
                cor_hex = quadrantes["bottom_left"]
            else:
                cor_hex = quadrantes["bottom_right"]

            canvas.create_rectangle(x, y, x + pixel_size, y + pixel_size, fill=cor_hex, outline="")

def iniciar_novo_teste():
    global cor_certa, quadrantes
    quadrantes = gerar_quadrantes()
    desenhar_quadrantes(quadrantes)

    cor_certa = random.choice(list(cores_disponiveis.items()))
    resultado_label.config(text=f"CLIQUE NA COR {cor_certa[1].upper()} \nE VERIFIQUE SE NÃO HÁ DISTORÇÕES NA IMAGEM OU LISTRAS NA TELA",)

def on_click(event):
    global acertos, erros
    x, y = event.x, event.y
    item = canvas.find_closest(x, y)
    cor_clicada = canvas.itemcget(item, "fill")

    if cor_clicada == cor_certa[0]:
        acertos += 1
        if acertos >= acertos_necessarios:
            with open("pass.txt", "w") as f:
                f.write("PASS")
            root.quit()
        else:
            iniciar_novo_teste()
    else:
        erros += 1
        if erros >= erros_maximos:
            with open("fail.txt", "w") as f:
                f.write("FAIL")
            root.quit()
        else:
            iniciar_novo_teste()

def toggle_fullscreen(event=None):
    global fullscreen
    fullscreen = not fullscreen
    root.attributes("-fullscreen", fullscreen)

# Interface


root = tk.Tk()
root.title("COLOR PUZZLE")
fullscreen = True

# mudar para topmost
root.attributes("-topmost", True)
# mudar fundo do root para amarelo

root.configure(bg="yellow")
root.attributes("-fullscreen", fullscreen)

canvas = tk.Canvas(root, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)

resultado_label = tk.Label(root, text="", font=("Arial", 20, "bold"), fg="black", bg="yellow")
resultado_label.pack(pady=10)

canvas.bind("<Button-1>", on_click)
canvas.bind("<Configure>", lambda event: iniciar_novo_teste())

iniciar_novo_teste()
root.mainloop()
