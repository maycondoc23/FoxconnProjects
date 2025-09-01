import sounddevice as sd
from tkinter import messagebox
import messagebox


# devices = sd.query_devices()
# print(devices)
def Check_HeadPhones():
    run = True
    while run == True:
        with open('config.ini', 'r') as file:
            for line in file.readlines():
            # print(line)
                if 'block_loopback' in line:
                    config,block = line.split('=')
                    block = block.replace("'","").strip()
                    print(block)
                try:
                    if str(block).upper() == 'NONE':
                        with open('devicepass.txt', 'w') as file:
                            file.write('Loopback_removed')
                        run = False
                except:
                    pass
        if run == True:
            devices = sd.query_devices()
        # print(devices)
            if str(block.upper().strip()) in str(devices).upper():
                messagebox.showerror('DeviceCheck','Remova o Cabo de AudioLoopback')
                exit()
            else:
                with open('devicepass.txt', 'w') as file:
                    file.write('Loopback_removed')
                exit() 
        else: 
            exit()

Check_HeadPhones()