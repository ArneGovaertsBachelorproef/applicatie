import io, sys, os, json, sqlite3, subprocess

from enum import Enum
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
            return (self.__google_cloud(dialect_opvangen=False), 'GOOGLE_ENKEL_NL_BE')
        except Exception as e:
            return (self.__vosk(small=True), 'VOSK_SMALL')

    def __google_cloud(self, dialect_opvangen: bool) -> str:
        client = speech.SpeechClient()

        with io.open(self.__audio_file_path, 'rb') as speech_file:
            content = speech_file.read()

        audio = speech.RecognitionAudio(content=content)

        if dialect_opvangen:
            # nl-BE als hoofdtaal, nl-NL, fr-BE en fr-FR om dialect op te vangen
            config = speech.RecognitionConfig(
                language_code='nl-BE',
                alternative_language_codes=['nl-NL', 'fr-BE', 'fr-FR'] # dialect hiermee opgelost?
            )
        else:
            # uitsluitend nl-BE
            config = speech.RecognitionConfig(
                language_code='nl-BE'
            )

        response = client.recognize(config=config, audio=audio)

        transcript = ''
        for result in response.results:
            transcript = transcript + str(result.alternatives[0].transcript)

        return transcript

    def __vosk(self, small=True) -> str:
        SetLogLevel(0)

        sample_rate = 16000
        if small:
            model   = Model(os.path.dirname(os.path.realpath(__file__)) + '/models/vosk/small')
        else:
            model   = Model(os.path.dirname(os.path.realpath(__file__)) + '/models/vosk/big')
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
