def _take_money_from_left(tokens: list[str], start: int) -> tuple[str | None, int]:
    """Parse money starting at index `start` moving left-to-right.

    Handles thousand separators split into separate tokens, e.g. ["6","240,00"] -> "6 240,00".
    Returns (money_str, next_index_after_money).
    """
    if start >= len(tokens):
        return None, start
    parts: list[str] = []
    i = start
    # consume leading 1-3 digit groups until we hit a token with comma decimals
    while i < len(tokens) and "," not in tokens[i]:
        # stop early if we hit something that is clearly not part of amount
        if not re.fullmatch(r"\d{1,3}", tokens[i]):
            return None, start
        parts.append(tokens[i])
        i += 1
    if i >= len(tokens) or "," not in tokens[i]:
        return None, start
    parts.append(tokens[i])
    i += 1
    return " ".join(parts), i


# faktury_pdf_to_excel_v13_state_buffer.py
# v13: Add state-buffer line assembler to attach orphan description rows (Lp 1-8) and improve parsing; keep v12 fixes.
# v12: Fix missing items (Lp 1-8 etc.) by stitching wrapped table rows before parsing; tighten Razem: money regex to avoid merging qty with amount.
# v11: Fix wrong pdf_netto extraction caused by "W tym:" totals line; also show which aggregate mismatched.
# - Picks "Razem:" line numbers more safely:
#     * extracts all money-like values (with comma) from the last Razem: line
#     * converts to floats
#     * keeps only "reasonable" values (< 1e9) to avoid the spurious "47 695 266 165,09"
#     * uses the first 3 reasonable values as (netto, vat, brutto)
# - Console summary remains one line, but adds FAIL reason: FAIL[netto] / FAIL[vat] / FAIL[brutto]

import re
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime

import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

# --- PyPDF2 compatibility shim (Camelot expects old PyPDF2 API) ---
try:
    import PyPDF2  # type: ignore
    if hasattr(PyPDF2, 'PdfReader'):
        PyPDF2.PdfFileReader = PyPDF2.PdfReader  # type: ignore
        R = PyPDF2.PdfReader  # type: ignore
        # Override deprecated legacy API to avoid runtime errors
        R.isEncrypted = property(lambda self: bool(getattr(self, 'is_encrypted', False)))  # type: ignore
        R.getNumPages = lambda self: len(self.pages)  # type: ignore
        R.numPages = property(lambda self: len(self.pages))  # type: ignore
        R.getPage = lambda self, i: self.pages[i]  # type: ignore
    if hasattr(PyPDF2, 'PdfWriter'):
        PyPDF2.PdfFileWriter = PyPDF2.PdfWriter  # type: ignore
        W = PyPDF2.PdfWriter  # type: ignore
        if hasattr(W, 'add_page'):
            W.addPage = W.add_page  # type: ignore
except Exception:
    pass

import pandas as pd
import camelot
import pdfplumber


BASE_DIR = Path(r"FAKTURY")
FROM_SELLER = BASE_DIR / "FROM_SELLER"
TO_EXCEL = BASE_DIR / "TO_EXCEL"
BAD_FAKTURY = BASE_DIR / "BAD_FAKTURY"
LOG_DIR = BASE_DIR / "LOG"

TO_EXCEL.mkdir(parents=True, exist_ok=True)
BAD_FAKTURY.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

TOL = 0.01
UNPARSED_PREVIEW = 25
MAX_REASONABLE_TOTAL = 1_000_000_000  # 1e9


# ----------------------------
# Logging (detailed file log + single-line console summary)
# ----------------------------
logger = logging.getLogger("pdf_to_excel")
logger.setLevel(logging.INFO)

log_path = LOG_DIR / f"pdf_to_excel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


class _TimeSeparatorFormatter(logging.Formatter):
    """Adds a separator line whenever the log timestamp (to the second) changes."""
    def __init__(self, fmt: str):
        super().__init__(fmt)
        self._last_sec = None

    def format(self, record: logging.LogRecord) -> str:
        sec = int(record.created)
        msg = super().format(record)
        if self._last_sec is None or sec != self._last_sec:
            self._last_sec = sec
            return "===================\n" + msg
        return msg

file_handler = logging.FileHandler(log_path, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(_TimeSeparatorFormatter("%(asctime)s | %(levelname)s | %(message)s"))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(message)s"))

class _OnlySummaryFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return bool(getattr(record, "summary", False))

console_handler.addFilter(_OnlySummaryFilter())

logger.handlers = []
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# ----------------------------
# Helpers
# ----------------------------
def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def parse_pl_number(x) -> float | None:
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    s = re.sub(r"[^\d,\.\-\s]", "", s).strip()
    if not s:
        return None
    s = s.replace(" ", "")
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    elif s.count(",") > 1 and s.count(".") == 0:
        parts = s.split(",")
        s = "".join(parts[:-1]) + "." + parts[-1]
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def find_header_row_index(df: pd.DataFrame) -> int | None:
    keys = ["Lp", "Nazwa", "Indeks", "Ilość", "Cena", "VAT", "Wartość"]
    for i in range(min(len(df), 12)):
        row_text = normalize_whitespace(" ".join(map(str, df.iloc[i].tolist())))
        hits = sum(1 for k in keys if k.lower() in row_text.lower())
        if hits >= 3:
            return i
    return None


def clean_items_table(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df = df.replace({None: ""})
    df = df.map(lambda x: str(x).strip() if x != "" else "")

    df = df[df.apply(lambda r: any(v != "" for v in r.tolist()), axis=1)].reset_index(drop=True)

    hdr_i = find_header_row_index(df)
    if hdr_i is not None:
        headers = df.iloc[hdr_i].tolist()
        headers = [normalize_whitespace(h) if h else f"col_{idx}" for idx, h in enumerate(headers)]
        df = df.iloc[hdr_i + 1 :].reset_index(drop=True)
        df.columns = headers
    else:
        df.columns = [f"col_{i}" for i in range(df.shape[1])]

    def col_is_empty(col: pd.Series) -> bool:
        return col.map(lambda x: str(x).strip() == "").all()

    df = df[[c for c in df.columns if not col_is_empty(df[c])]].copy()

    # Heuristic: some PDFs produce an extra leading blank column, shifting Lp. to the 2nd column.
    # If col0 is mostly empty/non-numeric while col1 is mostly numeric, drop col0.
    if df.shape[1] >= 2 and len(df) > 0:
        c0 = df.iloc[:, 0].astype(str).str.strip()
        c1 = df.iloc[:, 1].astype(str).str.strip()
        c0_empty_ratio = (c0 == "").mean()
        c0_num_ratio = c0.str.fullmatch(r"\d+").fillna(False).mean()
        c1_num_ratio = c1.str.fullmatch(r"\d+").fillna(False).mean()
        if (c0_empty_ratio > 0.5 or c0_num_ratio < 0.2) and c1_num_ratio > 0.6:
            df = df.iloc[:, 1:].copy()
            # re-label columns to keep downstream logic stable
            df.columns = [f"col_{i}" for i in range(df.shape[1])]

    if len(df) > 0:
        joined = df.astype(str).agg(" ".join, axis=1).str.lower()
        df = df[~joined.str.contains(r"\blp\b|\bnazwa\b|\bindeks\b|\bilo", regex=True)].reset_index(drop=True)

    return df


# ----------------------------
# Token-based line parser (from v10)
# ----------------------------
INDEKS_RE = re.compile(r"^[A-Z0-9][A-Z0-9_\-\/]*-[A-Z0-9_\-\/]+-?$", re.I)
PRICE_RE = re.compile(r"^\d+,\d{2}$")
VAT_RE = re.compile(r"^\d{1,2}\s*%$")

# Item rows start with an integer Lp followed by whitespace (sometimes "1." or "1)").
# IMPORTANT: avoid matching engine specs like "1.6/1.8/2.0" (no whitespace after the dot).
LP_START_RE = re.compile(r"^\s*\d{1,4}(?:[\.)])?\s+")


def stitch_lines(lines: list[str]) -> list[str]:
    """Join wrapped item rows: if a line doesn't start with Lp number, treat it as continuation."""
    stitched: list[str] = []
    buf = ""
    for line in lines:
        line = normalize_whitespace(line)
        if not line:
            continue
        if LP_START_RE.match(line):
            if buf:
                stitched.append(buf)
            buf = line
        else:
            buf = f"{buf} {line}".strip() if buf else line
    if buf:
        stitched.append(buf)
    return stitched


def state_buffer_lines(raw_lines: list[str]) -> tuple[list[str], list[str]]:
    """Assemble item lines using a simple state machine.

    Why: Camelot (stream) often splits one invoice position into multiple physical
    rows and may output "orphan" description/spec lines (no Lp) either *after* an
    item header row or even *before* the numeric row. For positions 1-8 we saw
    many such lines like "1.6/1.8/2.0..." and "16V ...".

    Strategy:
      - Keep a pending buffer for orphan lines BEFORE we see the next Lp row.
      - Keep a current buffer for the active item (started by an Lp row).
      - When a new Lp row appears: flush previous current; attach pending (as
        extra description) to the new row; start new current.
      - Non-Lp lines: append to current if active, otherwise accumulate into
        pending.

    Returns:
      (candidates, orphan_unparsed)
    """
    candidates: list[str] = []
    pending: list[str] = []
    current: list[str] = []

    def flush_current():
        if current:
            candidates.append(normalize_whitespace(" ".join(current)))

    for line in raw_lines:
        line = normalize_whitespace(line)
        if not line:
            continue

        if LP_START_RE.match(line):
            # start a new item
            if current:
                flush_current()
                current = []

            if pending:
                # Attach orphan lines as extra description for this item.
                line = normalize_whitespace(f"{line} {' '.join(pending)}")
                pending = []

            current = [line]
        else:
            if current:
                current.append(line)
            else:
                pending.append(line)

    if current:
        flush_current()

    # pending at the end is truly orphan text (usually header/footer noise)
    return candidates, pending


def pop_money(tokens: list[str]) -> str | None:
    if not tokens or "," not in tokens[-1]:
        return None
    tail = tokens.pop()
    parts = [tail]
    while tokens and re.fullmatch(r"\d{1,3}", tokens[-1]):
        parts.insert(0, tokens.pop())
    return " ".join(parts)

def _join_split_indeks(tokens: list[str], idx_pos: int) -> tuple[str, int]:
    indeks = tokens[idx_pos]
    end = idx_pos
    if indeks.endswith("-") and idx_pos + 1 < len(tokens):
        nxt = tokens[idx_pos + 1]
        if re.fullmatch(r"[A-Z]{2,6}", nxt):
            indeks = f"{indeks}{nxt}"
            end = idx_pos + 1
    return indeks, end

def _extract_qty_from_right(rest: list[str]) -> tuple[str | None, list[str]]:
    if not rest:
        return None, rest
    j = len(rest) - 1
    qty_parts = []
    while j >= 0 and re.fullmatch(r"\d{1,3}|\d+", rest[j]):
        qty_parts.insert(0, rest[j])
        j -= 1
    if not qty_parts:
        return None, rest
    leftover = rest[: j + 1]
    return " ".join(qty_parts), leftover

def parse_item_line(line: str) -> dict | None:
    s = normalize_whitespace(line.replace("\n", " "))
    if not s or s.lower().startswith("razem:"):
        return None
    tokens = s.split()
    if not tokens:
        return None

    # Guard: ignore engine specs / variants that start with decimals like "1.6/1.8/2.0".
    # Those are description-only lines and should be glued to the nearest real item row.
    if re.match(r"^\d+\.\d", tokens[0]):
        return None

    m = re.match(r"^(\d+)(\D.+)$", tokens[0])
    if m:
        lp = m.group(1)
        tokens[0] = m.group(2)
    else:
        if not re.fullmatch(r"\d+", tokens[0]):
            return None
        lp = tokens.pop(0)

    idx_pos = None
    for i, t in enumerate(tokens):
        if INDEKS_RE.match(t):
            idx_pos = i
            break
        # Some lines glue the engine spec + indeks w/o whitespace, e.g.
        # "1.8TDDI/1.8TDCIPFOR181-A-0-N" -> split tail indeks.
        m_glued = re.search(r"([A-Z]{2,6}\d{2,}[A-Z0-9_\-\/]*-[A-Z0-9_\-\/]+-?)$", t, re.I)
        if m_glued and m_glued.start() > 0:
            prefix = t[: m_glued.start()]
            idx_token = t[m_glued.start() :]
            tokens[i] = prefix
            tokens.insert(i + 1, idx_token)
            idx_pos = i + 1
            break
    if idx_pos is None or idx_pos == 0:
        return None

    nazwa_tokens = tokens[:idx_pos]
    indeks, idx_end = _join_split_indeks(tokens, idx_pos)

    jm_pos = idx_end + 1

    # Some invoices split a suffix like "-SET"/"SET" into a separate token right after the indeks.
    # In such case the unit (e.g., "szt") comes one token later.
    if jm_pos < len(tokens):
        t = tokens[jm_pos].upper()
        if t in {"-SET", "SET"} or (t.startswith("-") and t[1:].isalpha()):
            jm_pos += 1

    if jm_pos >= len(tokens):
        return None
    jm = tokens[jm_pos]

    rest = tokens[jm_pos + 1 :].copy()
    if len(rest) < 6:
        return None

    # Split numeric columns from trailing description using the VAT token as an anchor.
    # This avoids false positives when description ends with something like "76,50".
    vat_idx = None
    for i, tok in enumerate(rest):
        if VAT_RE.match(tok):
            vat_idx = i
    if vat_idx is None:
        return None

    vat_tok = rest[vat_idx].replace(" ", "")

    # Parse the three totals right after VAT% (netto, VAT amount, brutto).
    after_vat = rest[vat_idx + 1 :]
    netto_s, j = _take_money_from_left(after_vat, 0)
    vat_amt_s, j = _take_money_from_left(after_vat, j)
    brutto_s, j = _take_money_from_left(after_vat, j)
    if not (netto_s and vat_amt_s and brutto_s):
        return None

    tail_extra_tokens = after_vat[j:]  # description tail (can contain numbers like "76,50")

    # Everything before VAT% is: qty + price columns + (optional) discount
    rest = rest[:vat_idx]


    price_tail = []
    while rest and PRICE_RE.match(rest[-1]) and len(price_tail) < 4:
        price_tail.insert(0, rest.pop())
    if len(price_tail) < 2:
        return None

    if len(price_tail) == 2:
        cena_netto, cena_po = price_tail
        rabat = None
    else:
        cena_netto, rabat, cena_po = price_tail[-3:]

    qty_s, leftover = _extract_qty_from_right(rest)
    if not qty_s:
        return None

    nazwa_extra = " ".join(leftover).strip()
    if tail_extra_tokens:
        nazwa_extra = (nazwa_extra + ' ' + ' '.join(tail_extra_tokens)).strip()
    nazwa = " ".join(nazwa_tokens).strip()
    nazwa = normalize_whitespace(f"{nazwa} {nazwa_extra}") if nazwa_extra else normalize_whitespace(nazwa)

    return {
        "Lp.": int(lp),
        "Nazwa": nazwa,
        "Indeks": indeks,
        "J.m.": jm,
        "Ilość": int(qty_s.replace(" ", "")),
        "Cena netto": parse_pl_number(cena_netto),
        "Rabat": parse_pl_number(rabat) if rabat else None,
        "Cena netto po rabacie": parse_pl_number(cena_po),
        "St. VAT": vat_tok,
        "Wartość netto": parse_pl_number(netto_s),
        "Kwota VAT": parse_pl_number(vat_amt_s),
        "Wartość brutto": parse_pl_number(brutto_s),
    }


CANON_COLS = [
    "Lp.", "Nazwa", "Indeks", "J.m.", "Ilość", "Cena netto", "Rabat",
    "Cena netto po rabacie", "St. VAT", "Wartość netto", "Kwota VAT", "Wartość brutto"
]


def build_canonical_items(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    parsed = []
    unparsed = []

    # Build raw lines from Camelot rows.
    raw_lines: list[str] = []
    for _, row in df.iterrows():
        parts = []
        for v in row.tolist():
            vv = normalize_whitespace(str(v).replace("\n", " "))
            if vv:
                parts.append(vv)
        line = " ".join(parts)
        if line:
            # Skip obvious header/footer noise that Camelot sometimes includes in the table dump
            ll = line.lower()
            if any(k in ll for k in [
                "sprzedawca:", "nabywca:", "odbiorca:", "faktura sprzeda", "nip:", "waluta:", "kurs:", "termin płatności",
                "bank:", "forma płatności", "bdo:", "strona :",
            ]):
                unparsed.append(line)
                continue
            raw_lines.append(line)

    # Assemble candidate item lines using a state machine that can also attach
    # "orphan" description rows to the correct item.
    candidate_lines, orphan_pending = state_buffer_lines(raw_lines)

    for line in candidate_lines:
        item = parse_item_line(line)
        if item:
            parsed.append(item)
        else:
            if not line.lower().startswith("razem:"):
                unparsed.append(line)

    # Add truly orphan lines (usually header/footer noise)
    for line in orphan_pending:
        if line and not line.lower().startswith("razem:"):
            unparsed.append(line)

    if not parsed:
        logger.error("Sample unparsed lines (first rows):\n" + "\n".join(unparsed[:UNPARSED_PREVIEW]))
        raise RuntimeError("Could not parse any item lines into canonical table.")

    out = pd.DataFrame(parsed, columns=CANON_COLS).sort_values("Lp.").reset_index(drop=True)

    logger.info(f"Parsed items: {len(out)}; Unparsed lines: {len(unparsed)}")
    if unparsed:
        logger.info("First unparsed lines:\n" + "\n".join(unparsed[:UNPARSED_PREVIEW]))

    return out, unparsed


def extract_tables_with_camelot(pdf_path: Path) -> tuple[pd.DataFrame, list[str]]:
    logger.info(f"[{pdf_path.name}] extracting tables...")

    tables = []

    # 1️⃣ Спочатку STREAM (безпечніше на Windows)
    try:
        t_stream = camelot.read_pdf(
            str(pdf_path),
            pages="all",
            flavor="stream"
        )
        if t_stream and t_stream.n > 0:
            tables = [t.df for t in t_stream]
            logger.info(f"[{pdf_path.name}] stream tables: {t_stream.n}")
    except Exception as e:
        logger.warning(f"[{pdf_path.name}] stream failed: {e}")

    # 2️⃣ ТІЛЬКИ якщо stream нічого не знайшов — LATTICE
    if not tables:
        try:
            t_lattice = camelot.read_pdf(
                str(pdf_path),
                pages="all",
                flavor="lattice"
            )
            if t_lattice and t_lattice.n > 0:
                tables = [t.df for t in t_lattice]
                logger.info(f"[{pdf_path.name}] lattice tables: {t_lattice.n}")
        except Exception as e:
            logger.warning(f"[{pdf_path.name}] lattice failed: {e}")

    # 3️⃣ Якщо обидва режими нічого не дали — це реальна помилка
    if not tables:
        raise RuntimeError(
            f"[{pdf_path.name}] No tables extracted by Camelot (stream & lattice)."
        )

    combined = pd.concat(tables, ignore_index=True)
    raw = clean_items_table(combined)
    return build_canonical_items(raw)


def extract_pdf_totals(pdf_path: Path) -> dict:
    text_all = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t:
                text_all.append(t)
    full_text = "\n".join(text_all)

    # Detect currencies mentioned in the document
    currs = set(re.findall(r"\b(PLN|EUR|USD|CHF|GBP)\b", full_text))
    m_doc = re.search(r"Waluta:\s*([A-Z]{3})", full_text)
    doc_currency = m_doc.group(1) if m_doc else (next(iter(currs)) if currs else None)
    has_rate = bool(re.search(r"\bKurs\b", full_text, flags=re.IGNORECASE))

    matches = list(re.finditer(r"Razem:\s*(.+)", full_text))
    if not matches:
        # still return currency info for downstream warning logic
        return {
            "pdf_currency": None,
        "pdf_qty_total": None,
            "doc_currency": doc_currency,
            "currency_mixed": bool(currs and len(currs) > 1),
            "currencies_found": ",".join(sorted(currs)) if currs else None,
        }

    last_line = normalize_whitespace(matches[-1].group(1))

    # Optional: quantity total (first cell after 'Razem:'). Often formatted like '33 015.'
    qty_total = None
    m_qty = re.match(r"^\s*(\d{1,3}(?:[ \u00A0]\d{3})*)(?:[\.,])?\b", last_line)
    if m_qty:
        qty_s = m_qty.group(1)
        # Ensure it's an integer-like token (no comma decimals)
        if "," not in qty_s:
            try:
                qty_total = int(re.sub(r"[ \u00A0]", "", qty_s))
            except Exception:
                qty_total = None


    # Extract all money-like values (Polish style)
    money_strs = re.findall(r"\d{1,3}(?:[ \u00A0]\d{3})*,\d{2}", last_line)
    vals = []
    for ms in money_strs:
        v = parse_pl_number(ms)
        if v is None:
            continue
        if abs(v) < MAX_REASONABLE_TOTAL:
            vals.append(v)

    # We expect (netto, vat, brutto) as the last 3 values on the Razem line
    if len(vals) >= 3:
        netto, vat, brutto = vals[-3:]
        currency_mixed = False
        # Heuristic: invoices with "Kurs" and non-PLN document currency often show PLN totals + foreign currency elsewhere.
        if (has_rate and doc_currency and doc_currency != "PLN") or (currs and len(currs) > 1):
            currency_mixed = True

        return {
            "pdf_netto": netto,
            "pdf_vat": vat,
            "pdf_brutto": brutto,
            "pdf_qty_total": qty_total,
            "pdf_currency": "PLN" if (has_rate and doc_currency and doc_currency != "PLN") else doc_currency,
            "doc_currency": doc_currency,
            "currency_mixed": currency_mixed,
            "currencies_found": ",".join(sorted(currs)) if currs else None,
        }

    return {
        "pdf_currency": None,
        "pdf_qty_total": None,
        "doc_currency": doc_currency,
        "currency_mixed": bool(currs and len(currs) > 1),
        "currencies_found": ",".join(sorted(currs)) if currs else None,
    }

def _is_text_item_start(line: str) -> bool:
    """Detect item start in pdfplumber text lines.

    pdfplumber often returns lines like "1TUL.PROW. ..." (no whitespace after Lp).
    We treat a line as an item start if it begins with an integer Lp followed by a
    non-digit that is NOT a decimal continuation (avoid "1.6/1.8...").
    """
    s = normalize_whitespace(line)
    if not s:
        return False
    sl = s.lower()
    if sl.startswith("lp.") or sl.startswith("strona") or sl.startswith("razem:"):
        return False
    # starts with digits
    m = re.match(r"^(\d{1,4})(.*)$", s)
    if not m:
        return False
    rest = m.group(2)
    if not rest:
        return False
    # decimal engine spec like 1.6...
    if rest.startswith(".") and len(rest) > 1 and rest[1].isdigit():
        return False
    return True


def extract_items_from_pdf_text(pdf_path: Path, *, max_lp: int | None = None, all_pages: bool = False) -> pd.DataFrame:
    """Fallback extractor: parse items from pdfplumber text.

    By default we read only page 1 (the common failure case: missing top rows).
    If all_pages=True, we parse the whole PDF text and rely on max_lp to filter
    out accidental matches.
    """
    lines: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        if not pdf.pages:
            return pd.DataFrame(columns=CANON_COLS)
        pages = pdf.pages if all_pages else [pdf.pages[0]]
        for page in pages:
            t = page.extract_text() or ""
            for ln in t.splitlines():
                ln = normalize_whitespace(ln)
                if ln:
                    lines.append(ln)

    candidates: list[str] = []
    current: list[str] = []

    def flush():
        if current:
            candidates.append(normalize_whitespace(" ".join(current)))

    for ln in lines:
        if ln.lower().startswith("razem:"):
            flush()
            current = []
            continue
        if _is_text_item_start(ln):
            flush()
            current = [ln]
        else:
            if current:
                current.append(ln)
    flush()

    parsed = []
    for c in candidates:
        item = parse_item_line(c)
        if item:
            if max_lp is not None and int(item.get("Lp.", 0)) > max_lp:
                continue
            parsed.append(item)

    if not parsed:
        return pd.DataFrame(columns=CANON_COLS)

    return pd.DataFrame(parsed, columns=CANON_COLS).drop_duplicates(subset=["Lp."]).sort_values("Lp.").reset_index(drop=True)


def compute_items_sums(items: pd.DataFrame) -> dict:
    return {
        "calc_netto": float(pd.Series(items["Wartość netto"]).dropna().sum()),
        "calc_vat": float(pd.Series(items["Kwota VAT"]).dropna().sum()),
        "calc_brutto": float(pd.Series(items["Wartość brutto"]).dropna().sum()),
    }


def strict_compare_3_totals(pdf_totals: dict, calc_totals: dict, tol: float = TOL) -> dict:
    # If PDF totals are in mixed currencies (e.g., EUR + PLN with exchange rate),
    # do not hard-fail the invoice totals check. Mark as WARNING.
    if pdf_totals and pdf_totals.get("currency_mixed"):
        return {
            "checked_totals": 0,
            "mismatches": 0,
            "total_source": "src",
            "status": "WARNING",
            "failed": [],
            "warned": ["totals"],
            "warning_code": "W002",
            "warning_msg": "Totals w różnych walutach (mieszana waluta / kurs). Walidacja sum pominięta.",
            "diff_netto": None,
            "diff_vat": None,
            "diff_brutto": None,
        }

    if not pdf_totals or pdf_totals.get("pdf_netto") is None:
        return {
            "checked_totals": 0,
            "mismatches": 0,
            "total_source": "calc",
            "status": "PASS",
            "failed": [],
            "warning_code": None,
            "warning_msg": None,
            "diff_netto": None,
            "diff_vat": None,
            "diff_brutto": None,
        }

    checked = 0
    mism = 0
    failed = []
    diffs = {"diff_netto": None, "diff_vat": None, "diff_brutto": None}

    for short in ("netto", "vat", "brutto"):
        pv = pdf_totals.get(f"pdf_{short}")
        cv = calc_totals.get(f"calc_{short}")
        if pv is None or cv is None:
            continue
        checked += 1
        d = cv - pv
        diffs[f"diff_{short}"] = d
        if abs(d) > tol:
            mism += 1
            failed.append(short)

    status = "PASS" if mism == 0 else "FAIL"
    return {
        "checked_totals": checked,
        "mismatches": mism,
        "total_source": "src",
        "status": status,
        "failed": failed,
        "warning_code": None,
        "warning_msg": None,
        **diffs,
    }

def write_excel(output_xlsx: Path, items: pd.DataFrame, summary: dict, unparsed: list[str]):
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        items.to_excel(writer, sheet_name="Items", index=False)
        pd.DataFrame([{"Metric": k, "Value": v} for k, v in summary.items()]).to_excel(
            writer, sheet_name="Summary", index=False
        )
        if unparsed:
            pd.DataFrame({"raw_line": unparsed}).to_excel(writer, sheet_name="Unparsed", index=False)

    # --- ERP-like formatting (openpyxl) ---
    try:
        from openpyxl import load_workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        wb = load_workbook(output_xlsx)
        thin = Side(style="thin", color="D9D9D9")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        header_fill = PatternFill("solid", fgColor="F2F2F2")
        header_font = Font(bold=True, color="1F1F1F")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        fill_pass = PatternFill("solid", fgColor="C6EFCE")   # light green
        fill_warn = PatternFill("solid", fgColor="FFF2CC")   # light yellow
        fill_fail = PatternFill("solid", fgColor="FFC7CE")   # light red
        font_status = Font(bold=True, color="1F1F1F")

        def _autosize(ws):
            for col in range(1, ws.max_column + 1):
                letter = get_column_letter(col)
                max_len = 0
                for row in range(1, ws.max_row + 1):
                    v = ws.cell(row=row, column=col).value
                    if v is None:
                        continue
                    s = str(v)
                    max_len = max(max_len, len(s))
                ws.column_dimensions[letter].width = min(max(10, max_len + 2), 55)

        def _style_table(ws):
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            ws.sheet_view.showGridLines = False

            # Header
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border

            # Body cells
            body_alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            for r in range(2, ws.max_row + 1):
                for c in range(1, ws.max_column + 1):
                    cell = ws.cell(row=r, column=c)
                    cell.border = border
                    if cell.alignment is None or cell.alignment == Alignment():
                        cell.alignment = body_alignment

            _autosize(ws)

        for name in wb.sheetnames:
            _style_table(wb[name])

        # Number formats (basic)
        if "Items" in wb.sheetnames:
            ws = wb["Items"]
            headers = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
            money_like = {"netto", "vat", "brutto", "wartosc", "wartość", "cena", "price", "amount"}
            qty_like = {"ilosc", "ilość", "qty", "quantity"}
            for c, h in enumerate(headers, start=1):
                if not h:
                    continue
                h_norm = str(h).strip().lower()
                fmt = None
                if any(k in h_norm for k in money_like):
                    fmt = '#,##0.00'
                elif any(k in h_norm for k in qty_like):
                    fmt = '#,##0.00'
                if fmt:
                    for r in range(2, ws.max_row + 1):
                        cell = ws.cell(row=r, column=c)
                        if isinstance(cell.value, (int, float)):
                            cell.number_format = fmt

        if "Summary" in wb.sheetnames:
            ws = wb["Summary"]
            status_val = None
            status_row = None
            for r in range(2, ws.max_row + 1):
                if str(ws.cell(row=r, column=1).value).strip() == "status":
                    status_row = r
                    status_val = str(ws.cell(row=r, column=2).value).strip().upper()
                    break

            if status_row:
                if status_val == "PASS":
                    fill = fill_pass
                elif status_val == "WARNING":
                    fill = fill_warn
                else:
                    fill = fill_fail

                for c in range(1, ws.max_column + 1):
                    cell = ws.cell(row=status_row, column=c)
                    cell.fill = fill
                    cell.font = font_status
                    cell.alignment = Alignment(horizontal="left", vertical="center")

                wmsg = summary.get("warning_msg")
                if wmsg:
                    insert_at = status_row + 1
                    ws.insert_rows(insert_at)
                    ws.cell(row=insert_at, column=1, value="warning_msg")
                    ws.cell(row=insert_at, column=2, value=wmsg)
                    for c in (1, 2):
                        ws.cell(row=insert_at, column=c).fill = fill_warn
                        ws.cell(row=insert_at, column=c).font = Font(bold=True)
                        ws.cell(row=insert_at, column=c).border = border
                    _autosize(ws)

        wb.save(output_xlsx)
    except Exception:
        pass

def _console_summary_line(status: str, failed: list[str], xlsx_name: str, checked_rows: int, mismatches: int, total_source: str, warned: list[str] | None = None) -> str:
    badge = status
    if status == "FAIL" and failed:
        badge = f"FAIL[{','.join(failed)}]"
    elif status == "WARNING" and warned:
        badge = f"WARNING[{','.join(warned)}]"
    return (
        f"{badge:<11} | "
        f"{xlsx_name:<55} | "
        f"checked={checked_rows:<5} | "
        f"mismatches={mismatches:<1} | "
        f"total={total_source}"
    )


def process_one_pdf(pdf_path: Path):
    items, unparsed = extract_tables_with_camelot(pdf_path)

    # Fallback: Camelot can miss the top of page-1 table (often Lp 1-8). If we detect
    # missing Lp values, attempt to parse positions from pdfplumber text and merge.
    try:
        if not items.empty and "Lp." in items.columns:
            max_lp = int(items["Lp."].max())
            present = set(map(int, items["Lp."].tolist()))
            missing = {lp for lp in range(1, max_lp + 1) if lp not in present}
            # Fallback when Camelot misses any rows up to Lp<=20 (often the bottom of page 1 like 17-19)
            # We parse page-1 text with pdfplumber and merge by Lp.
            if missing and min(missing) <= 20:
                text_items = extract_items_from_pdf_text(pdf_path, max_lp=min(25, max_lp))
                if not text_items.empty:
                    add = text_items[~text_items["Lp."].isin(items["Lp."])]
                    if not add.empty:
                        items = pd.concat([items, add], ignore_index=True).sort_values("Lp.").reset_index(drop=True)
                        logger.info(f"[{pdf_path.name}] added missing items from text: {sorted(set(add['Lp.'].tolist()))}")

                # refresh missing set after early merge
                present = set(map(int, items["Lp."].tolist()))
                missing = {lp for lp in range(1, max_lp + 1) if lp not in present}

            # If we still have missing Lp values after the early fallback, run a full-text
            # pass (all pages) but keep it bounded by max_lp.
            if missing and any(lp > 25 for lp in missing):
                text_items_all = extract_items_from_pdf_text(pdf_path, max_lp=max_lp, all_pages=True)
                if not text_items_all.empty:
                    add = text_items_all[~text_items_all["Lp."].isin(items["Lp."])]
                    if not add.empty:
                        items = pd.concat([items, add], ignore_index=True).sort_values("Lp.").reset_index(drop=True)
                        logger.info(f"[{pdf_path.name}] added more missing items from text(all): {sorted(set(add['Lp.'].tolist()))}")

            # Final sanity: keep only 1..max_lp (Camelot's max_lp is usually reliable)
            items = items[(items["Lp."] >= 1) & (items["Lp."] <= max_lp)].sort_values("Lp.").reset_index(drop=True)
    except Exception as _e:
        # Never fail the run because of fallback logic
        pass

    pdf_totals = extract_pdf_totals(pdf_path)
    calc_totals = compute_items_sums(items)
    cmp = strict_compare_3_totals(pdf_totals, calc_totals, tol=TOL)

    # Extra validation: Sum(Ilość) must match quantity total from 'Razem:' (if present)
    qty_pdf = pdf_totals.get("pdf_qty_total")
    qty_calc = None
    diff_qty = None
    checked_qty = 0
    if qty_pdf is not None and not items.empty and "Ilość" in items.columns:
        try:
            qty_calc = float(pd.Series(items["Ilość"]).dropna().sum())
            diff_qty = qty_calc - float(qty_pdf)
            checked_qty = 1

            if abs(diff_qty) > 0.0001:
                # If the document looks multi-currency / has exchange rate, treat qty mismatch as WARNING (not FAIL).
                has_fx = bool(pdf_totals.get("currency_mixed")) or (
                    pdf_totals.get("doc_currency") and str(pdf_totals.get("doc_currency")).upper() != "PLN"
                )

                if has_fx:
                    # WARNING (do not downgrade an existing FAIL)
                    if cmp.get("status") != "FAIL":
                        cmp["status"] = "WARNING"
                    cmp.setdefault("warned", [])
                    if "qty" not in cmp["warned"]:
                        cmp["warned"].append("qty")

                    msg = f"W003: Невідповідність кількості (PDF={qty_pdf}, calc={qty_calc}, diff={diff_qty})"
                    existing = cmp.get("warning_msg")
                    if existing:
                        if msg not in existing:
                            cmp["warning_msg"] = existing + " | " + msg
                    else:
                        cmp["warning_code"] = cmp.get("warning_code") or "W003"
                        cmp["warning_msg"] = msg
                else:
                    # FAIL (hard mismatch in simple PLN invoices)
                    cmp["status"] = "FAIL"
                    cmp.setdefault("failed", [])
                    if "qty" not in cmp["failed"]:
                        cmp["failed"].append("qty")
                    cmp["mismatches"] = int(cmp.get("mismatches", 0)) + 1
        except Exception:
            pass

    # Attach qty check info to cmp for reporting
    cmp["checked_qty"] = checked_qty
    cmp["calc_qty_sum"] = qty_calc
    cmp["diff_qty"] = diff_qty

    if cmp["status"] != "PASS":
        logger.info(
            f"[{pdf_path.name}] pdf_totals={pdf_totals} | calc_totals={calc_totals} | diffs="
            f"netto={cmp.get('diff_netto')} vat={cmp.get('diff_vat')} brutto={cmp.get('diff_brutto')}"
        )

    checked_rows = int(items.shape[0])

    summary = {
        "checked_rows": checked_rows,
        "unparsed_lines": len(unparsed),
        "tolerance": TOL,
        **pdf_totals,
        **calc_totals,
        **cmp,
    }

    out_xlsx = TO_EXCEL / (pdf_path.stem + ".xlsx")
    write_excel(out_xlsx, items, summary, unparsed)

    line = _console_summary_line(
        status=str(cmp["status"]),
        failed=list(cmp.get("failed", [])),
        warned=list(cmp.get("warned", [])) if cmp.get("warned") else None,
        xlsx_name=out_xlsx.name,
        checked_rows=checked_rows,
        mismatches=int(cmp["mismatches"]),
        total_source=str(cmp["total_source"]),
    )
    logger.info(line, extra={"summary": True})


def main():
    if not FROM_SELLER.exists():
        raise SystemExit(f"Folder not found: {FROM_SELLER.resolve()}")

    pdfs = sorted(FROM_SELLER.glob("*.pdf"))
    if not pdfs:
        logger.info(f"No PDFs in: {FROM_SELLER.resolve()}")
        logger.info(f"Log file: {log_path.resolve()}")
        return

    for pdf_path in pdfs:
        try:
            process_one_pdf(pdf_path)
        except Exception as e:
            logger.error(f"[{pdf_path.name}] FAILED: {e}")

            target = BAD_FAKTURY / pdf_path.name
            try:
                shutil.move(str(pdf_path), str(target))
                logger.info(f"[{pdf_path.name}] moved to BAD_FAKTURY")
            except Exception as move_err:
                logger.error(f"[{pdf_path.name}] move failed: {move_err}")

            out_xlsx_name = f"{pdf_path.stem}.xlsx"
            line = _console_summary_line(
                status="FAIL",
                failed=[],
                warned=None,
                xlsx_name=out_xlsx_name,
                checked_rows=0,
                mismatches=0,
                total_source="calc",
            )
            logger.info(line, extra={"summary": True})

    logger.info(f"Log file: {log_path.resolve()}")


if __name__ == "__main__":
    main()