import ast
import sys
from minerva_plugin import MinervaVisitor, load_json

# 1. Читаем настройки из settings/plugin.json
settings = load_json("settings", "plugin.json")
print(f"Загружены настройки: {settings}\n")

# 2. Читаем целевой файл
target_file = sys.argv[1] if len(sys.argv) > 1 else "test.py"
with open(target_file, "r", encoding="utf-8") as f:
    source_code = f.read()
    lines = source_code.splitlines(keepends=True)

# 3. Парсим AST и запускаем визитор
tree = ast.parse(source_code)
visitor = MinervaVisitor(**settings)

# Сначала проверяем строки, потом AST
visitor.check_lines(lines)
visitor.visit(tree)

# 4. Выводим результаты
print(f"Файл: {target_file}")
print(f"Найдено нарушений: {len(visitor.violations)}\n")
for lineno, col_offset, msg, _ in visitor.violations:
    print(f"{target_file}:{lineno}:{col_offset}: {msg}")
