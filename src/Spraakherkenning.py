import io, sys, os, json, sqlite3, subprocess

from pathlib import Path
from google.cloud import speech
from vosk import Model, KaldiRecognizer, SetLogLevel

class Spraakherkenning:
    """ klasse die alle methodes omvat voor spraakherkenning

    methodes:
        * tekst() -> str
    
    constructor:
        :param audio_file_path: bestandsnaam als string
    """
    def __init__(self, audio_file_path: str):
        """ constructor
        :param audio_file_path: bestandsnaam als string
        """
        print('init Spraakherkenning')
        self.__audio_file_path    = audio_file_path
    
    def tekst(self) -> tuple:
        """ omzetten van spraak naar tekst
        :param: methode
        :return str: transcriptie
        """
                
        try:
            return (self.__google_cloud(), 'GOOGLE_ENKEL_NL_BE')
        except Exception as e:
            print(str(e))
            return (self.__vosk(), 'VOSK_SMALL')

    def __google_cloud(self) -> str:
        client = speech.SpeechClient()

        #wav_bestand  = Path(self.__audio_file_path)
        #flac_bestand = wav_bestand.with_suffix('.flac')

        with io.open(str(self.__audio_file_path), 'rb') as speech_file:
            content = speech_file.read()

        audio = speech.RecognitionAudio(content=content)

        # config = speech.RecognitionConfig(
        #     language_code='nl-BE',
        #     encoding='FLAC',
        #     sample_rate_hertz=16000
        # )

        config = speech.RecognitionConfig(
            language_code='nl-BE',
            audio_channel_count=2,
            enable_separate_recognition_per_channel=False,
        )

        response = client.recognize(config=config, audio=audio)
        results = response.results

        transcript = ''
        for result in results:
            transcript = transcript + str(result.alternatives[0].transcript)

        return transcript

    def __vosk(self) -> str:
        SetLogLevel(0)

        sample_rate = 16000
        model       = Model(os.path.dirname(os.path.realpath(__file__)) + '/models/vosk/small')
        rec         = KaldiRecognizer(model, sample_rate)

        process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i', self.__audio_file_path, '-ar', str(sample_rate) ,
            '-ac', '1', '-f', 's16le', '-'], stdout=subprocess.PIPE)

        res = []

        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                temp_res = json.loads(rec.Result())
                res.append(temp_res['text'])
        
        temp_res = json.loads(rec.FinalResult())
        res.append(temp_res['text'])

        return ' '.join(res)
