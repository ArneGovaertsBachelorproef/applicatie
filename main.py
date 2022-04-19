import os as opsys, queries

from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from src.auth import Auth
from hashids import Hashids
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import FastAPI, Request, Cookie, Response, status, File, Form, UploadFile
from src.analyseer import opslaan_audio_bestand, insert_gegevens_in_db, analyse, analyse_resultaat

from huey import RedisHuey
huey = RedisHuey(url='redis://localhost:6379')

app = FastAPI()

app.mount('/static', StaticFiles(directory='dist'), name='dist')
templates = Jinja2Templates(directory='templates')

# ----------------------------------------------------------------------------- #
# Infosite                                                                      #
# ----------------------------------------------------------------------------- #
@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse('landing.html', {'request': request})

# ----------------------------------------------------------------------------- #
# Passwordless inloggen en uitloggen                                            #
# ----------------------------------------------------------------------------- #
@app.get('/aanmelden')
async def login(
        request: Request,
        verzonden: Optional[bool] = False,
        error: Optional[bool] = False,
        _el_au: Optional[str] = Cookie('')
    ):
    auth = Auth(request)

    # check cookie
    if _el_au != '':
        veri = auth.verify_token(_el_au)
        if veri['verified']:
            return RedirectResponse('/app', 303)
    
    if verzonden:
        return templates.TemplateResponse('auth/send.html', {'request': request})
    else:
        return templates.TemplateResponse('auth/login.html', {'request': request, 'error': error})

@app.post('/aanmelden')
async def do_login(request: Request):
    form = await request.form()
    email = str(form.get('uname') + form.get('mpart'))
    
    auth = Auth(request)
    send = auth.send_token(email)
    return RedirectResponse('/aanmelden?verzonden=true&error=' + str(int(not send)), 303)

@app.get('/verifieren/{token}')
async def verifieren(request: Request, token: str):
    auth = Auth(request)
    veri = auth.verify_token(token, 10)

    if veri['verified']:
        resp = RedirectResponse('/app', 303)
        resp.set_cookie('_el_au', veri['token'], max_age=86400, path='/', httponly=True)
        return resp
    else:
        return RedirectResponse('/aanmelden', 303)

@app.get('/uitloggen')
async def uitloggen(request: Request, _el_au: Optional[str] = Cookie('')):
    auth = Auth(request)
    veri = auth.verify_token(_el_au)

    resp = RedirectResponse('/', 303)
    if veri['verified']:
        resp.set_cookie('_el_au', veri['token'], max_age=0, path='/', httponly=True)
    return resp

# ----------------------------------------------------------------------------- #
# App                                                                      #
# ----------------------------------------------------------------------------- #
@app.get('/app')
async def opnemen(request: Request, response: Response, _el_au: Optional[str] = Cookie('')):
    auth = Auth(request)
    veri = auth.verify_token(_el_au)
    
    if not veri['verified']:
        response.status_code = status.HTTP_403_FORBIDDEN
        return RedirectResponse('/aanmelden', 303)
    
    return templates.TemplateResponse('app/record.html', {'request': request})

@app.post('/app', status_code = 201)
async def analyseer(
        request: Request,
        response: Response,
        opname: UploadFile,
        _el_au: Optional[str] = Cookie(''),
        browser: str = Form(''),
        os: str = Form(''),
        platform: str = Form(''),
        bezoeker_id: str = Form(''),
        geslacht: str = Form('X'),
        leeftijd: int = Form(0)
    ):
    auth = Auth(request)
    veri = auth.verify_token(_el_au)

    if not veri['verified']:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {
            'success': False,
            'error': 'not verified' 
        }

    opslaan_bestand = await opslaan_audio_bestand(opname)
    if not opslaan_bestand['success']:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return opslaan_bestand

    insert = insert_gegevens_in_db(gebruiker_id=veri['gebruiker_id'], opname_bestandsnaam=opslaan_bestand['bestands_naam'], browser=browser, operating_system=os, platform=platform, bezoeker_id=bezoeker_id, geslacht=geslacht, leeftijd=leeftijd)
    if not insert['success']:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return insert
    
    analyse(analyse_id=insert['analyse_id'], opname_bestand=opslaan_bestand['bestands_naam'])

    return {
        'success': True,
        'redirect_url': '/app/' + Hashids(salt=opsys.getenv('HASHIDS_SALT')).encode(insert['analyse_id'])
    }

@app.get('/app/{hashid}')
async def resultaat(request: Request, hashid: str, _el_au: Optional[str] = Cookie('')):
    auth = Auth(request)
    veri = auth.verify_token(_el_au)
    
    if not veri['verified']:
        return RedirectResponse('/aanmelden', 303)
    
    analyse_id = Hashids(salt=opsys.getenv('HASHIDS_SALT')).decode(hashid)[0]
    
    return templates.TemplateResponse('app/result.html', {'request': request})

@app.get('/app/{hashid}/json')
async def resultaat_json(request: Request, hashid: str, _el_au: Optional[str] = Cookie('')):
    auth = Auth(request)
    veri = auth.verify_token(_el_au)
    
    if not veri['verified']:
        return RedirectResponse('/aanmelden', 303)
    
    analyse_id = Hashids(salt=opsys.getenv('HASHIDS_SALT')).decode(hashid)[0]

    return analyse_resultaat(analyse_id)