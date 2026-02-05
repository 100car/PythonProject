# RECIPES

Проєкт для парсингу файлів від продавця та формування вихідних Excel/CSV.

## Структура папок

Очікувана структура на диску (shared словники поруч з проєктами):

C:\AI01
DATA_DICTIONARIES
RECIPES\


## Структура всередині `RECIPES`:
RECIPES/
FROM_SELLER/ # вхідні файли від продавця (не комітимо)
OUT/ # результати парсингу (не комітимо)
LOGS/ # логи запусків (не комітимо)
src/ # python-код
config.yaml # базовий конфіг (комітимо)
requirements.txt
requirements-dev.txt
.gitignore
README.md


## Віртуальне середовище

Проєкт використовує virtualenv в `RECIPES/.venv`.

Активувати (PowerShell, Windows):

```powershell
C:\AI01\RECIPES\.venv\Scripts\Activate.ps1

Встановити залежності:
pip install -r requirements-dev.txt

config.yaml містить шляхи та базові параметри.

Важливе: project.shared_dictionaries_dir вказує на shared-папку словників
на одному рівні з проєктом, за замовчуванням:

project:
  shared_dictionaries_dir: "../DATA_DICTIONARIES"

Запуск (smoke test)

Базовий запуск перевіряє:

створення робочих папок (FROM_SELLER, OUT, LOGS)

логування в LOGS/run.log

тестовий експорт в Excel у OUT/

Запуск:

python -m src.main

Після запуску має з’явитися файл:

OUT/smoke_test_YYYYMMDD_HHMMSS.xlsx


