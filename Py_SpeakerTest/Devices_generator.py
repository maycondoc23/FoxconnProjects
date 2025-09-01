import sounddevice as sd

devices = sd.query_devices()
print(devices)

with open('Devices.txt','w') as file:
    file.write(str(devices))