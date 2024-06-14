from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from typing import Annotated
import sqlite3
import hashlib

# 데이터베이스 연결
con = sqlite3.connect('wsm.db', check_same_thread=False)
cur = con.cursor()

# FastAPI 앱 생성
app = FastAPI()

# 로그인 매니저 설정
SECRET = "super-coding"
manager = LoginManager(SECRET, '/login')

@manager.user_loader()
def query_user(data):
    WHERE_STATEMENT = f'id="{data}"'
    if type(data) == dict:
        WHERE_STATEMENT = f'id="{data["id"]}"'
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    user = cur.execute(f"""
                       SELECT * FROM users WHERE {WHERE_STATEMENT}
                       """).fetchone()
    return user

@app.post('/signup')
def signup(id: Annotated[str, Form()],
           password: Annotated[str, Form()],
           name: Annotated[str, Form()],
           email: Annotated[str, Form()]):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cur.execute(f"""
                INSERT INTO users(id, name, email, password)
                VALUES ('{id}', '{name}', '{email}', '{hashed_password}')
                """)
    con.commit()
    return '200'


@app.post('/login')
def login(id:Annotated[str,Form()],
          password:Annotated[str,Form()]):
    user = query_user(id)
    if not user:
        raise InvalidCredentialsException
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if hashed_password != user['password']:
        raise InvalidCredentialsException
    
    access_token=manager.create_access_token(data={
        'sub':{
        'id':user['id'],
        'name':user['name'],
        'email':user['email']
        }
    })
    
    return {'access_token':access_token}
    return {'access_token': access_token}

# 정적 파일 서빙
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

