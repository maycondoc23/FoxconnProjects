import csv

with open('FUNCTIONerror.DAT', 'w', encoding='utf-8') as file:
    # Iterar pelas partes processadas e escrever as traduções
    for i, parte in enumerate(partes_processadas):
        traducao = traducoes.get(parte[:2], 'Desconhecido')  # Usa os 2 primeiros dígitos para buscar a tradução
        # Verifica se não é a última tradução para não adicionar '__'
        if i < len(partes_processadas) - 1:
            file.write(f'{traducao}__')
        else:
            file.write(f'{traducao}')
