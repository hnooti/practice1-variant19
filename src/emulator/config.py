from __future__ import annotations

from dataclasses import dataclass
import argparse
import json


class ConfigError(Exception):
    pass


@dataclass
class Settings:
    vfs_path: str | None = None
    startup_script: str | None = None
    config_path: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m emulator",
        description="Эмулятор UNIX-подобной командной строки (вариант 19).",
    )
    parser.add_argument("--vfs", dest="vfs_path", help="путь к ZIP-архиву VFS")
    parser.add_argument(
        "--script", dest="startup_script", help="путь к стартовому скрипту"
    )
    parser.add_argument(
        "--config", dest="config_path", help="путь к JSON-конфигурации"
    )
    return parser


def _load_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise ConfigError(f"конфигурационный файл не найден: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"ошибка JSON в конфигурации: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"ошибка чтения конфигурации: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("конфигурация должна быть JSON-объектом")
    for key in ("vfs_path", "startup_script"):
        value = data.get(key)
        if value is not None and not isinstance(value, str):
            raise ConfigError(f"{key}: ожидается строка или null")
    return data


def resolve_settings(argv: list[str] | None = None) -> Settings:
    args = build_parser().parse_args(argv)

    file_cfg: dict = {}
    if args.config_path:
        file_cfg = _load_json(args.config_path)

    # CLI has higher priority than config file.
    vfs_path = (
        args.vfs_path
        if args.vfs_path is not None else file_cfg.get("vfs_path")
    )
    startup_script = (
        args.startup_script
        if args.startup_script is not None
        else file_cfg.get("startup_script")
    )

    return Settings(
        vfs_path=vfs_path,
        startup_script=startup_script,
        config_path=args.config_path,
    )
