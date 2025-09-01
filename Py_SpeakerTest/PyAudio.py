import customtkinter as ctk
from PIL import Image, ImageTk
import threading
import numpy as np
import os
import wave
import time
import sounddevice as sd
from tkinter import messagebox


if os.path.exists('devicepass.txt'):
    os.remove('devicepass.txt')
if os.path.exists('pass.txt'):
    os.remove('pass.txt')
if os.path.exists('fail.txt'):
    os.remove('fail.txt')


def Check_HeadPhones():
        block = True
        with open('config.ini', 'r') as file:
            for line in file.readlines():
            # print(line)
                if 'block_loopback' in line:
                    config,block = line.split('=')
                    block = block.replace("'","").strip()
                    print(block)
                try:
                    if str(block).upper() == 'NONE':
                        with open('devicepass.txt', 'w') as file:
                            file.write('Loopback_removed')
                        run = False
                except:
                    pass
            devices = sd.query_devices()
        # print(devices)
            if str(block.upper().strip()) in str(devices).upper():
                messagebox.showerror('DeviceCheck','Remova o Cabo de AudioLoopback')
            else:
                with open('devicepass.txt', 'w') as file:
                    file.write('Loopback_removed')

Check_HeadPhones()



if os.path.exists('devicepass.txt'):

    all_pass = True

    # Criar a pasta tmp se não existir
    tmp_dir = 'tmp'
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    # Definir diretório temporário
    os.environ['TMPDIR'] = tmp_dir

    with open('config.ini', 'r') as file:
        lines = file.readlines()

    config_dict = {}
    for line in lines:
        line = line.strip()
        if line and '=' in line:
            key, value = line.split('=', 1)
            config_dict[key.strip()] = value.strip()

    limite_pass = float(config_dict.get('pass', 0.01))
    device_mic = config_dict.get('mic_number_name', '1')
    device_speaker = config_dict.get('speaker_number_name', '3')
    duracao = float(config_dict.get('duration', 5))
    frequencia = int(config_dict.get('frequency', 440))

    # Definir dispositivos de entrada e saída
    try:
        input_device_index = int(device_mic)
    except ValueError:
        input_device_index = device_mic

    try:
        output_device_index = int(device_speaker)
    except ValueError:
        output_device_index = device_speaker

    sd.default.device = (input_device_index, output_device_index)
    sd.default.samplerate = samplerate = 48000
    sd.default.latency = ('low', 'low')
    sd.default.blocksize = 1024

    volume = 100.0

    samples = np.arange(int(duracao * samplerate))
    buffer = volume * np.sin(2 * np.pi * frequencia * samples / samplerate)

    buffer /= np.max(np.abs(buffer))

    # Ajuste de volume
    buffer *= volume / 100.0

    # Função para salvar o áudio gravado
    def save_audio(filename, audio_data, samplerate):
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(samplerate)
            wf.writeframes(audio_data.tobytes())
        print(f"Áudio salvo como: {filename}")

    # Função para calcular o volume RMS do áudio gravado
    def calculate_rms(audio_data):
        audio_data = np.clip(audio_data, -1.0, 1.0)
        rms = np.sqrt(np.mean(np.square(audio_data)))
        return rms

    # Função para tocar o som e gravar ao mesmo tempo
    def play_and_record(buffer, duration):
        time.sleep(0.1)  # Pequena pausa antes da gravação
        recorded_audio = sd.playrec(buffer, samplerate=samplerate, channels=1)
        sd.wait()  # Aguarda a reprodução e gravação completarem
        time.sleep(0.1)  # Pequena pausa após a gravação
        return recorded_audio

    # Função que será executada na thread
    def Run_teste():
        global all_pass
        
        # Teste para o lado esquerdo (mapping = [1]) e direito (mapping = [2])
        for mapping in ([1], [2]):
            lado = 'Speaker L' if 1 in mapping else 'Speaker R'
            print(f"Testando {lado}")

            if lado == 'Speaker L':
                left_label.configure(image=display_image_with_background('Left.png', 'yellow', image_size))
            else:
                right_label.configure(image=display_image_with_background('Right.png', 'yellow', image_size))

            # Ajuste do buffer para tocar em apenas um canal
            if mapping == [1]:
                stereo_buffer = np.column_stack((buffer, np.zeros_like(buffer)))  # Som no canal esquerdo
            else:
                stereo_buffer = np.column_stack((np.zeros_like(buffer), buffer))  # Som no canal direito

            # Sincroniza a execução do som e a gravação
            recorded_audio = play_and_record(stereo_buffer, duracao)

            # Calcula o valor RMS do áudio captado
            if recorded_audio is not None:
                rms_value = calculate_rms(recorded_audio)
                print(f"RMS: {rms_value} / Limite: {limite_pass}")

                if lado == 'Speaker L':
                    center_label_left.configure(text=f'Left Channel: {str(rms_value)}')
                else:
                    center_label_Right.configure(text=f'Right Channel: {str(rms_value)}')

                if rms_value > limite_pass:
                    if lado == 'Speaker L':
                        left_label.configure(image=display_image_with_background('Left.png', 'green', image_size))
                    else:
                        right_label.configure(image=display_image_with_background('Right.png', 'green', image_size))
                    print(f"Pass: O áudio captado está dentro do range aceitável para o {lado}.")
                else:
                    if lado == 'Speaker L':
                        left_label.configure(image=display_image_with_background('Left.png', 'red', image_size))
                    else:
                        right_label.configure(image=display_image_with_background('Right.png', 'red', image_size))
                    print(f"Fail: O áudio captado está fora do range aceitável para o {lado}.")
                    all_pass = False
            else:
                right_label.configure(image=display_image_with_background('Right.png', 'red', image_size))
                left_label.configure(image=display_image_with_background('Left.png', 'red', image_size))
                all_pass = False
                print(f"Erro: Áudio não foi gravado para o {lado}.")

            filename = f"output_audio_mapping_{lado}.wav"
            save_audio(os.path.join(tmp_dir, filename), recorded_audio, samplerate)
            time.sleep(0.5)

        if all_pass:
            with open('Pass.txt', 'w') as file:
                file.write('PASS MIC AND SPEAKER L and R Channel')
        else:
            with open('fail.txt', 'w') as file:
                file.write('FAIL MIC AND SPEAKER L and R Channel')

        # Fechar a aplicação após o teste
        root.destroy()

    # Função para carregar e redimensionar a imagem com um fundo verde
    def display_image_with_background(image_path, bg_color, size):
        # Abrir a imagem
        image = Image.open(image_path).convert("RGBA")
        image = image.resize(size, Image.Resampling.LANCZOS)
        
        # Criar uma nova imagem com o fundo verde
        background = Image.new('RGBA', image.size, bg_color)
        background.paste(image, (0, 0), image)
        
        return ImageTk.PhotoImage(background)

    # Função para carregar e redimensionar a imagem normal
    def display_image(image_path, size):
        image = Image.open(image_path)
        image = image.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image)

    # Criar a janela principal
    ctk.set_appearance_mode("dark")  # Modo claro ou escuro
    ctk.set_default_color_theme("blue")  # Tema de cor padrão

    root = ctk.CTk()
    root.title("Speaker Display")

    # Limitar o tamanho da janela para 400x420 pixels
    root.geometry("400x420")
    root.resizable(False, False)

    # Definir o tamanho das imagens com base no tamanho da janela
    image_size = (200, 300)

    # Carregar as imagens redimensionadas
    left_image = display_image_with_background('Left.png', 'White', image_size)
    right_image = display_image_with_background('Right.png', 'White', image_size)

    # Criar labels para exibir as imagens redimensionadas
    left_label = ctk.CTkLabel(root, image=left_image, text='')
    right_label = ctk.CTkLabel(root, image=right_image, text='')

    center_label = ctk.CTkLabel(root, text=f'Limit RMS PASS: {limite_pass}', font=ctk.CTkFont(size=20, weight='bold'))
    center_label_left = ctk.CTkLabel(root, text=f'Left Channel: Await', font=ctk.CTkFont(size=20, weight='bold'))
    center_label_Right = ctk.CTkLabel(root, text=f'Right Channel: Await', font=ctk.CTkFont(size=20, weight='bold'))

    # Posicionar as imagens na janela
    left_label.grid(row=0, column=0, padx=20, pady=10)
    right_label.grid(row=0, column=1, padx=20, pady=10)

    center_label.grid(row=1, column=0, padx=20, pady=10, columnspan=2)
    center_label_left.grid(row=2, column=0, padx=20, pady=10, columnspan=2)
    center_label_Right.grid(row=3, column=0, padx=20, pady=10, columnspan=2)

    # Iniciar a função de teste em uma thread separada
    threading.Thread(target=Run_teste, daemon=True).start()

    # Iniciar a aplicação
    root.mainloop()
else:
    pass