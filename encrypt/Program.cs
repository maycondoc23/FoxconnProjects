using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace FoxCore.ConsoleCrypt
{
    internal enum CryptProvider
    {
        Rijndael,
        RC2,
        DES,
        TripleDES
    }

    public class Crypt
    {
        private string _key = string.Empty;
        private CryptProvider _cryptProvider;
        private SymmetricAlgorithm _algorithm;

        private void SetIV()
        {
            if (_cryptProvider == CryptProvider.Rijndael)
            {
                _algorithm.IV = new byte[]
                {
                    0x0f,0x6f,0x13,0x2e,0x35,0xc2,0xcd,0xf9,
                    0x05,0x46,0x9c,0xea,0xa8,0x4b,0x73,0xcc
                };
            }
            else
            {
                _algorithm.IV = new byte[] { 0x0f, 0x6f, 0x13, 0x2e, 0x35, 0xc2, 0xcd, 0xf9 };
            }
        }

        public string Key
        {
            get { return _key; }
            set { _key = value; }
        }

        public Crypt()
        {
            _algorithm = new RijndaelManaged();
            _algorithm.Mode = CipherMode.CBC;
            _cryptProvider = CryptProvider.Rijndael;
        }

        public virtual byte[] GetKey()
        {
            string salt = string.Empty;

            if (_algorithm.LegalKeySizes.Length > 0)
            {
                int keySize = _key.Length * 8;
                int minSize = _algorithm.LegalKeySizes[0].MinSize;
                int maxSize = _algorithm.LegalKeySizes[0].MaxSize;
                int skipSize = _algorithm.LegalKeySizes[0].SkipSize;

                if (keySize > maxSize)
                {
                    _key = _key.Substring(0, maxSize / 8);
                }
                else if (keySize < maxSize)
                {
                    int validSize = (keySize <= minSize) ? minSize : (keySize - keySize % skipSize) + skipSize;
                    if (keySize < validSize)
                        _key = _key.PadRight(validSize / 8, '*');
                }
            }

            PasswordDeriveBytes pdb = new PasswordDeriveBytes(_key, Encoding.ASCII.GetBytes(salt));
            return pdb.GetBytes(_key.Length);
        }

        public string Encrypt(string text)
        {
            byte[] plainBytes = Encoding.UTF8.GetBytes(text);
            byte[] keyBytes = GetKey();
            Console.WriteLine(plainBytes.Length + keyBytes.Length);
            Console.WriteLine(keyBytes);

            _algorithm.Key = keyBytes;
            SetIV();

            ICryptoTransform encryptor = _algorithm.CreateEncryptor();

            using (MemoryStream ms = new MemoryStream())
            using (CryptoStream cs = new CryptoStream(ms, encryptor, CryptoStreamMode.Write))
            {
                cs.Write(plainBytes, 0, plainBytes.Length);
                cs.FlushFinalBlock();
                return Convert.ToBase64String(ms.ToArray());
            }
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            if (args.Length < 1)
            {
                Console.WriteLine("Uso: crypt.exe <senha>");
                return;
            }

            string senha = args[0];
            Crypt crypt = new Crypt();
            //crypt.Key = senha;

            string resultado = crypt.Encrypt(senha);
            Console.WriteLine(resultado);
        }
    }
}
