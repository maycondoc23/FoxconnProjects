import sounddevice as sd
import numpy as np
import math
import os
import re
import threading
import time
import wave


# Criar a pasta tmp se não existir
tmp_dir = 'tmp'
if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)

# Definir a variável de ambiente para o diretório temporário
os.environ['TMPDIR'] = tmp_dir

# Abrir e ler o arquivo de configuração
with open('config.ini', 'r') as file:
    lines = file.readlines()

# Dicionário para armazenar as configurações
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

volume = 100.0

samples = np.arange(int(duracao * samplerate))
buffer = volume * np.sin(2 * np.pi * frequencia * samples / samplerate)

buffer /= np.max(np.abs(buffer))

# Ajuste de volume
buffer *= volume / 100.0

# Variável global para armazenar o áudio gravado
recorded_audio = None
def save_audio(filename, audio_data, samplerate):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(samplerate)
        wf.writeframes(audio_data.tobytes())
    print(f"Áudio salvo como: {filename}")

# Função para capturar o áudio do microfone
def record_audio(duration):
    global recorded_audio
    print("Gravando áudio...")
    recorded_audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
    sd.wait()

# Função para tocar o som
# def play_sound(mapping):
#     sd.play(buffer, samplerate=samplerate, mapping=mapping, device=output_device_index)

# Função para calcular o volume RMS do áudio gravado
def calculate_rms(audio_data):
    audio_data = np.clip(audio_data, -1.0, 1.0)
    rms = np.sqrt(np.mean(np.square(audio_data)))
    return rms

def play_sound(mapping, duration):
    sd.play(buffer, samplerate=samplerate, mapping=mapping, device=output_device_index)
    sd.sleep(int(duration * 1000))  # Mantém a reprodução por toda a duração

# Teste para o lado esquerdo (mapping = [1]) e direito (mapping = [2])
for mapping in ([1], [2]):
    all_pass = True
    play_thread = threading.Thread(target=play_sound, args=(mapping, duracao))
    record_thread = threading.Thread(target=record_audio, args=(duracao,))

    # Iniciar threads
    play_thread.start()
    record_thread.start()

    # Esperar as threads terminarem
    play_thread.join()
    record_thread.join()

    print(f"Testando mapeamento: {mapping}")
    
    # Calcula o valor RMS do áudio captado
    if recorded_audio is not None:
        rms_value = calculate_rms(recorded_audio)
        print(f"RMS: {rms_value}")

        # Verifica se o valor RMS está dentro do limite aceitável
        if rms_value > limite_pass:
            print(f"Pass: O áudio captado está dentro do range aceitável para o lado {mapping}.")
        else:
            print(f"Fail: O áudio captado está fora do range aceitável para o lado {mapping}.")
            all_pass = False
    else:
        all_pass = False
        print(f"Erro: Áudio não foi gravado para o mapeamento {mapping}.")
    
    filename = f"output_audio_mapping_{mapping}.wav"
    save_audio(os.path.join(tmp_dir, filename), recorded_audio, samplerate) 
    time.sleep(0.5)

if all_pass == True:
    with open('Pass.txt','w') as file:
        file.write('PASS MIC AND SPEAKER L and R Channel')
else:
    with open('fail.txt','w') as file:
        file.write('FAIL MIC AND SPEAKER L and R Channel')

