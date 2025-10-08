# На екрані тоді кольори, а не esc-послідовності:
from colorama import init
init()


# Завдання 1
# Напишіть сервер для збереження даних про фільми. Дані знаходяться у файлі films.json
# Напишіть модель на pydentic з такими даними:
# ● id
# ● title
# ● director
# ● year
# Функціонал:
# 1. Отримання даних за ID фільму
#   ○ шлях – movies/{movie_id}
#   ○ метод – GET
# 2. Додавання нового фільму
#   ○ шлях – movies
#   ○ метод – POST
# 3. Видалення фільму за ID
#   ○ шлях – movies/{movie_id}
#   ○ метод – DELETE

from fastapi import FastAPI
from pydantic import BaseModel
import json
import os

app = FastAPI()


class Film(BaseModel):
    id: int
    title: str
    director: str
    year: int


def load_films(filename: str = 'films.json'):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def save_films(films: dict, filename: str = 'films.json'):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(films, file, indent=4, ensure_ascii=False)


# 1. Отримання даних за ID фільму
@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    films = load_films()
    movie_id_str = str(movie_id)
    if movie_id_str in films:
        return {"status": "ok", "film": films[movie_id_str]}
    else:
        return {"status": "error", "message": "Фільм не знайдено"}


# 2. Додавання нового фільму
@app.post("/movies")
def add_movie(film: Film):
    films = load_films()
    movie_id_str = str(film.id)
    if movie_id_str in films:
        return {"status": "error", "message": "Фільм із таким ID вже існує"}

    film_data = {
        "id": film.id,
        "title": film.title,
        "director": film.director,
        "year": film.year
    }

    films[movie_id_str] = film_data
    save_films(films)
    return {"status": "ok", "message": "Фільм додано успішно", "film": film_data}


# 3. Видалення фільму
@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):
    films = load_films()
    movie_id_str = str(movie_id)
    if movie_id_str not in films:
        return {"status": "error", "message": "Фільм не знайдено"}
    deleted_film = films.pop(movie_id_str)
    save_films(films)
    return {"status": "ok", "message": "Фільм видалено успішно", "film": deleted_film}



# @app.post('/message')
# def message():
#     print("виклик функції message")
#
#
# @app.post('/function')
# def func():
#     print("виклик функції func")
#
# @app.post('/data')
# def get_data():
#     return {"result": "Привіт від сервера"}

# @app.post("/mult2/{num}")
# def mult2(num: int):
#     return {"result": 2*num}
#
# # функція для реєстрації користувачів
# # отримує щось типу
# {
#     'user_name': 'Jhon',
#     "login": "jhon45678",
#     'password': '123qwer',
#     'age': 45
# }
#
# from pydantic import BaseModel
#
# class UserData(BaseModel):
#     user_name: str
#     login: str
#     password: str
#     age: int
#
# @app.post("/register")
# def register_user(user: UserData):
#     print(user)
#     results = {
#         "results": "Дані отримані",
#         "user_data": user
#     }
#     return results



