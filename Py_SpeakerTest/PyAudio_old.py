import sounddevice as sd
import numpy as np
import os
import wave
import time

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

# Teste para o lado esquerdo (mapping = [1]) e direito (mapping = [2])
for mapping in ([1], [2]):
    lado = 'Speaker L' if 1 in mapping else 'Speaker R'
    print(f"Testando {lado}")

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

        # Verifica se o valor RMS está dentro do limite aceitável
        if rms_value > limite_pass:
            print(f"Pass: O áudio captado está dentro do range aceitável para o {lado}.")
        else:
            print(f"Fail: O áudio captado está fora do range aceitável para o {lado}.")
            all_pass = False
    else:
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
