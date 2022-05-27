import os, pyphen, queries, spacy, re, string

class TekstGebaseerd:
    def __init__(self, db_connection_uri, transcript: str):
        print('init TekstGebaseerd')
        self.__transcript = transcript
        self.__db_connection_uri = db_connection_uri

    def woordlengteratio(self) -> float:
        # long woord ratio =  the amount of woords that contain more than three syllables divided by the total amount of woords
        dic = pyphen.Pyphen(lang='nl_NL') # Pyphen kent geen Belgisch Nederlands
        drie_of_meer_lettergrepen = 0.0

        woorden = self.__transcript.lower().replace('.','').replace('?','').replace('!','').replace(',','').split()
        if len(woorden) == 0:
            return -1

        for woord in woorden:
            letterprepen = dic.inserted(woord).split('-')
            if len(letterprepen) > 2:
                drie_of_meer_lettergrepen += 1

        return drie_of_meer_lettergrepen / len(woorden)

    def cilt(self) -> float:
        transcript_list = self.__transcript.lower().replace('.','').replace('?','').replace('!','').replace(',','').split()
        freq77 = 0.0
        avgwoordlen = 0.0

        if len(transcript_list) == 0:
            return -1

        with queries.Session(self.__db_connection_uri) as session:
            for woord in transcript_list:
                number = session.query('select nummer from freq77 where woord = %s', [ woord ])
                if len(number) > 0:
                    freq77 += 1

        freq77 /= len(transcript_list)
        avgwoordlen = sum( map(len, transcript_list) ) / len(transcript_list)

        return round(114.49 + 0.28 * freq77 - 12.33 * avgwoordlen, 2)

    def aantal_verkleinwoorden(self) -> int:
        # eindigen op -je, -tje, -etje, -pje, -kje, -tsje, -jes, -tjes, -etjes, -pjes, -kjes, -tsjes, -ke of -ken
        # filteren met woordenlijst -> nog op te stellen, zie: https://github.com/OpenTaal/opentaal-wordlist en lijst voornamen en plaatsnamen
        # tellen

        def deel_in_basiswoordenlijst(woorddeel):
            with queries.Session(self.__db_connection_uri) as session:
                res = session.query('select woord from woordenlijst where woord = %s', [woorddeel])
                return len(res) > 0

        transcript_list = self.__transcript.lower().split()
        count = 0

        for woord in transcript_list:
            if len(woord) > 2 and woord[-2:] == 'je' or woord[-2:] == 'ke' or woord[-3:] == 'jes' or woord[-3:] == 'ken':
                if deel_in_basiswoordenlijst(woord[:-2]) or deel_in_basiswoordenlijst(woord[:-3]):
                    count += 1

        return count

    def aantal_collectieve_voornaamwoorden(self) -> int:
        transcript_list = self.__transcript.lower().replace('.','').replace('?','').replace('!','').replace(',','').split()
        return transcript_list.count('we') + transcript_list.count('ons') + transcript_list.count('onze')

    def aantal_bevestigende_tussenwerpsels(self) -> int:
        transcript_list = self.__transcript.lower().replace('.','').replace('?','').replace('!','').replace(',','').split()
        print(transcript_list)
        return transcript_list.count('hé') + transcript_list.count('voilà') + transcript_list.count('he') + transcript_list.count('voila')

    def textcat_elderspeak(self) -> float:
        def preprocess_text(text):
            text = text.lower().strip()
            text = re.compile('<.*?>').sub('', text)
            text = re.compile('[%s]' % re.escape(string.punctuation)).sub(' ', text)
            text = re.sub('\s+', ' ', text)
            text = re.sub(r'\[[0-9]*\]',' ',text)
            text = re.sub(r'[^\w\s]', '', str(text).lower().strip())
            text = re.sub(r'\d',' ',text)
            text = re.sub(r'\s+',' ',text)

            return text

        nlp = spacy.load(os.path.dirname(os.path.realpath(__file__)) + '/models/spacy/model-best')
        doc = nlp(preprocess_text(self.__transcript))
        return doc.cats['elderspeak']

    def aantal_herhalingen(self) -> int:        
        sp = spacy.load('nl_core_news_lg')

        stopwoorden = sp.Defaults.stop_words
        transcript_list = self.__transcript.lower().split()
        zonder_stopwoorden = [ woord for woord in transcript_list if not woord in stopwoorden ]
        count_met_dict = { woord:zonder_stopwoorden.count(woord)
                            for woord in zonder_stopwoorden if zonder_stopwoorden.count(woord) > 1 }
        return(len(count_met_dict))