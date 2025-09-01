import requests
import xmltodict


hostname = '10.8.2.50'  # IP direto do servidor
customer = 'HUAWEI'
level = 'L10'

def Get_PCBA_SN(serial):
    pcba_sn = None
    url = f"http://{hostname}:88/WebServiceTest.asmx"  # URL correta com http://

    headers = {
        "Content-Type": "application/soap+xml;charset=UTF-8",
        "SOAPAction": "http://foxconn/fbrla/webservice/test/SFIS_GET_DATA",
        "X-Customer": f"{customer}",
        "X-Type": f"{level}"
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
        pcba_sn = response_dict['soap:Envelope']['soap:Body']['SFIS_GET_DATAResponse']['SFIS_GET_DATAResult']['Configuration']['MotherBoardSerialNumber']

        return pcba_sn

    else:
        print(f"Erro ao chamar a API SOAP. Status code: {response.status_code}")


    return pcba_sn

# serial = 'RY2520066693'

# print(Get_PCBA_SN(serial))
