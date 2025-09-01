from db_connection import connect_db
import time


conn = connect_db()
cursor = conn.cursor()

def insert_pcba_data(cursor, data):
    query = """
    INSERT INTO huawei_test_logs (SerialNumber, PcbaSerialNumber, Status, DateCreate, Starttime, Endtime, Duration, 
                           Station, StationId, Product, UserId, Slot, level, TestVersion, WorkOrder, wifiStation, wifiSlot, wifiDate, TxStation, TxSlot, TxDate, Log, IdUser)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        data['SerialNumber'],
        data['PcbaSerialNumber'],
        data['Status'],
        data['DateCreate'],
        data['Starttime'],
        data['Endtime'],
        data['Duration'],
        data['Station'],
        data['StationId'],
        data['Product'],
        data['UserId'],
        data['Slot'],
        data['level'],
        data['TestVersion'],
        data['WorkOrder'],
        data['wifiStation'],
        data['wifiSlot'],
        data['wifiDate'],
        data['TxStation'],
        data['TxSlot'],
        data['TxDate'],
        data['Log'],
        data['IdUser']
    ))

def insert_failure(cursor, pcba_data_id, test_name, subtest_name):
    query = """
    INSERT INTO huawei_test_log_failures (IdHuaweiLog, TestName, SubTestName)
    VALUES (%s, %s, %s)
    """
    cursor.execute(query, (pcba_data_id, test_name, subtest_name))

def get_pcba_test_data(cursor, SerialNumber):
    # Executando a consulta
    query = f"""
    SELECT STATIONID, SLOT, DateCreate FROM dbfalconcore.huawei_test_logs
    WHERE SerialNumber = '{SerialNumber}' ORDER BY ID DESC LIMIT 1;
    """
    cursor.execute(query)
    # Obtendo o resultado
    result = cursor.fetchone()
    print('RESULTADO DA CONSULTA DOS DADOS WIFI: ' ,result)

    # if result == None:
    #     result = ['','']
    
    return result

def get_TX_test_data(cursor, SerialNumber):
    # Executando a consulta
    print(SerialNumber)
    query = f"""
    SELECT STATIONID, SLOT, DateCreate FROM dbfalconcore.huawei_test_logs
    WHERE SerialNumber = "{SerialNumber}" and STATION = "ST-MP13" ORDER BY DateCreate DESC LIMIT 1;
    """
    print(query)
    # time.sleep(10)
    cursor.execute(query)
    # Obtendo o resultado
    result = cursor.fetchone()
    print('RESULTADO DA CONSULTA DOS DADOS DE TX (MP13): ' ,result)

    # if result == None:
    #     result = ['','']
    
    return result


def verificar_dados_existentes(cursor,serial_number, pcba_sn, datetime, starttime, endtime, stationid):
    try:
        # Exemplo de consulta para verificar se os dados já existem
        query = """
            SELECT id FROM dbfalconcore.huawei_test_logs 
            WHERE SerialNumber = %s AND PcbaSerialNumber = %s 
            AND DateCreate = %s AND Starttime = %s 
            AND Endtime = %s AND StationId = %s
        """
        cursor.execute(query, (serial_number, pcba_sn, datetime, starttime, endtime, stationid))
        result = cursor.fetchall()
        print(result)
        if result:
            # Dados encontrados
            print("Dados já existem:")
            for row in result:
                print(row)  # Aqui você pode personalizar para exibir de forma mais legível
            return True
        else:
            print("Dados ainda nao existem")
            # Dados não encontrados
            return False
    except Exception as e:
        print(f"Erro ao verificar dados existentes: {e}")
        return False