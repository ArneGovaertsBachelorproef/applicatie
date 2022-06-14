from dotenv import load_dotenv

load_dotenv()

import os, queries, subprocess

from pathlib import Path
from fastapi import UploadFile
from src.PraatGebaseerd import PraatGebaseerd
from src.Spraakherkenning import Spraakherkenning
from src.TekstGebaseerd import TekstGebaseerd

from huey import RedisHuey
huey = RedisHuey(url=f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}")

async def opslaan_audio_bestand(opname: UploadFile) -> dict:
    try:
        bestands_naam = 'uploads/'

        if not os.path.exists(bestands_naam):
            os.mkdir(bestands_naam)
        bestands_naam += opname.filename
        with open(bestands_naam, 'wb') as bestand:
            data = await opname.read()
            bestand.write(data)

        return {
            'success': True,
            'bestands_naam': bestands_naam
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'step': 'opslaan_audio_bestand'
        }

def insert_gegevens_in_db(gebruiker_id: int, browser: str, operating_system: str, platform: str, bezoeker_id: str, opname_bestandsnaam: str) -> dict:
    try:
        db_connection_uri = queries.uri(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB_NAME'),
            user=os.getenv('POSTGRES_USERNAME'),
            password=os.getenv('POSTGRES_PASSWORD')
        )

        with queries.Session(db_connection_uri) as session:            
            analyse_id = session.query('''insert into analyses (is_gestart, gebruiker_id, opname_bestandsnaam, browser, os, platform, bezoeker_id)
                values(%s, %s, %s, %s, %s, %s, %s)
                returning analyse_id''', [
                    False,
                    gebruiker_id,
                    opname_bestandsnaam,
                    browser,
                    operating_system,
                    platform,
                    bezoeker_id
                ])

            if len(analyse_id) == 1:
                analyse_id = analyse_id.as_dict()

                return {
                    'success': True,
                    'analyse_id': analyse_id['analyse_id']
                }
            
        raise Exception('probleem bij insert basisgegevens')
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'step': 'insert_gegevens_in_db'
        }

@huey.task()
def analyse(analyse_id: int, opname_bestand: str):
    db_connection_uri = queries.uri(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB_NAME'),
        user=os.getenv('POSTGRES_USERNAME'),
        password=os.getenv('POSTGRES_PASSWORD')
    )

    # FLAC naar WAV
    oud_pad     = Path(opname_bestand)
    nieuw_pad   = oud_pad.with_suffix('.wav')
    process = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'quiet', '-i', str(oud_pad.absolute()), str(nieuw_pad.absolute())], stdout=subprocess.PIPE)
    process.wait()
    
    opname_bestand = str(nieuw_pad.absolute())
    print('omgezet naar WAV: ' + opname_bestand)

    # analyseer
    praat = PraatGebaseerd(opname_bestand)
    transcriptie, methode = Spraakherkenning(opname_bestand).tekst()
    tekst_analyse = TekstGebaseerd(transcript=transcriptie, db_connection_uri=db_connection_uri)

    cilt                                = tekst_analyse.cilt()
    woordlengteratio                    = tekst_analyse.woordlengteratio()
    aantal_verkleinwoorden              = tekst_analyse.aantal_verkleinwoorden()
    aantal_collectieve_voornaamwoorden  = tekst_analyse.aantal_collectieve_voornaamwoorden()
    aantal_bevestigende_tussenwerpsels  = tekst_analyse.aantal_bevestigende_tussenwerpsels()
    aantal_herhalingen                  = tekst_analyse.aantal_herhalingen()
    textcat_elderspeak                  = tekst_analyse.textcat_elderspeak()

    with queries.Session(db_connection_uri) as session:
        session.query('''update analyses
        set     is_gestart                          = true,
                analyse_gemaakt_op                  = now(),
                opnameduur                           = %s,
                spraaksnelheid                      = %s,
                geluidniveau                        = %s,
                toonhoogte                          = %s,
                transcriptie                        = %s,
                methode                             = %s,
                cilt                                = %s,
                woordlengteratio                    = %s,
                aantal_verkleinwoorden              = %s,
                aantal_collectieve_voornaamwoorden  = %s,
                aantal_bevestigende_tussenwerpsels  = %s,
                aantal_herhalingen                  = %s,
                textcat_elderspeak                  = %s
        where   analyse_id          = %s''', [
                praat.opnameduur(),
                praat.spraaksnelheid_in_sylps(),
                praat.geluidsniveau_in_db(),
                praat.gemiddelde_toonhoogte_in_hz(),
                transcriptie,
                methode,
                cilt,
                woordlengteratio,
                aantal_verkleinwoorden,
                aantal_collectieve_voornaamwoorden,
                aantal_bevestigende_tussenwerpsels,
                aantal_herhalingen,
                textcat_elderspeak,

                analyse_id
            ])

def analyse_resultaat(analyse_id: int):
    db_connection_uri = queries.uri(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB_NAME'),
        user=os.getenv('POSTGRES_USERNAME'),
        password=os.getenv('POSTGRES_PASSWORD')
    )

    with queries.Session(db_connection_uri) as session:
        resultaat = session.query('''select analyse_id, is_gestart, is_succes, error, analyse_gemaakt_op,
            opnameduur, spraaksnelheid, geluidniveau, toonhoogte, cilt, woordlengteratio, aantal_verkleinwoorden,
            aantal_collectieve_voornaamwoorden, aantal_bevestigende_tussenwerpsels, aantal_herhalingen, textcat_elderspeak
        from analyses
        where analyse_id = %s''', [analyse_id])

        return resultaat.items() 