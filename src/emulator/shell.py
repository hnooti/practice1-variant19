from __future__ import annotations
import calendar
import getpass
import platform
import shlex
import socket
import time
from dataclasses import dataclass
from pathlib import Path


class ShellCommandError(Exception):
    pass


@dataclass
class ShellResult:
    should_exit: bool = False


class ShellEmulator:

    def __init__(self):
        self.cwd = "/"
        self.started_at = time.monotonic()
        self.username = getpass.getuser() or "user"
        self.hostname = socket.gethostname() or "host"

    def prompt(self) -> str:
        display = "~" if self.cwd == "/" else self.cwd
        return f"{self.username}@{self.hostname}:{display}$ "

    def parse(self, line: str) -> list[str]:
        try:
            return shlex.split(line, posix=True)
        except ValueError as exc:
            raise ShellCommandError(
                f"ошибка разбора аргументов: {exc}"
            ) from exc

    def execute(self, line: str) -> ShellResult:
        tokens = self.parse(line)
        if not tokens:
            return ShellResult()
        command, *args = tokens
        handlers = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
        }
        handler = handlers.get(command)
        if handler is None:
            raise ShellCommandError(f"{command}: неизвестная команда")
        return handler(args)

    @staticmethod
    def _require_arg_count(
        command: str, args: list[str], minimum: int, maximum: int | None = None
    ):
        if len(args) < minimum or (
            maximum is not None and len(args) > maximum
        ):
            if minimum == maximum:
                raise ShellCommandError(
                    f"{command}: ожидается аргументов: {minimum}"
                )
            raise ShellCommandError(
                f"{command}: неверное количество аргументов"
            )

    def cmd_ls(self, args: list[str]) -> ShellResult:
        print("ls", *args)
        return ShellResult()

    def cmd_cd(self, args: list[str]) -> ShellResult:
        print("cd", *args)
        return ShellResult()

    def cmd_exit(self, args: list[str]) -> ShellResult:
        self._require_arg_count("exit", args, 0, 0)
        return ShellResult(should_exit=True)

    def repl(self) -> None:
        while True:
            try:
                line = input(self.prompt())
            except (EOFError, KeyboardInterrupt):
                print()
                break
            try:
                result = self.execute(line)
            except ShellCommandError as exc:
                print(f"error: {exc}")
                continue
            if result.should_exit:
                break
