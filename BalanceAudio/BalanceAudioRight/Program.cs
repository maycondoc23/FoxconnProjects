using System;
using AudioSwitcher.AudioApi;
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
            MMDevice device = enumerator.GetDefaultAudioEndpoint(DataFlow.Render, NAudio.CoreAudioApi.Role.Multimedia);

            Console.WriteLine("Dispositivo padrão: " + device.FriendlyName);

            // Define o volume geral  
            device.AudioEndpointVolume.MasterVolumeLevelScalar = 1.0f; // 100%  

            // Vamos colocar totalmente para a esquerda  
            device.AudioEndpointVolume.Channels.ToString();
            int channels = device.AudioEndpointVolume.Channels.Count;

            if (channels >= 2)
            {
                device.AudioEndpointVolume.Channels[0].VolumeLevelScalar = 0.0f; // Esquerdo  
                device.AudioEndpointVolume.Channels[1].VolumeLevelScalar = 1.0f; // Direito  
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("Erro: " + ex.Message);
        }
    }
}
