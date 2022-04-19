from dotenv import load_dotenv

load_dotenv()

import os, queries

from fastapi import UploadFile
from src.PraatGebaseerd import PraatGebaseerd
from src.Spraakherkenning import Spraakherkenning
from src.TekstGebaseerd import TekstGebaseerd

from huey import RedisHuey
huey = RedisHuey(url='redis://localhost:6379')

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
            'error': str(e)
        }

def insert_gegevens_in_db(gebruiker_id: int, browser: str, operating_system: str, platform: str, bezoeker_id: str, geslacht: str, leeftijd: int, opname_bestandsnaam: str) -> dict:
    try:
        db_connection_uri = queries.uri(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB_NAME'),
            user=os.getenv('POSTGRES_USERNAME'),
            password=os.getenv('POSTGRES_PASSWORD')
        )

        with queries.Session(db_connection_uri) as session:            
            analyse_id = session.query('''insert into analyses (is_gestart, geslacht, leeftijd, gebruiker_id, opname_bestandsnaam, browser, os, platform, bezoeker_id)
                values(%s, %s, %s, %s, %s, %s, %s, %s, %s)
                returning analyse_id''', [
                    False,
                    geslacht,
                    leeftijd,
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
            'error': str(e)
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

    with queries.Session(db_connection_uri) as session:
        praat = PraatGebaseerd(opname_bestand)
        transcriptie, methode = Spraakherkenning(opname_bestand).tekst()
        tekst_analyse = TekstGebaseerd(transcript=transcriptie)

        session.query('''update analyses
        set     is_gestart          = true,
                analyse_gemaakt_op  = now(),

                spraaksnelheid      = %s,
                geluidniveau        = %s,
                toonhoogte          = %s,

                transcriptie        = %s,
                methode             = %s,

                woordlengteratio    = %s,
                aantal_collectieve_voornaamwoorden = %s,
                aantal_bevestigende_tussenwerpsels = %s

        where   analyse_id          = %s''', [
                praat.spraaksnelheid_in_sylps(),
                praat.geluidsniveau_in_db(),
                praat.gemiddelde_toonhoogte_in_hz(),

                transcriptie,
                methode,

                tekst_analyse.woordlengteratio(),
                tekst_analyse.aantal_collectieve_voornaamwoorden(),
                tekst_analyse.aantal_bevestigende_tussenwerpsels(),

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
        resultaat = session.query('''select analyse_id, is_gestart, is_succes, error, analyse_gemaakt_op, geslacht, leeftijd,
            spraaksnelheid, geluidniveau, toonhoogte,
            cilt, woordlengteratio, aantal_collectieve_voornaamwoorden, aantal_bevestigende_tussenwerpsels
        from analyses
        where analyse_id = %s''', [analyse_id])

        return resultaat.items() 