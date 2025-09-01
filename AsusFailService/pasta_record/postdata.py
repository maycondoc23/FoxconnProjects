import requests
import json

# URL da API
url = "http://foxcore.la.foxconn.com:8081/api/FailureLog/SendProjectLog"

# Abrir e ler o conteúdo do arquivo de falha
with open('NBQH1110053129106C3400_FAIL.txt', 'r') as file:
    textofalha = file.read()

params = {
    'IdProject': 18,
    'SerialNumber': "NBQH1110053129106C3401"
}

body = textofalha

print("Corpo da requisição:")
print(textofalha)

response = requests.post(url, params=params, json=textofalha)


try:
    print("Status da resposta:", response.status_code)
except ValueError:
    print("A resposta não está em formato JSON.")
