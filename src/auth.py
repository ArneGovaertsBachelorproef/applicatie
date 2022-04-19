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
                # als user, bestaat, genereer nieuwe token
                new_token = session.query('update gebruikers set laatste_token = md5(now() || %s), laatste_token_gemaakt_op = now() where email = %s returning laatste_token', [email, email])

                if len(new_token) == 0:
                     # user bestaat niet, maak user en stuur verificatie
                    new_token = session.query('insert into gebruikers (email, user_gemaakt_op, laatste_token, laatste_token_gemaakt_op) values(%s, now(), md5(now() || %s), now()) returning laatste_token', [email, email])

                new_token = new_token.as_dict()
                
                message = 'From: {}\nSubject: {}\n\nHey!\n\nWe registeerden een aanmeldpoging van {}.\nOm je aanmelding te bevestigen, ga naar {}.\n\nMet vriendelijke groeten\nTeam ElderSpeaky'.format(
                    self.email_metadata['email'],
                    self.email_metadata['subject'],
                    self.client_ip,
                    'http://127.0.1:8000/verifieren/' + new_token['laatste_token']
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
        try:
            with queries.Session(self.db_connection_uri) as session:
                update = session.query("update gebruikers set laaste_token_geverifeerd_op = now() where laatste_token = %s and laatste_token_gemaakt_op + interval '%s min' > now() returning gebruiker_id", [token, minutes])

                if len(update) == 1:
                    update = update.as_dict()

                    return {
                        'verified': True,
                        'token': token,
                        'gebruiker_id': update['gebruiker_id']
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