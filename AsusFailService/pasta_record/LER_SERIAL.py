import subprocess

def leitura_serial():
    command = "wmic baseboard get serialnumber"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)

    sn = result.stdout.replace('SerialNumber','').strip()

    return sn

retorno = leitura_serial()

print(f'{retorno}')