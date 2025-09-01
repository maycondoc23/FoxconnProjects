import csv

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
    # Exclui os dois primeiros dígitos
    codigo_restante = codigo[2:]
    # print(codigo_restante)
    # Divide o restante em partes de 3 caracteres e ignora o primeiro caractere de cada parte
    partes = [codigo_restante[i:i+3] for i in range(0, len(codigo_restante), 3)]
    partes_processadas = [parte[:-1] for parte in partes]  # Ignora o último caractere de cada parte
    # Concatena as partes processadas
    codigo_processado = ''.join(partes_processadas)
    # print(partes_processadas)
    # Traduz o código se existir no dicionário
    with open('FUNCTIONerror.DAT','w') as file:
        for i, partes in enumerate(partes_processadas):
        # for partes in partes_processadas:
            traducao = traducoes.get(partes[:2], 'Desconhecido')  # Usa os 2 primeiros dígitos para buscar a tradução
            print(traducao)
            if i < len(partes_processadas) - 1:
                file.write(f'{traducao}__')
            else:
                file.write(f'{traducao}')


csv_path = 'error_dict.csv'
arquivo_saida = 'FUNCTIONerror.DAT'

codigos = '112A12X1231' # Exemplo de códigos
traducoes = carregar_traducoes(csv_path)
processar_codigo(codigos, traducoes)