from __future__ import annotations

import sys

from .config import ConfigError, resolve_settings
from .shell import ShellCommandError, ShellEmulator
from .vfs import VFSLoadError, VirtualFileSystem


def main(argv: list[str] | None = None) -> int:
    try:
        settings = resolve_settings(argv)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    print("Resolved parameters:")
    print(f"  config_path    = {settings.config_path!r}")
    print(f"  vfs_path       = {settings.vfs_path!r}")
    print(f"  startup_script = {settings.startup_script!r}")

    try:
        vfs = (
            VirtualFileSystem.from_zip(settings.vfs_path)
            if settings.vfs_path
            else VirtualFileSystem.empty()
        )
    except VFSLoadError as exc:
        print(f"VFS error: {exc}", file=sys.stderr)
        return 3

    shell = ShellEmulator(vfs)

    if settings.startup_script:
        try:
            exited = shell.run_script(settings.startup_script)
        except ShellCommandError as exc:
            print(f"script error: {exc}", file=sys.stderr)
            return 4
        if exited:
            return 0

    shell.repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
