import math, parselmouth, datetime

from parselmouth.praat import call

class PraatGebaseerd:
    """ klasse die alle op PRAAT gebaseerde resultaten omvat

    methodes:
        * geluidsniveau_in_db() -> float
        * spraaksnelheid_in_sylps() -> float
        * gemiddelde_toonhoogte_in_hz(self) -> float
    
    constructor:
        :param audio_file_path: bestandsnaam als string
    """
    def __init__(self, audio_file_path: str):
        """ constructor
        :param audio_file_path: bestandsnaam als string
        """
        print('inti PRAAT')
        self.__audio_file_path = audio_file_path
    
    def opnameduur(self) -> str:
        sound = parselmouth.Sound(self.__audio_file_path)
        dur = sound.get_total_duration()
        return str(datetime.timedelta(seconds=dur))

    def geluidsniveau_in_db(self) -> float:             # intensity 
        """ opvragen van het geluidsniveau uitgedrukt in decibel
        :return float: geluidsniveau
        """
        sound = parselmouth.Sound(self.__audio_file_path)
        intensiteit = sound.to_intensity()
        return intensiteit.get_average()
    
    def spraaksnelheid_in_sylps(self) -> float:         # speech rate
        """ opvragen van de spraaksnelheid uitgedrukt in syllables per seconde
        :return float: spraaksnelheid
        """
        # zie: https://osf.io/r8jau/?ref=499aefb361abec341bcebd133699270d3d66f0d5
        # en https://github.com/Voice-Lab/VoiceLab/blob/main/Voicelab/toolkits/Voicelab/MeasureSpeechRateNode.py        
        silencedb = -25
        mindip = 2
        minpause = 0.3

        sound = parselmouth.Sound(self.__audio_file_path)
        originaldur = sound.get_total_duration()
        intensity = sound.to_intensity(50)
        start = call(intensity, 'Get time from frame number', 1)
        nframes = call(intensity, 'Get number of frames')
        end = call(intensity, 'Get time from frame number', nframes)
        min_intensity = call(intensity, 'Get minimum', 0, 0, 'Parabolic')
        max_intensity = call(intensity, 'Get maximum', 0, 0, 'Parabolic')

        # get .99 quantile to get maximum (without influence of non-speech sound bursts)
        max_99_intensity = call(intensity, 'Get quantile', 0, 0, 0.99)

        # estimate Intensity threshold
        threshold = max_99_intensity + silencedb
        threshold2 = max_intensity - max_99_intensity
        threshold3 = silencedb - threshold2
        if threshold < min_intensity:
            threshold = min_intensity

        # get pauses (silences) and speakingtime
        textgrid = call(intensity, 'To TextGrid (silences)', threshold3, minpause, 0.1, 'silent', 'sounding')
        silencetier = call(textgrid, 'Extract tier', 1)
        silencetable = call(silencetier, 'Down to TableOfReal', 'sounding')
        npauses = call(silencetable, 'Get number of rows')
        speakingtot = 0
        for ipause in range(npauses):
            pause = ipause + 1
            beginsound = call(silencetable, 'Get value', pause, 1)
            endsound = call(silencetable, 'Get value', pause, 2)
            speakingdur = endsound - beginsound
            speakingtot += speakingdur

        intensity_matrix = call(intensity, 'Down to Matrix')
        # sndintid = sound_from_intensity_matrix
        sound_from_intensity_matrix = call(intensity_matrix, 'To Sound (slice)', 1)
        # use total duration, not end time, to find out duration of intdur (intensity_duration)
        # in order to allow nonzero starting times.
        intensity_duration = call(sound_from_intensity_matrix, 'Get total duration')
        intensity_max = call(sound_from_intensity_matrix, 'Get maximum', 0, 0, 'Parabolic')
        point_process = call(sound_from_intensity_matrix, 'To PointProcess (extrema)', 'Left', 'yes', 'no', 'Sinc70')
        # estimate peak positions (all peaks)
        numpeaks = call(point_process, 'Get number of points')
        t = [call(point_process, 'Get time from index', i + 1) for i in range(numpeaks)]

        # fill array with intensity values
        timepeaks = []
        peakcount = 0
        intensities = []
        for i in range(numpeaks):
            value = call(sound_from_intensity_matrix, 'Get value at time', t[i], 'Cubic')
            if value > threshold:
                peakcount += 1
                intensities.append(value)
                timepeaks.append(t[i])

        # fill array with valid peaks: only intensity values if preceding
        # dip in intensity is greater than mindip
        validpeakcount = 0
        currenttime = timepeaks[0]
        currentint = intensities[0]
        validtime = []

        for p in range(peakcount - 1):
            following = p + 1
            followingtime = timepeaks[p + 1]
            dip = call(intensity, 'Get minimum', currenttime, timepeaks[p + 1], 'None')
            diffint = abs(currentint - dip)
            if diffint > mindip:
                validpeakcount += 1
                validtime.append(timepeaks[p])
            currenttime = timepeaks[following]
            currentint = call(intensity, 'Get value at time', timepeaks[following], 'Cubic')

        # Look for only voiced parts
        pitch = sound.to_pitch_ac(0.02, 30, 4, False, 0.03, 0.25, 0.01, 0.35, 0.25, 450)
        voicedcount = 0

        for time in range(validpeakcount):
            querytime = validtime[time]
            whichinterval = call(textgrid, 'Get interval at time', 1, querytime)
            whichlabel = call(textgrid, 'Get label of interval', 1, whichinterval)
            value = pitch.get_value_at_time(querytime) 
            if not math.isnan(value):
                if whichlabel == 'sounding':
                    voicedcount += 1

        return voicedcount / originaldur
    
    def gemiddelde_toonhoogte_in_hz(self) -> float:      # pitch
        """ opvragen van de fundamentele frequentie uitgedrukt in hertz
        :return float: toonhoogte
        """
        sound = parselmouth.Sound(self.__audio_file_path)
        return call(sound.to_pitch(), 'Get mean', 0, 0, 'Hertz')
