# Завдання 1
# Напишіть програму, яка приймає два цілих числа від користувача
# і виводить суму діапазону чисел між ними (включно).

# def calculate_range_sum() -> None:
#     try:
#         a = int(input("Перше ціле число: "))
#         b = int(input("Друге ціле число: "))
#     except ValueError:
#         print("Помилка: потрібно вводити саме цілі числа.")
#         return
#
#     start, end = sorted((a, b)) # Визначення початку і кінця діапазону
#     n = end - start + 1 # Кількість чисел у діапазоні
#     total = n * (start + end) // 2 # Використання формули суми арифметичної прогресії
#
#     print(f"Сума від {start} до {end} дорівнює {total}")
#
#
# if __name__ == "__main__":
#     calculate_range_sum()

# 2. Напишіть програму, для знаходження суми всіх парних чисел від 1 до 100.
# def sum_even_numbers() -> None:
#     total = sum(i for i in range(1, 101) if i % 2 == 0)
#     print(f"Сума всіх парних чисел від 1 до 100 дорівнює {total}")
#
#
# sum_even_numbers()

# 3 Напишіть програму, яка приймає рядок від користувача і виводить кожну літеру рядка на окремому рядку.
# def print_characters() -> None:
#     user_input = input("Введіть рядок: ")
#     for char in user_input:
#         print(char)
#
#
# print_characters()

# 4. Напишіть програму, яка створює список цілих чисел та виводить новий список, який містить лише парні числа з
# вихідного списку.
# def filter_even_numbers() -> None:
#     numbers = [12, 7, 5, 64, 14, 23, 8, 19, 42]
#     even_numbers = [num for num in numbers if num % 2 == 0] # Створення нового списку з парними числами - той же неможна!!!!
#     print(f"Парні числа з вихідного списку: {even_numbers}")
#
#
# filter_even_numbers()

# 5. Напишіть функцію, яка приймає список рядків від користувача і повертає новий список, що містить лише
# рядки, що починаються з великої літери.
# def filter_capitalized_strings() -> None:
#     user_input = input("Введіть рядки, розділені комами: ")
#     strings = [s.strip() for s in user_input.split(",")]
#     capitalized_strings = [s for s in strings if s and s[0].isupper()] # Перевірка на порожній рядок
#     print(f"Рядки, що починаються з великої літери: {capitalized_strings}")
#
#
# filter_capitalized_strings()

# 6. Напишіть функцію, яка приймає список рядків від користувача і повертає новий список, що містить лише
# рядки, які містять слово "Python".
# def filter_python_strings() -> None:
#     user_input = input("Введіть рядки, розділені комами: ")
#     strings = [s.strip() for s in user_input.split(",")]
#     python_strings = [s for s in strings if "Python" in s]
#     print(f'Рядки, які містять слово "Python": {python_strings}')
#
#
# filter_python_strings()


# Завдання 7 (додаткове на кристалики)
# Напишіть програму, яка створює словник (глосарій), де ключами є слова,
# а значеннями — їхні визначення. Дозвольте користувачу додавати,
# видаляти та шукати слова у цьому словнику.

# def build_glossary() -> None:
#     """Інтерактивна програма для роботи зі словником термінів Python."""
#
#     # glossary: dict[str, str] = {}  # порожній словник — нецікаво :)
#     glossary: dict[str, str] = {
#         "Python": "Мова програмування високого рівня.",
#         "Algorithm": "Послідовність дій для розв’язання задачі.",
#         "Variable": "Ім’я, що зберігає певне значення.",
#         "Function": "Блок коду, який виконує певну задачу.",
#         "Loop": "Конструкція для багаторазового виконання дій.",
#         "List": "Змінна структура даних для зберігання елементів.",
#         "Dictionary": "Колекція пар ключ-значення.",
#         "Class": "Шаблон для створення об’єктів в ООП.",
#         "Object": "Екземпляр класу з власними атрибутами та методами.",
#         "Module": "Файл з кодом Python, який можна імпортувати в програму."
#     }
#
#     menu = (
#         "Меню:\n"
#         "1 — Додати/оновити слово\n"
#         "2 — Видалити слово\n"
#         "3 — Знайти слово\n"
#         "4 — Показати всі слова\n"
#         "0 — Вийти\n"
#     )
#
#     while True:
#         print(menu)
#         choice = input("Ваш вибір: ").strip()
#
#         if choice == "1":
#             word = input("Слово: ").strip()
#             definition = input("Визначення: ").strip()
#             glossary[word] = definition
#             print("Збережено.\n")
#
#         elif choice == "2":
#             word = input("Слово для видалення: ").strip()
#             removed = glossary.pop(word, None)
#             if removed is None:
#                 print("Немає такого слова.\n")
#             else:
#                 print("Видалено.\n")
#
#         elif choice == "3":
#             word = input("Слово для пошуку: ").strip()
#             definition = glossary.get(word)
#             if definition:
#                 print(f"{word}: {definition}\n")
#             else:
#                 print("Не знайдено.\n")
#
#         elif choice == "4":
#             if not glossary:
#                 print("Глосарій порожній.\n")
#             else:
#                 print("\nПоточний глосарій:")
#                 for w, d in sorted(glossary.items()):
#                     print(f"  • {w}: {d}")
#                 print()
#
#         elif choice == "0":
#             print("Готово. До побачення!")
#             break
#
#         else:
#             print("Невірний вибір. Спробуйте ще.\n")
#
#
# build_glossary()

# Частина 2: Об'єктно-орієнтоване програмування (ООП)
# Симулятор роботи сайту
# WebSite: Основний клас, який представляє вебсайт.
#   Атрибути: назва сайту, URL, список сторінок.
#   Методи: додавання/видалення сторінок, відображення інформації про сайт.
# WebPage: Клас, який представляє окрему сторінку на сайті.
#   Атрибути: заголовок сторінки, вміст, дата публікації.
#   Методи: відображення деталей сторінки.

# Реалізація функціональності:
# Дозвольте користувачеві створювати новий сайт з  певною назвою та URL. Додайте можливість створювати нові
# сторінки для сайту, вводячи заголовок та вміст. Реалізуйте функцію для видалення сторінок з сайту. Включіть функцію
# для відображення всієї інформації про сайт, включаючи список усіх сторінок.

# Розробіть простий текстовий інтерфейс для взаємодії з користувачем. Користувач повинен мати змогу вибирати дії,
# такі як:
# створення сайту,
# додавання/видалення сторінок,
# перегляд інформації про сайт.

# Реалізуйте систему логіну/реєстрації для керування
# сайтом. Додайте можливість редагування існуючих сторінок.
# Створіть функціонал для пошуку сторінок за ключовими
# словами у заголовку або вмісті.
# from datetime import datetime
#
#
# class WebPage:
#     """Клас, що представляє окрему сторінку сайту."""
#
#     def __init__(self, title: str, content: str):
#         self.title = title
#         self.content = content
#         self.date = datetime.now()
#
#     def show(self) -> None:
#         print(f"\nЗаголовок: {self.title}")
#         print(f"Дата публікації: {self.date.strftime('%Y-%m-%d %H:%M')}")
#         print("Вміст:")
#         print(self.content)
#         print("-" * 40)
#
#
# class WebSite:
#     """Клас, що представляє вебсайт."""
#
#     def __init__(self, name: str, url: str):
#         self.name = name
#         self.url = url
#         self.pages = []
#
#     def add_page(self, page: WebPage) -> None:
#         self.pages.append(page)
#         print("!!! Сторінку додано !!!")
#
#     def remove_page(self, title: str) -> None:
#         for page in self.pages:
#             if page.title == title:
#                 self.pages.remove(page)
#                 print("!!!!️  Сторінку видалено. !!!!")
#                 return
#         print("!!! Сторінку не знайдено !!!")
#
#     def edit_page(self, title: str, new_title: str = "", new_content: str = "") -> None:
#         for page in self.pages:
#             if page.title == title:
#                 if new_title:
#                     page.title = new_title
#                 if new_content:
#                     page.content = new_content
#                 print("!!! Сторінку оновлено. !!!")
#                 return
#         print("!!! Сторінку не знайдено. !!!")
#
#     def show_info(self) -> None:
#         print(f"\nСайт: {self.name}")
#         print(f"URL: {self.url}")
#         if not self.pages:
#             print("Сайт не має сторінок.")
#         else:
#             print("Список сторінок:")
#             for i, page in enumerate(self.pages, 1):
#                 print(f" {i}. {page.title} ({page.date.strftime('%Y-%m-%d')})")
#         print("-" * 40)
#
#     def search(self, keyword: str) -> None:
#         results = [
#             page for page in self.pages
#             if keyword.lower() in page.title.lower() or keyword.lower() in page.content.lower()
#         ]
#         if results:
#             print(f"\n🔍 Знайдено сторінок: {len(results)}")
#             for page in results:
#                 print(f"- {page.title}")
#         else:
#             print("Нічого не знайдено.")
#
#
# class AuthSystem:
#     """Проста система реєстрації/логіну користувачів."""
#
#     def __init__(self):
#         self.users = {}
#         self.current_user = None
#
#     def register(self, username: str, password: str) -> None:
#         if username in self.users:
#             print("Такий користувач уже існує.")
#         else:
#             self.users[username] = password
#             print("Реєстрація успішна.")
#
#     def login(self, username: str, password: str) -> None:
#         if self.users.get(username) == password:
#             self.current_user = username
#             print(f"Вітаємо, {username}!")
#         else:
#             print("Невірний логін або пароль.")
#
#     def logout(self) -> None:
#         self.current_user = None
#         print("Вихід виконано.")
#
#
# def main():
#     auth = AuthSystem()
#     site = None
#
#     while True:
#         print(
#             "\n=== МЕНЮ ===\n"
#             "1 — Реєстрація\n"
#             "2 — Вхід\n"
#             "3 — Вихід з акаунта\n"
#             "4 — Створити сайт\n"
#             "5 — Додати сторінку\n"
#             "6 — Видалити сторінку\n"
#             "7 — Редагувати сторінку\n"
#             "8 — Пошук сторінок\n"
#             "9 — Показати інформацію про сайт\n"
#             "10 — Переглянути сторінку\n"
#             "0 — Вийти\n"
#         )
#
#         choice = input("Ваш вибір: ").strip()
#
#         if choice == "1":
#             user = input("Логін: ")
#             password = input("Пароль: ")
#             auth.register(user, password)
#
#         elif choice == "2":
#             user = input("Логін: ")
#             password = input("Пароль: ")
#             auth.login(user, password)
#
#         elif choice == "3":
#             auth.logout()
#
#         elif choice == "4":
#             if not auth.current_user:
#                 print("Спочатку увійдіть у систему.")
#                 continue
#             name = input("Назва сайту: ")
#             url = input("URL сайту: ")
#             site = WebSite(name, url)
#             print("Сайт створено.")
#
#         elif choice == "5":
#             if not site:
#                 print("Спочатку створіть сайт.")
#                 continue
#             title = input("Заголовок сторінки: ")
#             content = input("Вміст сторінки: ")
#             site.add_page(WebPage(title, content))
#
#         elif choice == "6":
#             if not site:
#                 print("Сайт ще не створено.")
#                 continue
#             title = input("Заголовок сторінки для видалення: ")
#             site.remove_page(title)
#
#         elif choice == "7":
#             if not site:
#                 print("Сайт ще не створено.")
#                 continue
#             title = input("Заголовок сторінки для редагування: ")
#             new_title = input("Новий заголовок (або Enter): ")
#             new_content = input("Новий вміст (або Enter): ")
#             site.edit_page(title, new_title, new_content)
#
#         elif choice == "8":
#             if not site:
#                 print("Сайт ще не створено.")
#                 continue
#             keyword = input("Ключове слово для пошуку: ")
#             site.search(keyword)
#
#         elif choice == "9":
#             if not site:
#                 print("Сайт ще не створено.")
#                 continue
#             site.show_info()
#
#         elif choice == "10":
#             if not site or not site.pages:
#                 print("Немає сторінок для перегляду.")
#                 continue
#             title = input("Введіть заголовок сторінки: ")
#             found = [p for p in site.pages if p.title == title]
#             if found:
#                 found[0].show()
#             else:
#                 print("Сторінку не знайдено.")
#
#         elif choice == "0":
#             print("Програму завершено.")
#             break
#
#         else:
#             print("Невірний вибір. Спробуйте ще.")
#
#
# if __name__ == '__main__':
#     main()

# 8. Використовуючи лямбдафункцію, напишіть вираз, який сортує список кортежів
# за другим елементом кожного кортежу (наприклад, [(1,3), (3, 2), (2, 1)]).

# tuples = [(1, 3), (3, 2), (2, 1)] # Список кортежів для сортування з умови
# sorted_tuples = sorted(tuples, key=lambda x: x[1]) # Сортування за другим елементом кортежу
# print(sorted_tuples) # Виведення відсортованого списку кортежів




