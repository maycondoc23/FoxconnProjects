import json
from Get_PCBA_DATA import Get_PCBA_SN
import elapsedtime
from pathlib import Path
import insertdb
import os
import time
import shutil
import threading
import insertdb
from insertdb import get_pcba_test_data, get_TX_test_data
import mysql.connector
# server=10.8.28.68;database=dbfalconcore;uid=falconcore;pwd=f@lc0nc0r3;sslmode=none

def connect_db():
    return mysql.connector.connect(
        host="10.8.28.68",  
        user="falconcore",        
        password="f@lc0nc0r3",  
        database="dbfalconcore"  
    )

conn = connect_db()
cursor = conn.cursor()


with open('path.ini','r') as file:
    pasta_servidor = file.read().strip()
    
def coletar_e_enviar(arquivo, pasta):
    try:
        with open(arquivo, 'r') as file:
            log = file.read()

        if 'r1json' in log:
            caminho = "r1json.value.data"  # Este caminho pode ser alterado dinamicamente
            continuar = True
        else:
            continuar = False
            caminho = "value.data"  # Este caminho pode ser alterado dinamicamente

        chaves = caminho.split('.')  # Split para gerar lista de chaves
        data = json.loads(log)

        # Acessar o caminho de forma dinâmica
        for chave in chaves:
            data = data.get(chave, {})  # Usa .get() para evitar erro caso a chave não exista

        for item in data:

            status = item['Result']
            status = "PASS" if str(status) == "0" else "FAIL"

            datetime = f"{str(item['FromTime']).split('T')[0]} {str(item['FromTime']).split('T')[1].split('.')[0]}"
            starttime = str(item["FromTime"])
            endtime = str(item["ToTime"])
            duration = elapsedtime.tempodecorrido(str(starttime), str(endtime))

            station = item['SubStation']
            if station == "1":
                station = "FT2-MP1"
            elif station == "9":
                station = "ST-MP9"
            elif station == "13":
                station = "ST-MP13"
            else:
                station = "FT2-MP6"

            level = "L06"
            if station == "ST-MP9" or station == "ST-MP13":
                level = "L10"


            wifi_station, wifi_slot, wifi_date = '', '', '0001-01-01 01:01:01.000000'
            SerialNumber = item['SN']
            pcba_sn = Get_PCBA_SN(SerialNumber)
            print(f'SerialNumber: {SerialNumber} PCBA_SN: {pcba_sn}')
            
            if str(pcba_sn).strip() != str(SerialNumber).strip() and pcba_sn != None:
                resultado_wifi = get_pcba_test_data(cursor, pcba_sn)

                if resultado_wifi != None:
                    wifi_station, wifi_slot, wifi_date = resultado_wifi
                    print(wifi_station, wifi_slot, wifi_date)
            else:
                print('SerialNumber igual a none  ou vazio')
                pcba_sn = SerialNumber
                wifi_date = '0001-01-01 01:01:01.000000'

            TxDate = '0001-01-01 01:01:01.000000'
            TxSlot = ''
            TxStation = ''
            stationid = item['AteName']
            product = item['UUTName']
            opid = item['OperatorID']
            slot = item['PositionSn']
            testversion = item['UUTVersion']
            workorder = item['WorkOrder']
            print("verificando duplicidade")
            if insertdb.verificar_dados_existentes(cursor, SerialNumber, pcba_sn, datetime, starttime, endtime, stationid):
                print("Os dados já existem na tabela, não será realizada a inserção.")
                shutil.move(arquivo, pasta / 'processed')
                continue 
                
            if station == "ST-MP9":
                print("mp9")
                try:
                    
                    resultado_tx = get_TX_test_data(cursor, SerialNumber)
                    print(resultado_tx)
                    if resultado_tx != None:
                        print(resultado_tx)
                        # time.sleep(2)
                        TxStation, TxSlot, TxDate = resultado_tx
                        print(TxStation, TxSlot, TxDate)
                        # time.sleep(5)
                    else:
                        TxStation, TxSlot, TxDate = ["", "", '0001-01-01 01:01:01.000000']
                        print("nao encontrado")
                except Exception as e:
                    print(e)
                    TxStation, TxSlot, TxDate = ["", "", '0001-01-01 01:01:01.000000']

            # time.sleep(20)


            if continuar ==False:
                  log = None



            data = {
                'SerialNumber': SerialNumber,
                'PcbaSerialNumber': pcba_sn,
                'Status': status,
                'DateCreate': datetime,
                'Starttime': starttime,
                'Endtime': endtime,
                'Duration': duration,
                'Station': station,
                'StationId': stationid,
                'Product': product,
                'UserId': opid,
                'IdUser': 1,
                'Slot': slot,
                'level': level,
                'TestVersion': testversion,
                'WorkOrder': workorder,
                'wifiStation': wifi_station,
                'wifiSlot': wifi_slot,
                'wifiDate': wifi_date,
                'TxStation': TxStation,
                'TxSlot': TxSlot,
                'TxDate': TxDate,
                'Log' : log
            }
            # print(TxSlot)
            # time.sleep(10)
            print("inserindo")
            insertdb.insert_pcba_data(cursor, data)
            # time.sleep(10)
            insertdb.conn.commit()

            pcba_data_id = cursor.lastrowid
            # Inserir as falhas na tabela failures

            test_r2guids = []
            test_subtest = []
            if continuar == True:
                for item in json.loads(log)["r2json"]["value"]["data"]:
                    if item['Value'] == "FAIL":
                        testname = item['UnitName']
                        test_r2guids.append(f"{str(testname)};{str(item['R2Guid'])}")
                
                for item in json.loads(log)["r3json"]["value"]["data"]:
                    for guid in test_r2guids:
                        if str(guid).split(';')[1] == str(item['R2Guid']):
                            test_subtest.append(f'{str(guid).split(";")[0]};{item["SubUnitName"]}')
                
                # Inserir falhas
                for fail_item in test_subtest:
                    test_name, subtest_name = str(fail_item).split(";")
                    insertdb.insert_failure(cursor, pcba_data_id, test_name, subtest_name)
            else:
                  log = ''
                  pass
            # time.sleep(10)
            insertdb.conn.commit()
            print(arquivo)
            print("arquivo finalizado")
            # os.remove(arquivo)
            shutil.move(arquivo, pasta / 'processed')


    except Exception as e:
        with open('log.txt','w') as file:
            # time.sleep(10)
            file.write(str(e))
            print(e)
            shutil.move(arquivo, pasta / 'errors')


with open('log.txt','w') as file:
    file.write('Iniciando o servico de coleta de dados\n')
    file.write('\n\n')


while True:
    folder_path = Path(pasta_servidor)  # Convert to Path object
    # print(folder_path)
    try:

        if not os.path.exists(folder_path / 'processed'):
            os.mkdir(folder_path / 'processed')

        if not os.path.exists(folder_path / 'errors'):
            os.mkdir(folder_path / 'errors')


        for arquivo in sorted(folder_path.iterdir(), key=lambda f: f.name):

            pasta = folder_path / "processed"

            if os.path.isfile(arquivo):
                try:
                    coletar_e_enviar(arquivo, folder_path)
                except Exception as e:
                    with open('log.txt', 'a') as file:
                        file.write(f"\n\nErro ao processar {arquivo.name}: {str(e)}\n")
                    continue

                print(arquivo)
                print('\n')
                # time.sleep(1)
    except Exception as e:
        with open('log.txt','a') as file:
            file.write(f"\n\nErro ao processar arquivos: {str(e)}\n")
        # time.sleep(5)
        print(e)



# folder_path = Path(pasta_servidor)  # Certifique-se que pasta_servidor está definido

# # Itera pelas subpastas da pasta principal
# for item in folder_path.iterdir():
#     if item.is_dir():
#         print(f"Pasta encontrada: {item.name}")
#         if item.name.startswith("ST-"):
#             print(f"Iniciando thread para: {item.name}")
#             threading.Thread(target=loop_pasta, args=(item,), daemon=True).start()
#         else:
#             print(f"Não se aplica para {item.name}")

# # Mantém o script principal vivo
# try:
#     print("Monitoramento iniciado. Pressione Ctrl+C para sair.")
#     while True:
#         time.sleep(1)
# except KeyboardInterrupt:
#     print("Encerrando serviço.")
