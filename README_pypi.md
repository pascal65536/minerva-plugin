### Как использовать

Любой пользователь может установить плагин одной командой:

```bash
pip install minerva-plugin
```

После установки плагин автоматически интегрируется с Flake8:

```bash
flake8 your_code.py
```

Проверить, что плагин подхватился:

```bash
flake8 --version
# В выводе должна быть строка: MN: 2.1.0
```

---

### Что делать при следующем обновлении

Когда добавите новые правила или исправите баги:

1. **Обновите версию в трёх местах**:
   - `setup.py`: `version="2.2.0"`
   - `pyproject.toml`: `version = "2.2.0"`
   - `minerva_plugin/__init__.py`: `version = "2.2.0"`

2. **Пересоберите пакет**:
   ```bash
   rm -rf build/ dist/ *.egg-info
   python -m build
   ```

3. **Загрузите на PyPI**:
   ```bash
   twine upload --username __token__ --password "$(cat ~/.pypi_token)" dist/*
   ```
