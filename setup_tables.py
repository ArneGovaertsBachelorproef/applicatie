import queries, os
from dotenv import load_dotenv

load_dotenv()

db_connection_uri = queries.uri(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    dbname=os.getenv('POSTGRES_DB_NAME'),
    user=os.getenv('POSTGRES_USERNAME'),
    password=os.getenv('POSTGRES_PASSWORD')
)

try:
    with queries.Session(db_connection_uri) as session:
        # drop oude tabellen indien ze bestaan
        session.query('drop table if exists analyses')
        session.query('drop table if exists gebruikers')
        session.query('drop table if exists woordenlijst')
        session.query('drop table if exists freq77')
        
        # maak nieuwe tabellen aan
        session.query('''create table gebruikers (
            gebruiker_id                        int primary key generated always as identity,
            email                               varchar(254) not null unique,
            user_gemaakt_op                     timestamp not null,
            laatste_token                       text unique,
            laatste_token_gemaakt_op            timestamp,
            laaste_token_geverifeerd_op         timestamp
        )''')

        session.query('''create table analyses (
            analyse_id                          int primary key generated always as identity,
            is_gestart                          bool not null,
            is_succes                           bool,
            error                               text,
            analyse_gemaakt_op                  timestamp,
            opnameduur                          text,
            
            gebruiker_id                        int not null,
            opname_bestandsnaam                 text not null,

            spraaksnelheid                      numeric(3),
            geluidniveau                        numeric(3),
            toonhoogte                          numeric(3),

            transcriptie                        text,
            methode                             text,

            cilt                                numeric(3),
            woordlengteratio                    numeric(3),
            aantal_verkleinwoorden              int,
            aantal_collectieve_voornaamwoorden  int,
            aantal_bevestigende_tussenwerpsels  int,
            aantal_herhalingen                  int,

            textcat_elderspeak                  numeric(3),

            browser                             text not null,
            os                                  text not null,
            platform                            text not null,
            bezoeker_id                         text not null,
            foreign key(gebruiker_id)           references gebruikers(gebruiker_id)
        )''')

        session.query('create table woordenlijst (woord text not null primary key)')
        session.query('create table freq77 (nummer int primary key generated always as identity, woord text not null)')

        print('tabellen ok')

        # opvullen freq77
        def verwerk_lijst(lijst: str, tabel: str) -> bool:
            with open('woordenlijsten\\' + lijst + '.txt', mode='r', encoding='utf-8') as lijst_bestand:
                woorden = lijst_bestand.readlines()
                for woord in woorden:
                    woord = str(woord.lstrip().rstrip())
                    if woord != '' and woord[0] != '#':
                        session.query('insert into ' + tabel + ' (woord) values (%s) on conflict do nothing', [ woord ])   
            print(lijst + ' ok')

        verwerk_lijst('freq77', 'freq77')

        # opvullen woordenlijst
        verwerk_lijst('voornamen_m', 'woordenlijst')
        verwerk_lijst('voornamen_v', 'woordenlijst')
        verwerk_lijst('plaatsnamen', 'woordenlijst')
        verwerk_lijst('woordenlijst_opentaal', 'woordenlijst')

except Exception as e:
    print(str(e))