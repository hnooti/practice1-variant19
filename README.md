# Практическое задание №1, вариант №19

Этап 4.

Требуется Python 3.10+, внешних зависимостей нет.
Все команды запуска выполняются из корневой папки этого проекта.

Интерактивный запуск:

```bash
bash run.sh
```

Запуск демонстрационного сценария с настройками из JSON:

```bash
bash run.sh --config config/default.json
```

Запуск с виртуальной файловой системой для ручного ввода команд:

```bash
bash run.sh --vfs vfs/sample_vfs.zip
```

`run.sh` сначала создаёт ZIP-архивы из JSON-манифестов,
а затем запускает пакет через `python3 -m emulator`.
При прямом запуске пакета сначала подготовьте архивы:

```bash
python3 scripts/build_vfs.py
PYTHONPATH=src python3 -m emulator --config config/default.json
```

`src/emulator/__main__.py` использует относительные импорты:
запускайте пакет указанными командами или настройкой модуля `emulator`
в PyCharm, а не как отдельный Python-файл.

Проверка виртуальной файловой системы:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Команды: cal, cd, exit, ls, uname, uptime.
