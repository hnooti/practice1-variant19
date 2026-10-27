from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import zipfile


class VFSError(Exception):
    """Base error for virtual file system operations."""


class VFSLoadError(VFSError):
    """Raised when a ZIP archive cannot be loaded."""


@dataclass
class VirtualFileSystem:
    """A tiny in-memory VFS loaded from a ZIP archive.

    Files are stored as bytes. Directories are stored as normalized POSIX paths.
    All modifications made by commands such as touch/rmdir exist only in memory.
    """

    files: dict[str, bytes]
    directories: set[str]

    @classmethod
    def empty(cls) -> "VirtualFileSystem":
        return cls(files={}, directories={"/"})

    @classmethod
    def from_zip(cls, archive_path: str) -> "VirtualFileSystem":
        vfs = cls.empty()
        vfs.load_zip(archive_path)
        return vfs

    @staticmethod
    def _norm(path: str) -> str:
        if not path:
            return "/"
        p = PurePosixPath("/" + path.lstrip("/"))
        parts: list[str] = []
        for part in p.parts:
            if part in ("", "/"):
                continue
            if part == ".":
                continue
            if part == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(part)
        return "/" + "/".join(parts) if parts else "/"

    def resolve(self, cwd: str, path: str | None = None) -> str:
        if path is None or path == "":
            return self._norm(cwd)
        if path.startswith("/"):
            return self._norm(path)
        return self._norm(cwd.rstrip("/") + "/" + path)

    def _ensure_parents(self, path: str) -> None:
        p = PurePosixPath(path)
        current = "/"
        self.directories.add("/")
        for part in p.parts[:-1]:
            if part == "/":
                continue
            current = self._norm(current.rstrip("/") + "/" + part)
            self.directories.add(current)

    def load_zip(self, archive_path: str) -> None:
        """Load a ZIP atomically, keeping the old VFS on failure."""
        try:
            with zipfile.ZipFile(archive_path, "r") as archive:
                new_files, new_dirs = self._read_archive(archive)
        except FileNotFoundError as exc:
            raise VFSLoadError(f"файл VFS не найден: {archive_path}") from exc
        except zipfile.BadZipFile as exc:
            raise VFSLoadError(
                f"неверный формат VFS (ожидался ZIP): {archive_path}"
            ) from exc
        except OSError as exc:
            raise VFSLoadError(f"ошибка чтения VFS: {exc}") from exc

        if new_dirs.intersection(new_files):
            raise VFSLoadError("путь одновременно является файлом и каталогом")
        self.files = new_files
        self.directories = new_dirs

    def _read_archive(
        self, archive: zipfile.ZipFile
    ) -> tuple[dict[str, bytes], set[str]]:
        """Read entries and infer directories omitted from the ZIP."""
        bad = archive.testzip()
        if bad is not None:
            raise VFSLoadError(f"поврежден файл внутри ZIP: {bad}")
        files: dict[str, bytes] = {}
        directories = {"/"}
        for info in archive.infolist():
            normalized = self._norm(info.filename)
            if normalized == "/":
                continue
            parents = PurePosixPath(normalized).parents
            directories.update(str(parent) for parent in parents)
            if info.is_dir():
                directories.add(normalized)
            else:
                files[normalized] = archive.read(info.filename)
        return files, directories

    def exists(self, path: str) -> bool:
        path = self._norm(path)
        return path in self.directories or path in self.files

    def is_dir(self, path: str) -> bool:
        return self._norm(path) in self.directories

    def list_dir(self, path: str) -> list[str]:
        """Return direct children, marking directory names with a slash."""
        path = self._norm(path)
        if path not in self.directories:
            raise VFSError(f"нет такого каталога: {path}")
        names = self._child_names(self.directories, path, "/")
        names.update(self._child_names(self.files, path, ""))
        return sorted(names, key=lambda name: name.rstrip("/"))

    @staticmethod
    def _child_names(paths, parent: str, suffix: str) -> set[str]:
        """Select entries whose immediate parent matches the given path."""
        names: set[str] = set()
        for path in paths:
            entry = PurePosixPath(path)
            if entry.name and str(entry.parent) == parent:
                names.add(entry.name + suffix)
        return names

    def make_file(self, path: str) -> None:
        path = self._norm(path)
        if path in self.directories:
            raise VFSError(
                f"нельзя создать файл: каталог уже существует: {path}"
            )
        parent = str(PurePosixPath(path).parent)
        if parent not in self.directories:
            raise VFSError(f"нет такого каталога: {parent}")
        self.files[path] = self.files.get(path, b"")

    def remove_dir(self, path: str) -> None:
        path = self._norm(path)
        if path == "/":
            raise VFSError("нельзя удалить корневой каталог")
        if path not in self.directories:
            raise VFSError(f"нет такого каталога: {path}")

        prefix = path.rstrip("/") + "/"
        has_children = any(
            d != path and d.startswith(prefix) for d in self.directories
        )
        has_files = any(f.startswith(prefix) for f in self.files)
        if has_children or has_files:
            raise VFSError(f"каталог не пуст: {path}")

        self.directories.remove(path)
