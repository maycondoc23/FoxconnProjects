import tkinter as tk
import random
import os

erros_maximos = 3
acertos_seguidos = 0
erros = 0
finalizacao_ativa = False
segunda_etapa = False  # Controle da etapa da bolinha branca

if os.path.exists("pass.txt"):
    os.remove("pass.txt")
if os.path.exists("fail.txt"):
    os.remove("fail.txt")

cores_disponiveis = ["blue", "red", "green"]
cor_para_tecla = {
    "red": "r",
    "green": "g",
    "blue": "b"
}

fila_cores = []

def embaralhar_fila():
    global fila_cores
    fila_cores = list(cores_disponiveis)
    random.shuffle(fila_cores)

cor_certa = None

def desenhar_cor_fundo(cor_nome):
    canvas.delete("all")
    width = canvas.winfo_width()
    height = canvas.winfo_height()
    canvas.create_rectangle(0, 0, width, height, fill=cor_nome, outline="")

def iniciar_novo_desafio():
    global cor_certa, fila_cores

    if not fila_cores:
        embaralhar_fila()

    cor_certa = fila_cores.pop(0)
    print(cor_certa)
    desenhar_cor_fundo(cor_certa)

    resultado_label.config(
        text="PRESSIONE R PARA VERMELHO, G PARA VERDE, B PARA AZUL\nOBSERVE A TELA E VERIFIQUE SE NÃO HÁ LISTRAS OU FALHAS",
    )

def on_key(event):
    global acertos_seguidos, erros, fila_cores

    if finalizacao_ativa:
        return

    tecla_pressionada = event.char.lower()
    tecla_certa = cor_para_tecla.get(cor_certa, "")

    if tecla_pressionada == tecla_certa:
        acertos_seguidos += 1
        if acertos_seguidos >= 3:
            mostrar_ponto_final_branco()
        else:
            iniciar_novo_desafio()
    else:
        erros += 1
        acertos_seguidos = 0
        fila_cores.clear()
        if erros >= erros_maximos:
            with open("fail.txt", "w") as f:
                f.write("FAIL")
            root.quit()
        else:
            iniciar_novo_desafio()

def mostrar_ponto_final_branco():
    global finalizacao_ativa, segunda_etapa
    finalizacao_ativa = True
    segunda_etapa = False  # Etapa 1: fundo branco, bolinha vermelha

    canvas.delete("all")
    canvas.configure(bg="white")

    width = canvas.winfo_width()
    height = canvas.winfo_height()
    raio = 12

    x = random.randint(raio, width - raio)
    y = random.randint(raio, height - raio)

    canvas.create_oval(x - raio, y - raio, x + raio, y + raio, fill="red", outline="black", tags="ponto_final")
    resultado_label.config(text="Clique no ponto vermelho para continuar.")
    canvas.tag_bind("ponto_final", "<Button-1>", clique_final)

def mostrar_ponto_final_preto():
    global segunda_etapa
    segunda_etapa = True  # Etapa 2: fundo preto, bolinha branca

    canvas.delete("all")
    canvas.configure(bg="black")

    width = canvas.winfo_width()
    height = canvas.winfo_height()
    raio = 12

    x = random.randint(raio, width - raio)
    y = random.randint(raio, height - raio)

    canvas.create_oval(x - raio, y - raio, x + raio, y + raio, fill="white", outline="gray", tags="ponto_final")
    resultado_label.config(text="Clique no ponto branco para finalizar.")
    canvas.tag_bind("ponto_final", "<Button-1>", clique_final)

def clique_final(event):
    if not segunda_etapa:
        mostrar_ponto_final_preto()
    else:
        with open("pass.txt", "w") as f:
            f.write("PASS")
        root.quit()

def toggle_fullscreen(event=None):
    global fullscreen
    fullscreen = not fullscreen
    root.attributes("-fullscreen", fullscreen)

# Interface
root = tk.Tk()
root.title("COLOR TEST")
fullscreen = True
root.attributes("-topmost", True)
root.configure(bg="yellow")
root.attributes("-fullscreen", fullscreen)

canvas = tk.Canvas(root, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)

resultado_label = tk.Label(root, text="", font=("Arial", 20, "bold"), fg="black", bg="yellow")
resultado_label.pack(pady=10)

embaralhar_fila()
root.bind("<Key>", on_key)
root.bind("<F11>", toggle_fullscreen)
    
root.after(100, iniciar_novo_desafio)
root.mainloop()
