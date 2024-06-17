import logging
import sqlite3
from fastapi import FastAPI, Form, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from typing import Annotated
import hashlib
from fastapi.middleware.cors import CORSMiddleware
import random

logging.basicConfig(level=logging.INFO)

# 데이터베이스 연결
def create_connection():
    try:
        conn = sqlite3.connect('wsm.db', check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        raise

conn = create_connection()
cur = conn.cursor()

# 데이터베이스 초기화
def initialize_database():
    try:
        with conn:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS word_searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    words TEXT NOT NULL,
                    grid TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    points INTEGER NOT NULL,
                    time_elapsed INTEGER NOT NULL,
                    FOREIGN KEY (game_id) REFERENCES word_searches (id)
                );
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    password TEXT NOT NULL
                );
            ''')
    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")
        raise

initialize_database()

# FastAPI 앱 생성
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로그인 매니저 설정
SECRET = "super-coding"
manager = LoginManager(SECRET, '/login')

def generate_word_search(words):
    size = 10
    grid = [[' ' for _ in range(size)] for _ in range(size)]
    
    for word in words:
        placed = False
        while not placed:
            direction = random.choice(['horizontal', 'vertical'])
            if direction == 'horizontal':
                row = random.randint(0, size - 1)
                col = random.randint(0, size - len(word))
                if all(grid[row][col+i] in (' ', letter) for i, letter in enumerate(word)):
                    for i, letter in enumerate(word):
                        grid[row][col+i] = letter
                    placed = True
            else:
                row = random.randint(0, size - len(word))
                col = random.randint(0, size - 1)
                if all(grid[row+i][col] in (' ', letter) for i, letter in enumerate(word)):
                    for i, letter in enumerate(word):
                        grid[row+i][col] = letter
                    placed = True

    for row in range(size):
        for col in range(size):
            if grid[row][col] == ' ':
                grid[row][col] = chr(random.randint(65, 90))
    
    return grid

@app.post("/generate")
async def generate(request: Request):
    try:
        data = await request.json()
        title = data.get("title")
        description = data.get("description")
        words = data.get("words", [])
        if not title or not description or not words:
            raise ValueError("Missing required fields")

        grid = generate_word_search(words)

        conn = create_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO word_searches (title, description, words, grid) VALUES (?, ?, ?, ?)',
                (title, description, ",".join(words), str(grid))
            )
            game_id = cursor.lastrowid

        return {"gameId": game_id, "grid": grid}
    except Exception as e:
        logging.error(f"Error in /generate: {e}, Data received: {data}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/game/{game_id}")
async def get_game(game_id: int):
    try:
        conn = create_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute('SELECT title, description, words, grid FROM word_searches WHERE id = ?', (game_id,))
            row = cursor.fetchone()
            if row:
                title, description, words, grid = row
                return {"title": title, "description": description, "words": words.split(','), "grid": eval(grid)}
            return {"error": "Game not found"}
    except Exception as e:
        logging.error(f"Error in /game/{game_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/score")
async def post_score(request: Request):
    try:
        data = await request.json()
        game_id = data.get("gameId")
        username = data.get("username")
        points = data.get("points")
        time_elapsed = data.get("timeElapsed")

        conn = create_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO scores (game_id, username, points, time_elapsed) VALUES (?, ?, ?, ?)',
                (game_id, username, points, time_elapsed)
            )
        return {"status": "Score submitted"}
    except Exception as e:
        logging.error(f"Error in /score: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@manager.user_loader()
def query_user(data):
    WHERE_STATEMENT = f'id="{data}"'
    if isinstance(data, dict):
        WHERE_STATEMENT = f'id="{data["id"]}"'
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    user = cur.execute(f"""
                       SELECT * FROM users WHERE {WHERE_STATEMENT}
                       """).fetchone()
    return user

@app.post('/signup')
def signup(id: Annotated[str, Form()],
           password: Annotated[str, Form()],
           name: Annotated[str, Form()],
           email: Annotated[str, Form()]):
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cur.execute(f"""
                    INSERT INTO users(id, name, email, password)
                    VALUES (?, ?, ?, ?)
                    """, (id, name, email, hashed_password))
        conn.commit()
        return '200'
    except Exception as e:
        logging.error(f"Error in /signup: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post('/login')
def login(id: Annotated[str, Form()],
          password: Annotated[str, Form()]):
    try:
        user = query_user(id)
        if not user:
            raise InvalidCredentialsException
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if hashed_password != user['password']:
            raise InvalidCredentialsException

        access_token = manager.create_access_token(data={
            'sub': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email']
            }
        })

        return {'access_token': access_token}
    except Exception as e:
        logging.error(f"Error in /login: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 정적 파일 서빙
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
