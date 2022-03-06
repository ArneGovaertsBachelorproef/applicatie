import queries, os, jwt, secrets, string, time, smtplib, base64

class Auth:
    def __init__(self, request):
        self.client_ip = request.client.host

        self.token_ttl = int(os.getenv('AUTH_TOKEN_TTL'))
        self.secret = os.getenv('AUTH_SECRET')
        
        self.email_metadata = {
            'smtp-server':  os.getenv('AUTH_SMTP_SERVER'),
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
        token = secrets.token_urlsafe(16)

        try:
            with queries.Session(self.db_connection_uri) as session:
                results = session.query('''create table if not exists token_auth (
                    token           char(24) not null unique primary key,
                    email           varchar(254) not null,
                    valid_until     timestamp
                )
                ''')
                if results:
                    results = session.query("insert into token_auth values (%s, %s, now() + INTERVAL '" + str(self.token_ttl) + " min')", [token, email])

                    if results:
                        message = 'From: {}\nSubject: {}\n\nHallo.\n\nJe vroeg een aanmeldlink aan (request van {}).\nGebruik volgende url om aan te melden: http://127.0.0.1:8000/aanmelden?token={}&email={}\n\nTeam ElderSpeaky'.format(
                            self.email_metadata['email'],
                            self.email_metadata['subject'],
                            self.client_ip,
                            token,
                            email
                        )
            
                        server = smtplib.SMTP(self.email_metadata['smtp-server'], self.email_metadata['port'])
                        server.ehlo()
                        server.starttls()
                        server.login(self.email_metadata['username'], self.email_metadata['password'])
                        server.sendmail(self.email_metadata['email'], email, message)
                        server.close()
                        
                        return True
                    else:
                        # error
                        return False
                else:
                    # error
                    return False
        except Exception as e:
            # log error
            print(str(e))
            return False

    def validate_token(self, return_token, return_email = '') -> bool:
        try:
            with queries.Session(self.db_connection_uri) as session:
                results = session.query('select * from token_auth where token = %s and email = %s and valid_until > now()', [return_token, return_email])

                if results:
                    return True
                else:
                    return False
        except Exception as e:
            # log: eror
            return False