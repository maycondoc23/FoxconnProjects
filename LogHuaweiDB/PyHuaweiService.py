# pcba_service.py

import win32serviceutil
import win32service
import win32event
import servicemanager
import os
import time
from pathlib import Path

from LogHuaweiDB import coletar_e_enviar, pasta_servidor

class PCBAService(win32serviceutil.ServiceFramework):
    _svc_name_ = "HuaweiDataService"
    _svc_display_name_ = "Huawei Log Collector Service"
    _svc_description_ = "Coleta e envia dados de testes em tempo real."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("HuaweiService started.")
        self.main()

    def main(self):
        pastalog = r'C:\HuaweiLogger'
        if not os.path.exists(pastalog):
            os.makedirs(pastalog)
            
        dataagora = time.strftime("%Y-%m-%d %H:%M:%S")
        folder_path = Path(pasta_servidor)

        processed_path = folder_path / 'processed'
        errors_path = folder_path / 'errors'

        processed_path.mkdir(exist_ok=True)
        errors_path.mkdir(exist_ok=True)

        while self.running:
            for arquivo in folder_path.iterdir():
                if arquivo.is_file():
                    try:
                        coletar_e_enviar(arquivo, folder_path)
                    except Exception as e:
                        with open(fr'C:\HuaweiLogger\log.txt', 'a') as file:
                            file.write(f"{dataagora} ==> Erro ao processar {arquivo.name}: {str(e)}\n\n\n")
                        continue
