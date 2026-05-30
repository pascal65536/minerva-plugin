## Установка и компиляция плагина 

### Вариант 1: Установка в режиме разработки

```bash
# Находясь в директории с setup.py:
pip install -e .
```

**Преимущества:**
- ✅ Изменения в коде применяются немедленно (без переустановки)
- ✅ Плагин доступен в текущем виртуальном окружении
- ✅ Идеально для тестирования с flake8

### Вариант 2: Классическая установка через setup.py

```bash
# Установка в окружение
python setup.py install

# Или сборка без установки
python setup.py build

# Создание исходного дистрибутива
python setup.py sdist

# Создание wheel-пакета
python setup.py bdist_wheel
```

### Вариант 3: Сборка через pip

```bash
# Сборка и установка
pip install .

# Сборка wheel-файла
pip wheel .
```

---

## Проверка плагина

После установки проверьте, что flake8 видит ваш плагин:

```bash
# Проверка версии плагина
flake8 --version

# Ожидаемый вывод должен содержать:
# minerva-plugin: 1.0.0

# Тестирование на тестовом файле
echo "badVariableName = 1" > test.py
flake8 test.py

# Ожидаемый вывод:
# test.py:1:1: MN004 import of 're' is prohibited
# test.py:3:1: MN003 variable name must be in snake_case
# test.py:5:1: MN001 variable name too short (min 2 chars)
# test.py:6:1: MN001 variable name too short (min 2 chars)
# test.py:11:1: MN002 variable name too long (max 40 chars)
```

### 1. Структура пакета

Убедитесь, что структура директорий соответствует `find_packages()`:

```
minerva-plugin/
├── setup.py
├── minerva_plugin/
│   ├── __init__.py
│   └── minerva.py
└── ...
```

### 2. Зависимости

Плагин требует `flake8>=3.8.0`. Убедитесь, что flake8 установлен в окружении:

```bash
pip install flake8>=3.8.0
pip install -e .
```

