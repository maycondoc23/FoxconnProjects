import customtkinter as ctk
from tkinter import Listbox, END
import csv
from tkinter import messagebox
from PIL import Image, ImageTk
import warnings
import subprocess
import time
import sys
import os
import tempfile

if getattr(sys, 'frozen', False):
    tempdir = os.path.dirname(sys.executable)
else:
    tempdir = tempfile.gettempdir()

tempfile.tempdir = tempdir

warnings.filterwarnings("ignore", category=UserWarning)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("AcerRepair")
window_width = 680
window_height = 420

# Obter as dimensões da tela (resolução da tela)
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
# Calcular a posição de abertura da janela rootlevel para centralizar na tela
center_x = (screen_width // 2) - (window_width // 2)
center_y = (screen_height // 2) - (window_height // 2)

# Ajusta a posição da janela rootlevel
root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
root.resizable(False, False)

def carregar_codigos_falha(arquivo_csv):
    falhas = {}
    with open(arquivo_csv, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            falhas[row[0]] = row[1]
    return falhas

def mostrar_tabela_csv():
    root2 = ctk.CTk()

    # Lê os dados do arquivo CSV
    dados = []
    with open('tabela_falhas.csv', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            dados.append(row)

    # Cria uma nova janela Toplevel
    top = ctk.CTkToplevel(root2)
    top.title("Tabela de Falhas")
    top.geometry('500x220')

    # Centraliza a janela Toplevel na tela
    window_width = 500
    window_height = 220
    screen_width = top.winfo_screenwidth()
    screen_height = top.winfo_screenheight()
    center_x = (screen_width // 2) - (window_width // 2)
    center_y = (screen_height // 2) - (window_height // 2)
    top.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    # Cria o canvas e o scrollbar
    canvas = ctk.CTkCanvas(top)
    scrollbar = ctk.CTkScrollbar(top, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set, width=600)

    # Cria o frame com rolagem
    scrollable_frame = ctk.CTkFrame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=620)

    # Exibe os dados na tabela
    for i, row in enumerate(dados):
        for j, col in enumerate(row):
            label = ctk.CTkLabel(scrollable_frame, text=col, width=200, height=30)
            label.grid(row=i, column=j, padx=5, pady=5)

    # Atualiza a rolagem
    scrollable_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # Exibe o canvas e o scrollbar
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    # Permite rolar o canvas usando a rolagem do mouse em qualquer parte da janela
    def on_mouse_wheel(event):
        # Para o scroll para cima ou para baixo, dependendo do movimento do mouse
        if event.delta > 0:
            canvas.yview_scroll(-1, "units")
        elif event.delta < 0:
            canvas.yview_scroll(1, "units")
    # Liga o evento de rolagem do mouse à janela Toplevel
    top.bind_all("<MouseWheel>", on_mouse_wheel)
    top.protocol("WM_DELETE_WINDOW", lambda: root2.destroy())  

listbox_selecionado = False

def mostrar_autocomplete(event):
    global listbox_selecionado
    texto_digitado = input_CODE.get().upper()
    listbox_autocomplete.delete(0, END)
    
    if texto_digitado:
        sugeridos = False  
        for codigo, descricao in falhas.items():
            if texto_digitado in codigo.upper() or texto_digitado in descricao.upper():
                listbox_autocomplete.insert(END, f"{codigo} - {descricao}")
                sugeridos = True  
        
        if sugeridos:  # Se houver sugestões, exibe o listbox
            listbox_autocomplete.place(
                x=frame_input_code.winfo_x(),
                y=frame_input_code.winfo_y() + frame_input_code.winfo_height()
            )
            listbox_autocomplete.lift()
            listbox_selecionado = False  # Reset when showing suggestions
        else:  # Se não houver sugestões, esconda o listbox
            listbox_autocomplete.place_forget()
    else:
        listbox_autocomplete.place_forget()

def on_segmented_button_change(value):  # Accept the value argument
    if value == 'NOTEBOOK':
        input_titl_app.configure(text='ACER INPUT REPAIR NB')
        input_stastion_entry.configure(placeholder_text='A51FBT01')
    elif value == 'DESKTOP':
        input_titl_app.configure(text='ACER INPUT REPAIR DT')
        input_stastion_entry.configure(placeholder_text='F101')
    elif value == 'MONITOR':
        input_titl_app.configure(text='ACER INPUT REPAIR MONITOR')
        input_stastion_entry.configure(placeholder_text='FT01')


def tecla_pressionada(event):
    global listbox_selecionado
    if event.keysym == "Down" and not listbox_selecionado:
        listbox_autocomplete.focus_set()
        listbox_autocomplete.selection_set(0)
        listbox_selecionado = True

def inserir_codigo(event):
    selecionado = listbox_autocomplete.get(listbox_autocomplete.curselection())
    codigo = selecionado.split(" - ")[0]  
    input_CODE.delete(0, 'end')
    input_CODE.insert(0, codigo)
    listbox_autocomplete.place_forget()


falhas = carregar_codigos_falha('tabela_falhas.csv')
input_titl_app = ctk.CTkLabel(root, text='ACER INPUT REPAIR NB', width=200, height=40, font=("Arial", 40))
input_titl_app.grid(row=0, column=0, padx=20, pady=9, columnspan=2)

options = ctk.CTkSegmentedButton(root, values=['NOTEBOOK','DESKTOP', 'MONITOR'], width=40, height=20, font=("Arial", 16), command=on_segmented_button_change)
options.grid(row=1, column=0, padx=20, pady=9, columnspan=2)
options.set('NOTEBOOK')

input_title = ctk.CTkButton(root, text='SN LABEL', width=300, height=40, state='disable', font=("Arial", 16))
input_title.grid(row=2, column=0, padx=20, pady=9)

input_label = ctk.CTkEntry(root, placeholder_text='NB00000000000000000000', width=300, height=40, font=("Arial", 16))
input_label.grid(row=3, column=0, padx=20, pady=9)

input_OPID = ctk.CTkButton(root, text='OPID', width=300, height=40, state='disable', font=("Arial", 16))
input_OPID.grid(row=4, column=0, padx=20, pady=9)

input_OPID_entry = ctk.CTkEntry(root, placeholder_text='000000', width=300, height=40, font=("Arial", 16))
input_OPID_entry.grid(row=5, column=0, padx=20, pady=9)


def DONE(status):
    if not root.winfo_exists():  # Verifica se a janela root ainda existe
        return  # Se a janela foi fechada, não execute mais nada

    simulacao = ctk.CTkToplevel(root)
    simulacao.title(str(status))
    simulacao.geometry("250x190")  
    janela_largura = 250
    janela_altura = 200
    x = root.winfo_x() + (root.winfo_width() // 2) - (janela_largura // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (janela_altura // 2)
    simulacao.geometry(f"{janela_largura}x{janela_altura}+{x}+{y}")

    # Carregar e redimensionar o GIF
    gif_image = Image.open(f"{status}.png")
    gif_image = gif_image.resize((150, 150), Image.LANCZOS)  
    gif_image = ImageTk.PhotoImage(gif_image)  

    label_gif = ctk.CTkLabel(simulacao, image=gif_image, text='')
    label_gif.image = gif_image  
    label_gif.pack(pady=20)

    simulacao.after(1600, simulacao.destroy)  # Fecha o Toplevel após 1600 ms

def validar_input(label, tamanho, nome_erro, nome_label):
    """Valida o tamanho de um campo de entrada"""
    valor = label.get().upper().strip()
    if not valor or len(valor) != tamanho:
        messagebox.showerror(f'{nome_label} ERRO', f'O CAMPO {nome_label} NÃO PODE ESTAR VAZIO OU COM TAMANHO DIFERENTE DE {tamanho} CARACTERES.')
        return False, valor
    return True, valor

def validar_estacao(estacao, tipo='NOTEBOOK'):
    """Valida o campo de estação com base no tipo (NOTEBOOK ou DESKTOP)"""
    if tipo == 'NOTEBOOK':
        if len(estacao) != 8 or not estacao.startswith('A51FBT'):
            messagebox.showerror('ESTACAO ERRO', 'O CAMPO ESTACAO PARA NB DEVE CONTER 8 CARACTERES, SENDO OS 6 PRIMEIROS DIGITOS A51FBT.')
            return False
        
    elif tipo == 'MONITOR':
        if len(estacao) != 4 or not estacao.startswith('FT'):
            messagebox.showerror('ESTACAO ERRO', 'O CAMPO ESTACAO PARA MONITOR DEVE CONTER 4 CARACTERES.')
            return False
        else:
            return True, 'FT'
    else:
        if estacao == 'OQC':
            return True, 'OOBA'
        elif len(estacao) != 4 or ('F1' not in estacao and 'F2' not in estacao):
            messagebox.showerror('ESTACAO ERRO', 'O CAMPO ESTACAO DEVE CONTER 4 CARACTERES, SENDO F1 OU F2.')
            return False, ''
        else:
            return True, 'F1' if 'F1' in estacao else 'F2'
    return True, 'FBT'  # Default for notebook

def Pergunta():
    all_good = True

    # Obter dados de entradas
    sn_valid, sn = validar_input(input_label, 22, 'SN', 'SN')
    operador_valid, operador = validar_input(input_OPID_entry, 6, 'OPID', 'OPID')
    falha = input_CODE.get().upper().strip()

    # Validação de falha
    if falha not in falhas:
        messagebox.showerror('CODES ERRO', 'O CODIGO DE FALHA INPUTADO NAO CONSTA NA TABELA DE FALHAS.')
        all_good = False

    # Verificar Estação
    estacao_valid, testename = validar_estacao(input_stastion_entry.get().upper().strip(), options.get())

    if not sn_valid or not operador_valid or not estacao_valid:
        all_good = False

    # Se tudo estiver OK, perguntar confirmação
    if all_good:
        if messagebox.askyesno('CONFIRMAR', f'CONFIRME OS DADOS!\nSN: {sn}\nESTAÇÃO: {input_stastion_entry.get().upper().strip()}\nTEST: {testename}\nOPID: {operador}\nFALHA: {falha}') == True:
            funcao(sn, operador, testename, input_stastion_entry.get().upper().strip(), falha)

def checar_rota(sn, testename_):
    subprocess.run(f'CALL WebServiceApplicationL06.exe SFIS_CHECK_STATUS {sn} S_INPUT_T', capture_output=True, text=True, shell=True)
    with open('WebServiceReturn.bat', 'r') as file:
        retorno = str(file.read().strip().upper()).replace('SET STATUSCODE=1','').replace('SET ERRORMESSAGE=','RETORNO: ')
        print(retorno)

    if f"GO-{testename_}".strip() in retorno:
        print('true')
        return True
    else:
        messagebox.showerror('FAIL', f'PLACA FORA DE ROTA OU ROTA INVALIDA: \n\n{retorno}')
        return False

def funcao(sn, operador, testename, estacao, falha):
    all_good = True
    enviada = True

    # Verificação de SN, OPID e Estação
    sn_valid, sn = validar_input(input_label, 22, 'SN', 'SN')
    operador_valid, operador = validar_input(input_OPID_entry, 6, 'OPID', 'OPID')
    estacao_valid, testename = validar_estacao(estacao, options.get())
    
    if not sn_valid or not operador_valid or not estacao_valid:
        all_good = False

    # Checar falha
    if falha not in falhas:
        messagebox.showerror('CODES ERRO', 'O CODIGO DE FALHA INPUTADO NAO CONSTA NA TABELA DE FALHAS.')
        all_good = False

    # Checar Rota
    if all_good and checar_rota(sn, testename):
        subprocess.run(f'CALL WebServiceApplicationL06.exe SFIS_LOGOUT {sn} {operador} TEST {testename} {estacao} {falha}', capture_output=True, text=True, shell=True)
        time.sleep(0.5)

        with open('WebServiceReturn.bat', 'r') as file:
            retorno = str(file.read().strip().upper())
            retorno = retorno.replace('SET ERRORMESSAGE=','')
            retorno = retorno.replace('SET STATUSCODE=1','').strip()

        if 'NOT FOUND' not in retorno and 'INVALID' not in retorno and 'IS NOT MB OR FG' not in retorno and 'GO-R_F' not in retorno:
            print(retorno)
            status = 'DONE'
            DONE(status)
            root.after(1700, lambda: messagebox.showinfo('ENVIADA', f'PLACA INPUTADA COM SUCESSO\nENVIAR PARA ANALISE TÉCNICA.\n\n{retorno}'))
            input_OPID_entry.configure(text='')
            input_stastion_entry.configure(text='')
            input_OPID_entry.configure(text='')

        else:
            status = 'FAILED'
            DONE(status)
            root.after(1700, lambda: messagebox.showerror('FALHA DE RETORNO', f'VERIFIQUE OS CAMPOS INSERIDOS E TENTE NOVAMENTE.\n\n{retorno}'))
    else:
        print(f'FAILED: {sn} / {falha} / {operador} / {estacao} / {testename}')

def pular_para_entrada(next_entry):
    next_entry.focus_set()

input_title_station = ctk.CTkButton(root, text='STATION', width=300, height=40, state='disable', font=("Arial", 16))
input_title_station.grid(row=2, column=1, padx=20, pady=9)

input_stastion_entry = ctk.CTkEntry(root, placeholder_text='A51FBT01', width=300, height=40, font=("Arial", 16))
input_stastion_entry.grid(row=3, column=1, padx=20, pady=9)

frame_input_code = ctk.CTkFrame(root)
frame_input_code.grid(row=5, column=1, padx=20, pady=9, sticky="ew")

input_failcode = ctk.CTkButton(root, text='FAIL CODE', width=300, height=40, state='disable', font=("Arial", 16))
input_failcode.grid(row=4, column=1, padx=20, pady=9)

input_CODE = ctk.CTkEntry(frame_input_code, placeholder_text='FCT0001', width=270, height=40, font=("Arial", 16))
input_HELP = ctk.CTkButton(frame_input_code, text='?', width=10, height=35, command=mostrar_tabela_csv, font=("Arial", 20), fg_color='grey')
input_CODE.pack(fill='x', side='left')
input_HELP.pack(fill='x', side='right')

listbox_autocomplete = Listbox(root, width=40, height=6, font=("Arial", 11))

listbox_autocomplete.bind("<ButtonRelease-1>", inserir_codigo)
listbox_autocomplete.bind("<Return>", inserir_codigo)

input_CODE.bind("<KeyRelease>", mostrar_autocomplete)
input_CODE.bind("<KeyPress>", tecla_pressionada)

input_CODE.bind("<KeyRelease>", mostrar_autocomplete)

input_repair_but = ctk.CTkButton(root, text='SUBMIT', width=110, height=40,command=Pergunta, font=("Arial", 20))
input_repair_but.grid(row=6, column=0, padx=20, pady=13, columnspan=2)

input_label.bind("<Return>", lambda event: pular_para_entrada(input_OPID_entry))  # Move para o próximo Entry
input_OPID_entry.bind("<Return>", lambda event: pular_para_entrada(input_stastion_entry))
input_stastion_entry.bind("<Return>", lambda event: pular_para_entrada(input_CODE))
input_CODE.bind("<Return>", lambda event: pular_para_entrada(input_HELP))  # Optional: Pular para o botão de ajuda ou outro campo.
# mostrar_tabela_csv()
root.mainloop()
