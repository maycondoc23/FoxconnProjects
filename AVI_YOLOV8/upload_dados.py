import mysql.connector
from mysql.connector import Error
from datetime import datetime
import requests
import xmltodict



def upload_dados(SerialNumber, Status, datetimefile, datecreate, componentes):

    try:
        idline = 7
        idmachine = 1211
        model = "HUAWEI"
        testedcomponents = 0
        flaws = 0
        userflaws = 0
        iduser = 105

        
        connection = mysql.connector.connect(
            host="10.8.28.68",  
            user="falconcore",        
            password="f@lc0nc0r3",  
            database="dbfalconcore"  
        )

        for componente, info in componentes.items():
            status = info["status"]
            if status == "FAIL":
                userflaws += 1
            flaws += 1


        if connection.is_connected():
            wo, pn = get_wo(SerialNumber)

            cursor = connection.cursor()
            sql_insert_query = """
            INSERT INTO automated_optical_inspections (IdLine, IdMachine, WorkOrder, PartNumber, SerialNumber,
            Model, Status, TestedComponents, Flaws, UserFlaws, DateTimeFile, DateCreate, IdUser)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            insert_tuple = (idline, idmachine, int(wo.replace("-1","")), pn, SerialNumber,
            model, Status, testedcomponents, flaws, userflaws, datecreate, datetimefile, iduser)
            print("inserindo dados na    tabela automated_optical_inspections...")
            cursor.execute(sql_insert_query, insert_tuple)
            print("cursor.executed")

            idinspection = cursor.lastrowid


            for componente, info in componentes.items():
                photo = info["imagem"]
                status = info["status"]

                failuretype = "P"
                if status == "FAIL":
                    failuretype = "F"

                # ler pasta com iamgem e transformar para blob
                with open(photo, 'rb') as file:
                    photo_bytes = file.read()
                
                query = """
                INSERT INTO automated_optical_inspection_photo (IdAutomatedOpticalInspection, Component, FailureType, Type, Photo, PartNumber)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (idinspection, componente, "SOLDER", failuretype, photo_bytes, "N/A"))

            connection.commit()

            print("Dados inseridos com sucesso na tabela automated_optical_inspections")

    except Error as e:
        print("Erro ao conectar ao MySQL", e)

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexão MySQL foi encerrada")    

def get_wo(serial, customer="HUAWEI", level="L06"):
    
    resultado = ','
    url = f"http://10.8.2.50:88/WebServiceTest.asmx"  # URL correta com http://

    headers = {
        "Content-Type": "application/soap+xml;charset=UTF-8",
        "SOAPAction": "http://foxconn/fbrla/webservice/test/SFIS_LOGOUT",
        "X-Customer": f"HUAWEI",
        "X-Type": f"L06"
    }

    soap_body = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:test="http://foxconn/fbrla/webservice/test">
        <soap:Header/>
        <soap:Body>
            <test:SFIS_GET_DATA>
                <test:motherBoardSerialNumber>{serial}</test:motherBoardSerialNumber>
            </test:SFIS_GET_DATA>
        </soap:Body>
        </soap:Envelope>"""

    response = requests.post(url, headers=headers, data=soap_body)
    
    if response.status_code == 200:
        response_dict = xmltodict.parse(response.content)
        device_details = response_dict['soap:Envelope']['soap:Body']['SFIS_GET_DATAResponse']['SFIS_GET_DATAResult']['Configuration']['DeviceDetails']['DeviceDetail']
        pn = response_dict['soap:Envelope']['soap:Body']['SFIS_GET_DATAResponse']['SFIS_GET_DATAResult']['Configuration']['Sku']

        # Check if device_details is a list or a single dictionary
        if isinstance(device_details, list):
            for device_detail in device_details:
                if device_detail.get('@Key') == 'WORKORDER':
                    # print(device_detail)  # Changed 'device_detail' to 'device_detail' to show content
                    workorder_value = device_detail.get('#text', None)
                    break

        elif isinstance(device_details, dict):
            device_detail = device_details  # If there's only one device_detail, use it directly
            if device_detail.get('@Key') == 'WORKORDER':
                # print(device_detail)
                workorder_value = device_detail.get('#text', None)


        return [workorder_value, pn]
    else:
        print(f"Erro na requisição: {response.status_code} - {response.text}")
        return '1,Erro na requisição'


workorder = 0
partnumber = ""
# serialnumber = "RY2570034921"

# status = "RPASS"


# datecreate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# datetimefile = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# IdAutomatedOpticalInspection = 0
# component = ["BOSA1", "BOSA2"]
# failuretype = ""
# type = ""
# photo   = r"C:\Users\mayconcosta\yolo-V8\testeyolo\Logs\14082025\xxxxxx_072322\capacitor2.bmp"
# IdAutomatedOpticalInspection = 0
# type = "F"

# upload_dados(serialnumber, status, datetimefile, datecreate, component, photo)
# logout_cmc(serialnumber)