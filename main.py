from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount('/static', StaticFiles(directory='dist'), name='dist')
templates = Jinja2Templates(directory='templates')

@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse('landing.html', {'request': request})

@app.get('/dashboard')
async def dashboard(request: Request):
    return templates.TemplateResponse('dashboard.html', {'request': request})