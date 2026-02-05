"""
Скрипт очищення Excel-звітів (пакування/палети) з папки UPDATES.

Структура папок проєкту
-----------------------
UPDATES/
  ACTIVE_REPORTS/        (вхідні файли .xlsx)
  PROCESSED_REPORTS/     (вихідні "очищені" файли)
  FAILED_REPORTS/        (файли, які не вдалося обробити)
  LOGS/                  (детальні логи виконання)

Ключові можливості
------------------
1) Пошук рядка заголовків (header row) у верхній частині листа.
2) Пошук колонок: Symbol, Netto, Brutto, Total (Total НЕ є обов'язковим).
3) Пошук "палетних" колонок між Brutto і Total (або, якщо Total відсутній, до кінця таблиці),
   при цьому приховані стовпчики спочатку відображаються (unhide), а потім враховуються.
4) Створення нового файлу з підмножиною колонок: Symbol, Netto, Brutto, pallet_cols..., TOTAL
   де TOTAL = сума числових значень у pallet_cols (кількість одиниць товару по Symbol).
5) Якщо у вхідному файлі є колонка Total – порівнюємо її з обчисленим TOTAL і підсвічуємо рядки з mismatch.
6) Рядки, де Symbol порожній, не переносяться у вихідний файл.

Вимоги
------
- Python 3.10+
- openpyxl

Примітка
--------
Лог у консоль — компактний (1 рядок на файл).
Детальний лог — у UPDATES/LOGS/excel_cleaner.log
"""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import openpyxl
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook

# =============================================================================
# ПАПКИ ПРОЄКТУ
# =============================================================================
UPDATES_ROOT_DIR = "UPDATES"
ACTIVE_REPORTS_DIR = os.path.join(UPDATES_ROOT_DIR, "ACTIVE_REPORTS")
PROCESSED_REPORTS_DIR = os.path.join(UPDATES_ROOT_DIR, "PROCESSED_REPORTS")
FAILED_REPORTS_DIR = os.path.join(UPDATES_ROOT_DIR, "FAILED_REPORTS")
LOGS_DIR = os.path.join(UPDATES_ROOT_DIR, "LOGS")
LOG_FILE = os.path.join(LOGS_DIR, "excel_cleaner.log")

# =============================================================================
# НАЛАШТУВАННЯ ОБРОБКИ
# =============================================================================
PREFERRED_SHEET_NAME = "Arkusz1"  # якщо нема — береться перший лист
HEADER_SCAN_LIMIT = 40            # скільки верхніх рядків перевіряємо як кандидатів на заголовки
MAX_COLS_SCAN = 120               # скільки колонок скануємо у заголовку
TOL = 1e-6                        # допуск для порівняння чисел

# Підсвітка для рядків з mismatch (коли є оригінальний Total, але він не дорівнює сумі pallet_cols)
FILL_RED = PatternFill("solid", fgColor="FFC7CE")


# =============================================================================
# СИНОНІМИ НАЗВ КОЛОНОК (пошук через "містить")
# =============================================================================
SYMBOL_NAMES = {
    "symbol", "артикул", "арт", "арт.", "кат номер", "кат. номер", "кат.номер",
    "каталоговый номер", "каталожный номер", "код товара", "код", "sku",
    "item", "item no", "item number"
}
NETTO_NAMES = {"waga netto", "netto", "вага нетто", "вес нетто", "net weight", "waga netto kg", "waga netto [kg]"}
BRUTTO_NAMES = {"waga brutto", "brutto", "вага брутто", "вес брутто", "gross weight", "waga brutto kg", "waga brutto [kg]"}
TOTAL_NAMES = {"total", "всього", "всего", "итого", "разом", "sum", "suma", "grand total", "suma razem"}

REQUIRED_NON_TOTAL = SYMBOL_NAMES | NETTO_NAMES | BRUTTO_NAMES


# =============================================================================
# ЛОГЕР
# =============================================================================
def setup_logger() -> logging.Logger:
    """
    Створює логер, який пише детальний лог у файл UPDATES/LOGS/excel_cleaner.log
    """
    os.makedirs(LOGS_DIR, exist_ok=True)

    logger = logging.getLogger("excel_cleaner")
    logger.setLevel(logging.DEBUG)

    # Щоб не дублювати handlers при повторному запуску з IDE
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


LOGGER = setup_logger()


# =============================================================================
# ДОПОМІЖНІ ФУНКЦІЇ
# =============================================================================
def ensure_dirs() -> None:
    """Створює всі потрібні папки, якщо їх немає."""
    os.makedirs(ACTIVE_REPORTS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_REPORTS_DIR, exist_ok=True)
    os.makedirs(FAILED_REPORTS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)


def norm(value: object) -> str:
    """
    Нормалізує текст:
    - None -> ""
    - прибирає NBSP
    - стискає пробіли
    - обрізає по краях
    """
    if value is None:
        return ""
    return " ".join(str(value).replace("\u00a0", " ").split()).strip()


def norm_lower(value: object) -> str:
    """Нормалізує та приводить до нижнього регістру для порівнянь."""
    return norm(value).lower()


def pick_sheet_name(wb: openpyxl.Workbook) -> str:
    """Обирає лист: Arkusz1, якщо існує; інакше — перший лист у книзі."""
    return PREFERRED_SHEET_NAME if PREFERRED_SHEET_NAME in wb.sheetnames else wb.sheetnames[0]


def unmerge_all(ws: openpyxl.worksheet.worksheet.Worksheet) -> None:
    """
    Розмерджує всі merged-комірки і копіює значення верхньої-лівої комірки на весь діапазон.
    Це спрощує пошук заголовків і читання даних.
    """
    for merged in list(ws.merged_cells.ranges):
        min_r, min_c, max_r, max_c = merged.bounds
        value = ws.cell(min_r, min_c).value
        ws.unmerge_cells(str(merged))
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                ws.cell(r, c).value = value


def unhide_all_columns(ws: openpyxl.worksheet.worksheet.Worksheet, max_cols: int = 300) -> None:
    """
    Відображає (unhide) всі стовпчики, щоб приховані колонки теж брали участь у пошуку і обчисленнях.
    """
    max_col = min(ws.max_column, max_cols)
    for c in range(1, max_col + 1):
        letter = get_column_letter(c)
        ws.column_dimensions[letter].hidden = False


def build_header_map(
    ws: openpyxl.worksheet.worksheet.Worksheet,
    header_row: int,
    max_cols_scan: int = MAX_COLS_SCAN,
) -> Dict[int, str]:
    """
    Повертає мапу заголовків {col_idx: normalized_header}.
    Беремо лише непорожні заголовки.
    """
    header_map: Dict[int, str] = {}
    max_col = min(ws.max_column, max_cols_scan)
    for c in range(1, max_col + 1):
        txt = norm(ws.cell(header_row, c).value)
        if txt:
            header_map[c] = txt
    return header_map


def header_contains_any(header: str, keys: Sequence[str]) -> bool:
    """
    Перевіряє, чи заголовок містить хоча б один ключ (substring).
    Ключі і заголовок порівнюються у нижньому регістрі.
    """
    h = header.lower()
    return any(k in h for k in keys)


def find_first_contains(header_map: Dict[int, str], keys: Sequence[str]) -> Optional[int]:
    """
    Повертає першу колонку, де заголовок містить будь-який ключ із keys.
    Якщо не знайдено — None.
    """
    for c, h in header_map.items():
        if header_contains_any(h, keys):
            return c
    return None


def safe_copy_to_failed(path: str) -> str:
    """Копіює файл у FAILED_REPORTS і повертає шлях призначення."""
    dst = os.path.join(FAILED_REPORTS_DIR, os.path.basename(path))
    shutil.copy2(path, dst)
    return dst


def as_float(value: object) -> Optional[float]:
    """
    Перетворює значення в float, якщо це число (int/float).
    Якщо це не число — повертає None.
    """
    if isinstance(value, (int, float)):
        return float(value)
    return None


def is_row_hidden(ws: openpyxl.worksheet.worksheet.Worksheet, row_idx: int) -> bool:
    """True, якщо рядок прихований."""
    return bool(ws.row_dimensions[row_idx].hidden)


# =============================================================================
# ПОШУК HEADER ROW
# =============================================================================
def score_header_row(header_map: Dict[int, str]) -> float:
    """
    Оцінює, наскільки рядок схожий на заголовки потрібної таблиці.

    Бали:
    - знайшли Symbol: +10
    - знайшли Netto: +5
    - знайшли Brutto: +5
    - знайшли Total: +2 (не обов'язково, але корисно)
    - багато непорожніх заголовків: + (len/10)
    """
    if not header_map:
        return -1.0

    sym = find_first_contains(header_map, SYMBOL_NAMES) is not None
    net = find_first_contains(header_map, NETTO_NAMES) is not None
    bru = find_first_contains(header_map, BRUTTO_NAMES) is not None
    tot = find_first_contains(header_map, TOTAL_NAMES) is not None

    score = 0.0
    score += 10.0 if sym else 0.0
    score += 5.0 if net else 0.0
    score += 5.0 if bru else 0.0
    score += 2.0 if tot else 0.0
    score += min(3.0, len(header_map) / 10.0)

    return score


def find_header_row(ws: openpyxl.worksheet.worksheet.Worksheet) -> int:
    """
    Шукає рядок заголовків у верхній частині таблиці за максимальним score.
    """
    best_row = 1
    best_score = -1.0

    max_row = min(ws.max_row, HEADER_SCAN_LIMIT)
    for r in range(1, max_row + 1):
        hm = build_header_map(ws, r)
        sc = score_header_row(hm)
        if sc > best_score:
            best_score = sc
            best_row = r

    # Поріг: хоча б Symbol + Netto + Brutto
    if best_score < 18.0:
        raise ValueError("Не вдалося надійно знайти рядок заголовків (низький score).")

    return best_row


# =============================================================================
# ДЕТЕКЦІЯ КОЛОНОК ТА ПАЛЕТНИХ КОЛОНОК
# =============================================================================
@dataclass(frozen=True)
class ColumnsDetection:
    """Результат розпізнавання структури колонок у файлі."""
    sheet_name: str
    header_row: int
    col_symbol: int
    col_netto: int
    col_brutto: int
    col_total: Optional[int]          # може бути None
    pallet_cols: List[int]            # колонки-осередки (кількість по палетах/боксах)


def detect_columns(
    ws_struct: openpyxl.worksheet.worksheet.Worksheet,
) -> ColumnsDetection:
    """
    Визначає рядок заголовків і ключові колонки.

    Total НЕ є обов'язковим:
    - Якщо Total знайдений, палетні колонки шукаються між Brutto і Total.
    - Якщо Total не знайдений, палетні колонки шукаються праворуч від Brutto до кінця заголовка.
    """
    sheet_name = ws_struct.title

    header_row = find_header_row(ws_struct)
    header_map = build_header_map(ws_struct, header_row)

    col_symbol = find_first_contains(header_map, SYMBOL_NAMES)
    col_netto = find_first_contains(header_map, NETTO_NAMES)
    col_brutto = find_first_contains(header_map, BRUTTO_NAMES)
    col_total = find_first_contains(header_map, TOTAL_NAMES)

    # Symbol/Netto/Brutto — обов'язкові
    if col_symbol is None or col_netto is None or col_brutto is None:
        raise ValueError(
            "Не знайдено всі обов'язкові колонки. "
            f"symbol={col_symbol}, netto={col_netto}, brutto={col_brutto}, total={col_total}, header_row={header_row}"
        )

    # Межі пошуку палетних колонок
    left = col_brutto
    right = col_total if col_total is not None else min(ws_struct.max_column, MAX_COLS_SCAN + 10)

    # Палетні колонки — усі заголовки між left і right (без ключових колонок)
    pallet_cols: List[int] = []
    for c in range(left + 1, right):
        hdr = header_map.get(c)
        if not hdr:
            continue
        # Відсікаємо ключові колонки
        if header_contains_any(hdr, REQUIRED_NON_TOTAL | TOTAL_NAMES):
            continue
        pallet_cols.append(c)

    if not pallet_cols:
        raise ValueError("Не знайдено жодної палетної колонки (між Brutto і Total або праворуч від Brutto).")

    return ColumnsDetection(
        sheet_name=sheet_name,
        header_row=header_row,
        col_symbol=col_symbol,
        col_netto=col_netto,
        col_brutto=col_brutto,
        col_total=col_total,
        pallet_cols=pallet_cols,
    )


# =============================================================================
# ОСНОВНА ОБРОБКА 1 ФАЙЛУ
# =============================================================================
def clean_one_file(input_path: str, output_path: str) -> Tuple[int, int, bool]:
    """
    Очищає один файл і зберігає результат.

    Повертає:
        checked_rows: кількість рядків, що потрапили у вихідний файл
        mismatches:   кількість рядків з mismatch (лише якщо у файлі була колонка Total)
        total_found:  чи була знайдена колонка Total у вхідному файлі
    """
    # Завантаження структури (формули), щоб прочитати заголовки та ознаки колонок
    wb_struct = openpyxl.load_workbook(input_path, data_only=False)
    sheet = pick_sheet_name(wb_struct)
    ws_struct = wb_struct[sheet]

    # Підготовка листа: розмерджити + показати приховані колонки
    unmerge_all(ws_struct)
    unhide_all_columns(ws_struct)

    # Завантаження значень (data_only=True), щоб отримати результати формул
    wb_val = openpyxl.load_workbook(input_path, data_only=True)
    ws_val = wb_val[sheet]

    # Детекція структури
    det = detect_columns(ws_struct)

    LOGGER.debug("Sheet=%s", sheet)
    LOGGER.debug("Header row=%s", det.header_row)
    LOGGER.debug(
        "Cols: symbol=%s netto=%s brutto=%s total=%s",
        det.col_symbol, det.col_netto, det.col_brutto, det.col_total
    )
    LOGGER.debug("Pallet cols=%s", det.pallet_cols)
    for c in det.pallet_cols:
        hdr = norm_lower(ws_struct.cell(det.header_row, c).value)
        LOGGER.debug(
            "Pallet header col=%s letter=%s header=%s",
            c, get_column_letter(c), hdr
        )

    # Формуємо набір колонок, що переносимо у вихід:
    # Symbol, Netto, Brutto, pallet_cols..., TOTAL
    kept_cols: List[int] = []
    for c in [det.col_symbol, det.col_netto, det.col_brutto, *det.pallet_cols]:
        if c not in kept_cols:
            kept_cols.append(c)

    # У вихідному файлі остання колонка завжди TOTAL (обчислений)
    out_wb = Workbook()
    out_ws = out_wb.active
    out_ws.title = sheet

    # Підтягнути ширину колонок (за наявності)
    for out_idx, src_col in enumerate(kept_cols, start=1):
        w = ws_struct.column_dimensions[get_column_letter(src_col)].width
        if w:
            out_ws.column_dimensions[get_column_letter(out_idx)].width = w

    # Заголовки вихідного файлу
    out_headers: List[str] = []
    header_map = build_header_map(ws_struct, det.header_row)
    for c in kept_cols:
        if c == det.col_symbol:
            out_headers.append("Symbol")
        else:
            out_headers.append(header_map.get(c, f"col_{c}"))
    out_headers.append("TOTAL")

    for j, h in enumerate(out_headers, start=1):
        out_ws.cell(1, j, h)

    checked = 0
    mismatches = 0
    out_row = 2

    total_found = det.col_total is not None

    # Проходимо всі рядки, починаючи з 1 — але:
    # - рядок заголовків переносимо як заголовок (вже записали),
    # - приховані рядки пропускаємо,
    # - рядки без Symbol пропускаємо.
    for r in range(det.header_row + 1, ws_struct.max_row + 1):
        if is_row_hidden(ws_struct, r):
            continue

        symbol_val = ws_val.cell(r, det.col_symbol).value
        if norm(symbol_val) == "":
            # Рядки без Symbol у вихід не переносимо
            continue

        # Обчислюємо TOTAL як суму палетних колонок (кількість одиниць товару)
        comp_total = 0.0
        for c in det.pallet_cols:
            v = as_float(ws_val.cell(r, c).value)
            if v is not None:
                comp_total += v

        # Якщо у файлі є оригінальний Total — перевіряємо mismatch
        row_mismatch = False
        if total_found:
            orig = as_float(ws_val.cell(r, det.col_total).value) if det.col_total is not None else None
            orig_total = orig if orig is not None else 0.0

            # Якщо і обчислений, і оригінальний підсумок нульові — можна не переносити рядок
            # (часто це "порожні" рядки з формулами або технічні підсумки)
            if abs(comp_total) < TOL and abs(orig_total) < TOL:
                continue

            row_mismatch = abs(comp_total - orig_total) > TOL
            if row_mismatch:
                mismatches += 1
                LOGGER.debug(
                    "Mismatch row=%s comp_total=%s orig_total=%s diff=%s",
                    r, comp_total, orig_total, comp_total - orig_total
                )
        else:
            # Якщо Total не знайдено — просто пропускаємо "порожні" рядки
            if abs(comp_total) < TOL:
                continue

        # Записуємо рядок у вихідний файл
        for j, c in enumerate(kept_cols, start=1):
            out_ws.cell(out_row, j, ws_val.cell(r, c).value)

        out_ws.cell(out_row, len(kept_cols) + 1, comp_total)

        if row_mismatch:
            for j in range(1, len(kept_cols) + 2):
                out_ws.cell(out_row, j).fill = FILL_RED

        checked += 1
        out_row += 1

    out_wb.save(output_path)
    return checked, mismatches, total_found


# =============================================================================
# BATCH-ОБРОБКА ПАПКИ
# =============================================================================
def main() -> None:
    """
    Обробляє всі .xlsx-файли з UPDATES/ACTIVE_REPORTS та формує результати у UPDATES/PROCESSED_REPORTS.

    В консолі:
      - 1 рядок на файл
      - 1 підсумковий рядок по всьому запуску

    У лог-файлі:
      - детальна інформація по колонках, палетних колонках та mismatch
      - підсумок запуску
    """
    ensure_dirs()
    LOGGER.info("======== NEW RUN ========")

    files = [
        f for f in os.listdir(ACTIVE_REPORTS_DIR)
        if f.lower().endswith(".xlsx") and not f.startswith("~$")
    ]

    total_files = 0
    success_files = 0
    total_missing_files = 0

    for f in files:
        total_files += 1
        src = os.path.join(ACTIVE_REPORTS_DIR, f)
        dst = os.path.join(PROCESSED_REPORTS_DIR, f.replace(".xlsx", "_cleaned.xlsx"))

        try:
            LOGGER.info("START file=%s", src)
            checked, mismatches, total_found = clean_one_file(src, dst)
            LOGGER.info(
                "DONE file=%s checked=%s mismatches=%s saved=%s total_found=%s",
                src, checked, mismatches, dst, total_found
            )

            success_files += 1
            if not total_found:
                total_missing_files += 1

            total_tag = "total=calc" if not total_found else "total=src"
            print(f"OK   {f} | checked={checked} | mismatches={mismatches} | {total_tag}")

        except Exception as exc:
            fail_dst = safe_copy_to_failed(src)
            LOGGER.exception("FAIL file=%s error=%s", src, exc)
            print(f"FAIL {f} | {exc} | copied to {fail_dst}")

    summary = (
        f"Проаналізовано: {total_files} файлів | "
        f"Сформовано: {success_files} файлів "
        f"(із них без Total у вхідному файлі: {total_missing_files})"
    )
    print(summary)
    LOGGER.info(summary)


if __name__ == "__main__":
    main()
