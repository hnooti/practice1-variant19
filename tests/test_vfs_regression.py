"""Check ZIP loading and listing after the complexity refactor."""

import tempfile
import unittest
import zipfile
from pathlib import Path

from emulator.vfs import VFSLoadError, VirtualFileSystem


class ArchiveRegressionTests(unittest.TestCase):
    def test_direct_children_sorted_and_marked(self):
        vfs = VirtualFileSystem.empty()
        vfs.directories.update({"/a", "/a/deep", "/b", "/b/a"})
        vfs.files.update({"/a/file": b"data", "/z": b"z"})
        self.assertEqual(vfs.list_dir("/"), ["a/", "b/", "z"])
        self.assertEqual(vfs.list_dir("/a"), ["deep/", "file"])
        self.assertEqual(vfs.list_dir("/a/deep"), [])
        self.assertEqual(vfs.list_dir("/a/../b/"), ["a/"])

    def test_implicit_parents_and_binary_content(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "vfs.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("file/parent/data", bytes(range(256)))
                output.writestr("directory/parent/leaf/", b"")
            vfs = VirtualFileSystem.from_zip(str(archive))
            self.assertEqual(vfs.list_dir("/"), ["directory/", "file/"])
            self.assertEqual(vfs.list_dir("/file"), ["parent/"])
            self.assertEqual(vfs.list_dir("/file/parent"), ["data"])
            self.assertEqual(vfs.files["/file/parent/data"], bytes(range(256)))
            self.assertIn("/directory/parent", vfs.directories)

    def test_collision_does_not_replace_existing_state(self):
        for names in [("a", "a/b"), ("a", "a/")]:
            with self.subTest(names=names):
                with tempfile.TemporaryDirectory() as directory:
                    archive = Path(directory) / "conflict.zip"
                    with zipfile.ZipFile(archive, "w") as output:
                        for name in names:
                            output.writestr(name, b"")
                    vfs = VirtualFileSystem.empty()
                    vfs.files["/old"] = b"original"
                    with self.assertRaises(VFSLoadError):
                        vfs.load_zip(str(archive))
                    self.assertEqual(vfs.files, {"/old": b"original"})
                    self.assertEqual(vfs.directories, {"/"})

    def test_successful_reload_replaces_old_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "new.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("new", b"new")
            vfs = VirtualFileSystem.empty()
            vfs.files["/old"] = b"old"
            vfs.load_zip(str(archive))
            self.assertEqual(vfs.files, {"/new": b"new"})
            self.assertEqual(vfs.directories, {"/"})


if __name__ == "__main__":
    unittest.main()
