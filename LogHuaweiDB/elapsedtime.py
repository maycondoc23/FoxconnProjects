from datetime import datetime

def tempodecorrido(incio, fim):
    from_time = datetime.strptime(incio, "%Y-%m-%dT%H:%M:%S.%f")
    to_time = datetime.strptime(fim, "%Y-%m-%dT%H:%M:%S.%f")

    time_diff = to_time - from_time

    # Obter a diferença em segundos
    seconds = time_diff.total_seconds()

    # print(f'Tempo percorrido: {seconds} segundos')
    return seconds
