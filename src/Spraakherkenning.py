import os, io, sys, json, wave, subprocess

from enum import Enum
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
        self.__audio_file_path    = audio_file_path
    
    def tekst(self) -> tuple:
        # try: 
        #    return {
        #        'transcriptie': self.__google_cloud(),
        #        'methode': 'Google Clooud'
        #    }
        # except Exception as e:
        return (self.__vosk(), 'VOSK')

    def __google_cloud(self) -> str:
        client = speech.SpeechClient()

        with io.open(self.__audio_file_path, 'rb') as speech_file:
            content = speech_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            language_code='nl-BE'
        )
        response = client.recognize(config=config, audio=audio)

        transcript = ''
        for result in response.results:
            transcript = transcript + str(result.alternatives[0].transcript)

        return transcript

    def __vosk(self) -> str:        
        oud_pad     = Path(self.__audio_file_path)
        nieuw_pad   = oud_pad.with_suffix('.wav')
        os.system('ffmpeg -y -v info -i ' + str(oud_pad.absolute()) + ' ' + str(nieuw_pad.absolute()))

        SetLogLevel(0)

        sample_rate = 16000
        model       = Model('vosk-model-nl-spraakherkenning-0.6')
        rec         = KaldiRecognizer(model, sample_rate)

        process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i', str(nieuw_pad.absolute()), '-ar', str(sample_rate) ,
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
