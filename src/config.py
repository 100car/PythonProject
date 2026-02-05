from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


def project_root() -> Path:
    """
    Повертає корінь проєкту RECIPES.
    Очікуємо структуру:
      RECIPES/
        src/
          config.py
        config.yaml
    """
    return Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AppConfig:
    root: Path
    shared_dictionaries_dir: Path
    in_dir: Path
    out_dir: Path
    log_dir: Path
    log_file: Path
    log_level: str
    input_extensions: tuple[str, ...]


def load_config(config_path: Path | None = None) -> AppConfig:
    root = project_root()
    config_path = config_path or (root / "config.yaml")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    # ../DATA_DICTIONARIES (папка на одному рівні з RECIPES)
    shared_rel = data["project"]["shared_dictionaries_dir"]
    shared_dir = (root / shared_rel).resolve()

    in_dir = (root / data["paths"]["in_dir"]).resolve()
    out_dir = (root / data["paths"]["out_dir"]).resolve()
    log_dir = (root / data["paths"]["log_dir"]).resolve()

    logging_cfg = data.get("logging", {})
    log_level = logging_cfg.get("level", "INFO")
    log_file_name = logging_cfg.get("file_name", "run.log")
    log_file = (log_dir / log_file_name).resolve()

    parsing_cfg = data.get("parsing", {})
    exts = tuple(parsing_cfg.get("input_extensions", [".xlsx", ".xls", ".pdf"]))

    return AppConfig(
        root=root,
        shared_dictionaries_dir=shared_dir,
        in_dir=in_dir,
        out_dir=out_dir,
        log_dir=log_dir,
        log_file=log_file,
        log_level=log_level,
        input_extensions=exts,
    )
