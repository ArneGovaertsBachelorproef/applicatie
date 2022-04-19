import os
import pyphen

class TekstGebaseerd:
    def __init__(self, transcript: str):
        self.__transcript = transcript

    def woordlengteratio(self) -> float:
        # long word ratio =  the amount of words that contain more than three syllables divided by the total amount of words
        dic = pyphen.Pyphen(lang='nl_NL') # Pyphen kent geen Belgisch Nederlands
        drie_of_meer_lettergrepen = 0.0

        woorden = self.__transcript.lower().replace('.','').replace('?','').replace('!','').replace(',','').split()

        for woord in woorden:
            letterprepen = dic.inserted(woord).split('-')
            if len(letterprepen) > 2:
                drie_of_meer_lettergrepen += 1

        return drie_of_meer_lettergrepen / len(woorden)

    def cilt(self) -> float:
        # zie ook: https://www.nemokennislink.nl/publicaties/leesniveau-zegt-niets-over-leesplezier/
        # CILT =  114.49 + 0.28 × freq77 − 12.33 × avgwordlen
        # cur = self.__con.cursor()

        # transcript_list = self.__transcript.lower().replace('.','').replace('?','').replace('!','').replace(',','').split()
        freq77 = 0.0
        avgwordlen = 0.0

        # for word in transcript_list:
        #     number = cur.execute('select number from freq77 where word = ?', [word]).fetchone()
        #     if number is not None:
        #        freq77 += 1

        # freq77 /= len(transcript_list)
        # avgwordlen = sum( map(len, transcript_list) ) / len(transcript_list)

        return round(114.49 + 0.28 * freq77 - 12.33 * avgwordlen, 2)

    def aantal_verkleinwoorden(self) -> int:
        # eindigen op -je, -tje, -etje, -pje, -kje, -tsje, -jes, -tjes, -etjes, -pjes, -kjes, -tsjes, -ke of -ken
        # filteren met woordenlijst -> nog op te stellen, zie: https://github.com/OpenTaal/opentaal-wordlist en lijst voornamen en plaatsnamen
        # tellen
        # transcript_list = self.__transcript.lower().split()
        count = 0

        # for woord in transcript_list:
        #    if woord[-2:] == 'je' or woord[-3:] == 'jes' or woord[-2:] == 'ke' or woord[-3:] == 'ken':
        #        if not_in_basiswoordenlijst:
        #            count += 1

        return count

    def aantal_collectieve_voornaamwoorden(self) -> int:
        transcript_list = self.__transcript.lower().replace('.','').replace('?','').replace('!','').replace(',','').split()
        return transcript_list.count('we') + transcript_list.count('ons') + transcript_list.count('onze')

    def aantal_bevestigende_tussenwerpsels(self) -> int:
        transcript_list = self.__transcript.lower().replace('.','').replace('?','').replace('!','').replace(',','').split()
        return transcript_list.count('hé') + transcript_list.count('voilà') + transcript_list.count('he') + transcript_list.count('voila')