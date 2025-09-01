using System;
using System.Data;
using NAudio.CoreAudioApi;

class Program
{
    static void Main()
    {
        try
        {
            // Inicializa o dispositivo de áudio padrão
            var enumerator = new MMDeviceEnumerator();
            MMDevice device = enumerator.GetDefaultAudioEndpoint(DataFlow.Render, Role.Multimedia);

            Console.WriteLine("Dispositivo padrão: " + device.FriendlyName);

            // Define o volume geral
            device.AudioEndpointVolume.MasterVolumeLevelScalar = 1.0f; // 100%

            // Define o balanço (0.0 = só esquerda, 1.0 = só direita)
            // Vamos colocar totalmente para a esquerda
            device.AudioEndpointVolume.Channels.ToString();
            int channels = device.AudioEndpointVolume.Channels.Count;

            if (channels >= 2)
            {
                // Canal esquerdo = 100%, direito = 0%
                device.AudioEndpointVolume.Channels[0].VolumeLevelScalar = 1.0f; // Esquerdo
                device.AudioEndpointVolume.Channels[1].VolumeLevelScalar = 0.0f; // Direito
                Console.WriteLine("Balanço ajustado: Esquerda 100%, Direita 0%");
            }
            else
            {
                Console.WriteLine("O dispositivo de áudio não suporta canais esquerdo/direito separadamente.");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("Erro: " + ex.Message);
        }
    }
}
