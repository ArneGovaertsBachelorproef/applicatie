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
        session.query('drop table if exists analyses')
        session.query('drop table if exists gebruikers')
        
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
            
            geslacht                            char(1) not null,
            leeftijd                            int not null,
            gebruiker_id                        int not null,
            opname_bestandsnaam                 text not null,

            spraaksnelheid                      numeric(3),
            geluidniveau                        numeric(3),
            toonhoogte                          numeric(3),

            transcriptie                        text,
            methode                             text,
            cilt                                numeric(3),
            woordlengteratio                    numeric(3),
            aantal_collectieve_voornaamwoorden  int,
            aantal_bevestigende_tussenwerpsels  int,

            browser                             text not null,
            os                                  text not null,
            platform                            text not null,
            bezoeker_id                         text not null,
            foreign key(gebruiker_id)           references gebruikers(gebruiker_id)
        )''') # aantal_verkleinwoorden en herhalingen nog toevoegen!!

except Exception as e:
    print(str(e))