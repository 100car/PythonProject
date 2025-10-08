import requests


def get_movie():
    movie_id = input("Введіть ID фільму: ").strip()
    if not movie_id.isdigit():
        print("Помилка: ID повинен бути числом!!!")
        return
    result = requests.get(f"http://localhost:8000/movies/{movie_id}")
    data = result.json()
    if data["status"] == "ok":
        film = data["film"]
        print(f"\nФільм знайдено:\nID: {film['id']}\nНазва: {film['title']}\nРежисер: {film['director']}\nРік: {film['year']}")
    else:
        print("\nПомилка:", data["message"])


def add_movie():
    movie_id = input("ID фільму: ").strip()
    title = input("Назва: ").strip()
    director = input("Режисер: ").strip()
    year = input("Рік: ").strip()

    if not movie_id.isdigit() or not year.isdigit():
        print("Помилка: ID та Рік повинні бути числами!")
        return

    film_data = {
        "id": int(movie_id),
        "title": title,
        "director": director,
        "year": int(year)
    }

    result = requests.post("http://localhost:8000/movies", json=film_data)
    data = result.json()
    if data["status"] == "ok":
        print("\nФільм додано успішно!")
    else:
        print("\nПомилка:", data["message"])


def delete_movie():
    movie_id = input("Введіть ID фільму для видалення: ").strip()
    if not movie_id.isdigit():
        print("Помилка: ID повинен бути числом!")
        return

    result = requests.delete(f"http://localhost:8000/movies/{movie_id}")
    data = result.json()
    if data["status"] == "ok":
        print("\nФільм видалено успішно!")
    else:
        print("\nПомилка:", data["message"])


def main():
    while True:
        print("\nВиберіть, будь ласка, один з варіантів:")
        print("0. Вийти")
        print("1. Отримати дані про фільм")
        print("2. Додати новий фільм")
        print("3. Видалити фільм")
        choice = input("Ваш вибір: ").strip()

        if choice == "1":
            get_movie()
        elif choice == "2":
            add_movie()
        elif choice == "3":
            delete_movie()
        elif choice == "0":
            print("До побачення!")
            break
        else:
            print("Неправильний вибір!")

if __name__ == "__main__":
    main()

#
# response = requests.post("http://localhost:8000/message")
# print(response.status_code)
#
# requests.post("http://localhost:8000/function")

# num = 24
# response = requests.post(f"http://localhost:8000/mult2/{num}")
#
# if response.ok:
#     data = response.json()
#     print(data)
# else:
#     print(response.text)

# передача параметрів як JSON
# user_data = {
#     'user_name': 'Jhon',
#     "login": "jhon45678",
#     'password': '123qwer',
#     'age': 45
# }
#
# # запит на сервер
# response = requests.post(f"http://localhost:8000/register", json=user_data)
#
# if response.ok:
#     result = response.json()
#     print(result)
# else:
#     print(response.text)



