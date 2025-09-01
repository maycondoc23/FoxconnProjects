import requests
import xmltodict


def logout_cmc(serial, customer, level):
    
    resultado = ','
    url = f"http://10.8.2.50:88/WebServiceTest.asmx"  # URL correta com http://

    headers = {
        "Content-Type": "application/soap+xml;charset=UTF-8",
        "SOAPAction": "http://foxconn/fbrla/webservice/test/SFIS_LOGOUT",
        "X-Customer": f"{customer}",
        "X-Type": f"{level}"
    }

    soap_body = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:test="http://foxconn/fbrla/webservice/test">
        <soap:Header/>
        <soap:Body>
            <test:SFIS_LOGOUT>
                <test:motherBoardSerialNumber>{serial}</test:motherBoardSerialNumber>
                <test:operatorId>TEST</test:operatorId>
                <test:productionLine>TEST</test:productionLine>
                <test:stationGroup>AVITU</test:stationGroup>
                <test:hostname>AVITU01</test:hostname>
                <test:statusCode>0</test:statusCode>
            </test:SFIS_LOGOUT>
        </soap:Body>
        </soap:Envelope>"""

    response = requests.post(url, headers=headers, data=soap_body)

    if response.status_code == 200:
        response_dict = xmltodict.parse(response.content)
        # print(response_dict)
        result_code = response_dict['soap:Envelope']['soap:Body']['SFIS_LOGOUTResponse']['SFIS_LOGOUTResult']['StatusCode']
        print(result_code)
        if str(result_code).strip() == '0':
            result_message = 'PASS'
        else:
            result_message = response_dict['soap:Envelope']['soap:Body']['SFIS_LOGOUTResponse']['SFIS_LOGOUTResult']['ErrorMessage']
            print(result_message)
            # device_details = response_dict['soap:Envelope']['SFIS_LOGOUTResult']['SFIS_GET_DATAResponse']['SFIS_GET_DATAResult']['Configuration']['DeviceDetails']['DeviceDetail']

        resultado = f'{result_code,result_message}'
        print(resultado)
        return resultado
