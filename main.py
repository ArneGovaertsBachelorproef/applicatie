from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from src.auth import Auth

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount('/static', StaticFiles(directory='dist'), name='dist')
templates = Jinja2Templates(directory='templates')

@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse('landing.html', {'request': request})

@app.get('/aanmelden')
async def login(
        request: Request,
        demo: Optional[bool] = False,
        token: Optional[str] = '',
        email: Optional[str] = '',
        verzonden: Optional[bool] = False,
        error: Optional[bool] = False
    ):
    if demo:
        # set cookie for demo user and redirect
        return RedirectResponse('/dashboard', 303)
    elif token and email:
        auth = Auth(request)
        res = auth.validate_token(token, email)
        # set cookie for user and redirect
        return RedirectResponse('/dashboard', 303)
    elif verzonden:
        return templates.TemplateResponse('auth/send.html', {'request': request, 'error': error})
    else:
        return templates.TemplateResponse('auth/login.html', {'request': request, 'error': error})

@app.post('/aanmelden')
async def do_login(request: Request):
    form = await request.form()
    email = str(form.get('uname') + form.get('mpart'))
    
    auth = Auth(request)
    send = auth.send_token(email)
    return RedirectResponse('/aanmelden?verzonden=true&error=' + str(not send), 303)

@app.get('/dashboard')
async def dashboard(request: Request):
    return templates.TemplateResponse('app/dashboard.html', {'request': request})