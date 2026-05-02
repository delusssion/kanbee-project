from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / '.env')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import storage
from routers import auth, boards, settings, tasks

ROOT_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.init_db()
    yield


app = FastAPI(title='KanBee API', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['null'],
    allow_origin_regex=r'^https?://(www\.)?kanbee\.ru$|^http://localhost(:\d+)?$',
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health():
    return {'status': 'ok'}


app.mount('/css', StaticFiles(directory=ROOT_DIR / 'css'), name='css')
app.mount('/js', StaticFiles(directory=ROOT_DIR / 'js'), name='js')
app.mount('/img', StaticFiles(directory=ROOT_DIR / 'img'), name='img')


@app.get('/')
def index_page():
    return FileResponse(ROOT_DIR / 'index.html')


@app.get('/board')
def board_page():
    return FileResponse(ROOT_DIR / 'board.html')


@app.get('/registration')
def registration_page():
    return FileResponse(ROOT_DIR / 'registration.html')


@app.get('/reset-password')
def reset_password_page():
    return FileResponse(ROOT_DIR / 'reset-password.html')


app.include_router(auth.router)
app.include_router(boards.router)
app.include_router(tasks.router)
app.include_router(settings.router)
