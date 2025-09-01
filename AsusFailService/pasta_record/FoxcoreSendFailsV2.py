import time
import os
import subprocess
import hashlib
import sys
import threading
import customtkinter as ctk
import pystray
from pystray import MenuItem as item
from PIL import Image
from datetime import datetime
from plyer import notification  
import configparser
import requests
import csv


csv_path = 'error_dict.csv'



config = configparser.ConfigParser()
ini_path = fr'{os.getcwd()}\config.ini'
config.read(ini_path)
diretorio_logs = config.get('PATH','diretorio_logs').strip()
diretorio_record = config.get('PATH','diretorio_record').strip()
diretorio_emsdata = config.get('PATH','diretorio_emsdata').strip()
print(diretorio_logs)
print(diretorio_record)
print(diretorio_emsdata)

file_path = rf'{diretorio_record}\error.DAT'
try:
    os.remove(f'{file_path}')
except:
    pass
class RedirectStdoutToTextbox:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, message):
        # Adiciona a mensagem no widget de texto, mantendo a rolagem para o final
        self.textbox.insert(ctk.END, message)
        self.textbox.yview(ctk.END)

    def flush(self):
        pass

def mostrar_notificacao(titulo, mensagem):
    notification.notify(
        title=titulo,
        message=mensagem,
        app_name='ConsoleFails',
        timeout=5
    )


def carregar_traducoes(csv_path):
    traducoes = {}
    with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Pular o cabeçalho
        for row in reader:
            function_id = row[0]
            function_name = row[1]
            traducoes[function_id] = function_name
    return traducoes

# Função para processar o código de entrada
def processar_codigo(codigo, traducoes):
    codigo_restante = codigo[2:]

    partes = [codigo_restante[i:i+3] for i in range(0, len(codigo_restante), 3)]
    partes_processadas = [parte[:-1] for parte in partes]  # Ignora o último caractere de cada parte

    with open(fr'{diretorio_record}\functionerror.DAT','w') as file:
        for i, partes in enumerate(partes_processadas):
            traducao = traducoes.get(partes[:2], 'Desconhecido')  # Usa os 2 primeiros dígitos para buscar a tradução
            if i < len(partes_processadas) - 1:
                file.write(f'{traducao}__')
            else:
                file.write(f'{traducao}')




def funcao_foxcore(sfis, station, file_content):
    try:
        # URL da API
        url = "http://foxcore.la.foxconn.com:8081/api/FailureLog/SendProjectLog"

        # Abrir e ler o conteúdo do arquivo de falha
        with open(f'{sfis}_FAIL.txt', 'r') as file:
            textofalha = file.read()

        
        params = {
            'IdProject': 18,
            'SerialNumber': str(sfis)
        }
        # print("Corpo da requisição:")
        # print(textofalha)
        print(f'\n\nExecutando envio de dados ao Foxcore:\nSN={sfis}\nFAILS CODES: {file_content}\nStation={station}\nDATE: {log_date} TIME: {log_time}\n')
        try:
            response = requests.post(url, params=params, json=textofalha)
            print("Status da resposta:", response.status_code)
            print('concluído\n')

            mostrar_notificacao(
                titulo='Envio de Dados ao Foxcore',
                mensagem=f'SN={sfis} Station={station}\nFALHA(s):{file_content}\nEnvio concluído com sucesso!'
            )
            os.remove(f'{sfis}_FAIL.txt')
            time.sleep(10)
            try:
                os.remove(f'{file_path}')
                time.sleep(10)
                print('limpando dados para nova captura.')
            except:
                pass
        except Exception as e:
            os.remove(f'{sfis}_FAIL.txt')
            print('FALHA NO ENVIO DOS DADOS, ACIONE O TIME DE ENG TESTE.')
            mostrar_notificacao(
                titulo='Envio de Dados ao Foxcore',
                mensagem=f'FALHA AO ENVIAR DADOS AO FOXCORE.'
            )

            print(e)
            time.sleep(5)
    
    except Exception as e:
        print(e)

def leitura_serial_station():
    try:
        with open (fr'{diretorio_record}\sfis.DAT','r') as file:
            sn = file.read().strip()
            print(sn)
    except:
        command = "wmic baseboard get serialnumber"
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        sn = result.stdout.replace('SerialNumber', '').strip()
        with open('SFIS_WMIC.txt', 'w') as file:
            file.write(sn.strip())
    return sn

def processar_falhas(diretorio_record, diretorio_logs, diretorio_emsdata):
    print(f'INICIANDO MONITORAMENTE DA PASTA {str(diretorio_record).upper()}\n\n')

    try:
        with open(rf'{diretorio_emsdata}\pt.DAT', 'r') as file:
            station = file.read().strip()
        with open('STATION.txt', 'w') as file:
            file.write(station.strip())
    except:   
        print('FALHA NA LEITURA DE ESTAÇÃO, VERIFIQUE SE A CONFIGURACAO DO DIRETORIO EMSDATA ESTA CORRETO NO ARQUIVO CONFIG.INI')
        station = 'FT1-01'
        with open('STATION.txt', 'w') as file:
            file.write(station.strip())

    while True:
        global log_time, log_date
        log_date = datetime.now().strftime("%d/%m/%Y")
        log_time = datetime.now().strftime("%H:%M:%S")
        sfis = leitura_serial_station().strip()
        try:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as file:
                        file_content = file.read().strip()

                    if file_content.strip() == '11':
                        print('placa pass, CODIGO: 11')
                        pass
                    else:
                        traducoes = carregar_traducoes(csv_path)
                        if os.path.exists(rf'{diretorio_record}\functionerror.DAT'):
                            pass
                        else:
                            try:
                                processar_codigo(file_content.strip(), traducoes)
                            except Exception as e:
                                print(e)
                        texto_falhas = f'MB SFIS: {sfis}\nSTATION: {station}\nDATE: {log_date} TIME: {log_time}'
                        with open(rf'{diretorio_record}\functionerror.DAT', 'r') as file:
                            leituradefalhas = file.read().strip()
                            falhas = leituradefalhas.split('__')
                            texto_falhas = f'{texto_falhas}\nFAIL(s) CODE(s): {file_content}\nFAIL(s) NAME(s): {falhas}\n\n'

                            for falha in falhas:
                                if os.path.exists(rf'{diretorio_logs}\{falha}.txt'):
                                    with open(fr'{diretorio_logs}\{falha}.txt', 'r') as file:
                                        texto_falhas = f'{texto_falhas}\n\n--------------- {falha} --------------- \n\n{file.read()}'
                                elif os.path.exists(rf'{diretorio_logs}\{falha}.log'):
                                    with open(fr'{diretorio_logs}\{falha}.log', 'r') as file:
                                        texto_falhas = f'{texto_falhas}\n\n--------------- {falha} --------------- \n\n{file.read()}'
                        # Cálculo do MD5 para verificar alterações
                        file_stat = os.stat(fr'{diretorio_record}\functionerror.DAT')
                        criacao_arquivo = time.ctime(file_stat.st_mtime)
                        print(criacao_arquivo)
                        md5_hash = hashlib.md5(str(criacao_arquivo).encode()).hexdigest()

                        if os.path.exists('md5_control.txt'):
                            with open('md5_control.txt', 'r') as file:
                                md5_anterior = file.read().strip()
                                if md5_anterior == md5_hash:
                                    print(f'MD5 IGUAL AO LOG JÁ ENVIADO, AGUARDANDO RETESTE PARA NOVO ENVIO. ({log_time})')
                                else:
                                    with open(f'{sfis}_FAIL.txt', 'w') as file:
                                        file.write(texto_falhas)
                                    with open('md5_control.txt', 'w') as file:
                                        file.write(md5_hash.strip())
                                    funcao_foxcore(sfis, station, file_content)
                        else:
                            with open(f'{sfis}_FAIL.txt', 'w') as file:
                                file.write(texto_falhas)
                            with open('md5_control.txt', 'w') as file:
                                file.write(md5_hash.strip())
                            funcao_foxcore(sfis, station, file_content)

            except:
                print(f"O arquivo '{file_path}' não foi encontrado.")
                break

            time.sleep(2)
        except:
            pass
def iniciar_processamento(diretorio_record, diretorio_logs, diretorio_emsdata):
    threading.Thread(target=processar_falhas, args=(diretorio_record, diretorio_logs, diretorio_emsdata), daemon=True).start()

def iniciar_interface(diretorio_record, diretorio_logs, diretorio_emsdata):
    root = ctk.CTk()

    # Obter as dimensões da tela (resolução da tela)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    # Calcular a posição de abertura da janela rootlevel para centralizar na tela
    center_x = (screen_width // 2) - (600 // 2)
    center_y = (screen_height // 2) - (400// 2)
    root.geometry(f'{600}x{400}+{center_x}+{center_y}')
    
    root.title("ConsoleFails")
    label = ctk.CTkLabel(root, text="SERVICE CONSOLE")
    label.grid(row=0, column=0, padx=0, pady=0)
    textbox = ctk.CTkTextbox(root, wrap="word", width=550, height=350)
    textbox.grid(row=1, column=0, padx=20, pady=0)
    
    sys.stdout = RedirectStdoutToTextbox(textbox)

    iniciar_processamento(diretorio_record, diretorio_logs, diretorio_emsdata)
    def on_alt_backspace(event):
        print("Alt+Backspace pressionado, fechando a janela!")
        root.destroy() 

    def hide_window():
        root.withdraw()  
        image = Image.open(r"icon/icone.ico")
        menu = (item('Show', show_window), item('Quit', quit_program))
        icon = pystray.Icon("name", image, "ConsoleFails", menu)
        threading.Thread(target=icon.run, daemon=True).start() 
    def show_window(icon, item):
        icon.stop()  # Para o ícone da bandeja
        root.after(0, root.deiconify)  # Restaura a janela

    def quit_program(icon, item):
        icon.stop()
        root.quit()
    root.protocol("WM_DELETE_WINDOW", hide_window) 

    def on_alt_f4(event):
        print("PARA FECHAR O PROGRAMA, PRESSIONE ALT+BACKSPACE OU FINALIZE PELO GERENCIADOR DE TAREFAS")
        return "break"  

    root.bind("<Alt-BackSpace>", on_alt_backspace)
    root.bind("<Alt-F4>", on_alt_f4)
    hide_window()
    root.mainloop()

if __name__ == "__main__":
    iniciar_interface(diretorio_record, diretorio_logs, diretorio_emsdata)
