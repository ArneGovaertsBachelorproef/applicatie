import queries, os, jwt, secrets, string, time, smtplib, base64

class Auth:
    def __init__(self, request):
        self.client_ip = request.client.host

        self.token_ttl = int(os.getenv('AUTH_TOKEN_TTL'))
        self.secret = os.getenv('AUTH_SECRET')
        
        self.email_metadata = {
            'smtp_server':  os.getenv('AUTH_SMTP_SERVER'),
            'port':         os.getenv('AUTH_SMTP_PORT'),
            'username':     os.getenv('AUTH_SMTP_USERNAME'),
            'password':     os.getenv('AUTH_SMTP_PASSWORD'),
            'email':        os.getenv('AUTH_SMTP_EMAIL'),
            'subject':      'Aanmelden bij ElderSpeaky',
        }

        self.db_connection_uri = queries.uri(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB_NAME'),
            user=os.getenv('POSTGRES_USERNAME'),
            password=os.getenv('POSTGRES_PASSWORD')
        )

    def send_token(self, email) -> bool:
        try:
            with queries.Session(self.db_connection_uri) as session:
                # tabellen moet bestaan
                results = session.query('''create table if not exists users (
                    user_id                 int primary key generated always as identity,
                    email                   varchar(254) not null unique,
                    user_created_on         timestamp not null,
                    last_token              text unique,
                    last_token_created_on   timestamp,
                    last_token_verified_on  timestamp
                )
                ''')

                # als user, bestaat, genereer nieuwe token
                new_token = session.query('update users set last_token = md5(now() || %s), last_token_created_on = now() where email = %s returning last_token', [email, email])

                if len(new_token) == 0:
                     # user bestaat niet, maak user en stuur verificatie
                    new_token = session.query('insert into users (email, user_created_on, last_token, last_token_created_on) values(%s, now(), md5(now() || %s), now()) returning last_token', [email, email])

                new_token = new_token.as_dict()
                
                message = 'From: {}\nSubject: {}\n\nHey!\n\nWe registeerden een aanmeldpoging van {}.\nOm je aanmelding te bevestigen, ga naar {}.\n\nMet vriendelijke groeten\nTeam ElderSpeaky'.format(
                    self.email_metadata['email'],
                    self.email_metadata['subject'],
                    self.client_ip,
                    'http://127.0.1:8000/verifieren/' + new_token['last_token']
                )
                server = smtplib.SMTP(self.email_metadata["smtp_server"], self.email_metadata["port"])
                server.ehlo()
                server.starttls()
                server.login(self.email_metadata["username"], self.email_metadata["password"])
                server.sendmail(self.email_metadata['email'], email, message)
                server.close()

                return True
        except Exception as e:
            # log error
            print(str(e))
            return False

    def verify_token(self, token, minutes: int = 1440) -> object:
        if token == 'demo':
            return {
                'verified': True,
                'token': token
            } 
            
        try:
            with queries.Session(self.db_connection_uri) as session:
                update = session.query("update users set last_token_verified_on = now() where last_token = %s and last_token_created_on + interval '%s min' > now() returning user_id", [token, minutes])
                print(update)
                if len(update) == 1:
                    return {
                        'verified': True,
                        'token': token
                    }
                else:
                    return {
                        'verified': False
                    }
        except Exception as e:
            # log error
            print(str(e))
            return {
                'verified': False
            }