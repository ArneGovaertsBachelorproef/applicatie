from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from src.auth import Auth

from fastapi import FastAPI, Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
# Passwordless inloggen                                                         #
# ----------------------------------------------------------------------------- #
@app.get('/aanmelden')
async def login(
        request: Request,
        demo: Optional[bool] = False,
        verzonden: Optional[bool] = False,
        error: Optional[bool] = False,
        _el_au: Optional[str] = Cookie('')
    ):
    auth = Auth(request)

    # check cookie
    if _el_au != '':
        veri = auth.verify_token(_el_au)
        if veri['verified']:
            return RedirectResponse('/dashboard', 303)
    
    if demo:
        resp = RedirectResponse('/dashboard', 303)
        resp.set_cookie('_el_au', 'demo', path='/', httponly=True)
        return resp
    elif verzonden:
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
        resp = RedirectResponse('/dashboard', 303)
        resp.set_cookie('_el_au', veri['token'], max_age=86400, path='/', httponly=True)
        return resp
    else:
        return RedirectResponse('/aanmelden', 303)

# ----------------------------------------------------------------------------- #
# Dashboard                                                                     #
# ----------------------------------------------------------------------------- #
@app.get('/uitloggen')
async def uitloggen(request: Request, _el_au: Optional[str] = Cookie('')):
    auth = Auth(request)
    veri = auth.verify_token(_el_au)

    resp = RedirectResponse('/', 303)
    if veri['verified']:
        resp.set_cookie('_el_au', veri['token'], max_age=0, path='/', httponly=True)
    return resp

# ----------------------------------------------------------------------------- #
# Dashboard                                                                     #
# ----------------------------------------------------------------------------- #
@app.get('/dashboard')
async def dashboard(request: Request, _el_au: Optional[str] = Cookie('')):
    auth = Auth(request)
    veri = auth.verify_token(_el_au)
    
    if not veri['verified']:
        return RedirectResponse('/aanmelden', 303)
    
    return templates.TemplateResponse('app/dashboard.html', {'request': request})