import hashlib
import os
import time
file_stat = os.stat('Foxcore_SendFails.txt')
criacao_arquivo = time.ctime(file_stat.st_mtime)

with open('Foxcore_SendFails.txt','r') as file:
    conteudo_arquivo = file.read()
var1 = criacao_arquivo
var2 = conteudo_arquivo

combined = str(var1) + str(var2)

md5_hash = hashlib.md5(combined.encode()).hexdigest()

print("MD5:", md5_hash)
