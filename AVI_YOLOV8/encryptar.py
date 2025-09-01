from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA1
import base64
import sys


class Crypt:
    def __init__(self, key: str):
        self._key = key
        self._iv_rijndael = bytes([
            0x0f, 0x6f, 0x13, 0x2e,
            0x35, 0xc2, 0xcd, 0xf9,
            0x05, 0x46, 0x9c, 0xea,
            0xa8, 0x4b, 0x73, 0xcc
        ])
        self._block_size = 16

    def adjust_key(self, key: str):
        """Simula a lógica de ajuste da chave do C#."""
        key_size = len(key) * 8
        min_size = 128
        max_size = 256
        skip_size = 64

        if key_size > max_size:
            key = key[:max_size // 8]
        elif key_size < max_size:
            valid_size = min_size if key_size <= min_size else ((key_size - key_size % skip_size) + skip_size)
            key = key.ljust(valid_size // 8, '*')
        return key

    def get_key(self):
        """Simula PasswordDeriveBytes do C# usando PBKDF2 com SHA1 (sem salt)."""
        adjusted_key = self.adjust_key(self._key)
        salt = b''  # C# usa salt vazio
        key_bytes = PBKDF2(
            adjusted_key.encode('ascii'),
            salt,
            dkLen=len(adjusted_key),
            count=1000,
            hmac_hash_module=SHA1
        )
        return key_bytes

    def encrypt(self, text: str):
        key_bytes = self.get_key()
        cipher = AES.new(key_bytes, AES.MODE_CBC, self._iv_rijndael)
        padded = pad(text.encode('utf-8'), self._block_size)
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode('utf-8')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python crypt.py <senha>")
        sys.exit(1)

    senha = sys.argv[1]
    crypt = Crypt(senha)
    resultado = crypt.encrypt(senha)
    print(resultado)
