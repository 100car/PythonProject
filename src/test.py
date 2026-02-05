# from src.config import load_config
#
# cfg = load_config()
# print("ROOT:", cfg.root)
# print("IN:", cfg.in_dir)
# print("OUT:", cfg.out_dir)
# print("LOG:", cfg.log_dir)
# print("DICT:", cfg.shared_dictionaries_dir)

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import load_config


def setup_logging(log_file: Path, level: str = "INFO") -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # щоб не дублювало хендлери при повторних запусках в IDE
    if logger.handlers:
        logger.handlers.clear()

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # лог у файл
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # лог у консоль
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)


def ensure_dirs(*dirs: Path) -> None:
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def write_smoke_test_excel(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"smoke_test_{ts}.xlsx"

    df = pd.DataFrame(
        {
            "hello": ["world", "recipes"],
            "value": [1, 2],
        }
    )

    # приклад: 2 аркуші в одному файлі
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
        df.describe(include="all").to_excel(writer, sheet_name="summary")

    return out_path


def main() -> int:
    cfg = load_config()

    # створюємо робочі папки (в межах проєкту)
    ensure_dirs(cfg.in_dir, cfg.out_dir, cfg.log_dir)

    # логування
    setup_logging(cfg.log_file, cfg.log_level)
    log = logging.getLogger("recipes")

    log.info("Project root: %s", cfg.root)
    log.info("IN dir:       %s", cfg.in_dir)
    log.info("OUT dir:      %s", cfg.out_dir)
    log.info("LOG dir:      %s", cfg.log_dir)
    log.info("Dictionaries: %s", cfg.shared_dictionaries_dir)

    # перевірка, що shared словники існують (не фейлимось, просто попереджаємо)
    if not cfg.shared_dictionaries_dir.exists():
        log.warning("Shared dictionaries dir does not exist: %s", cfg.shared_dictionaries_dir)

    # “smoke test” експорту в Excel
    out_xlsx = write_smoke_test_excel(cfg.out_dir)
    log.info("Smoke test Excel written: %s", out_xlsx)

    # показати, що є у FROM_SELLER
    files = []
    if cfg.in_dir.exists():
        for p in cfg.in_dir.iterdir():
            if p.is_file() and p.suffix.lower() in cfg.input_extensions:
                files.append(p.name)

    if files:
        log.info("Input files detected (%d): %s", len(files), ", ".join(files))
    else:
        log.info("No input files in %s yet (ok).", cfg.in_dir)

    log.info("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
