import ast
import re
import os
import json


def load_json(folder_name_lst, file_name, default=None):
    if default is None:
        default = {}
    if isinstance(folder_name_lst, str):
        folder_name = folder_name_lst
    elif isinstance(folder_name_lst, list):
        folder_name = os.path.join(*folder_name_lst)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    filename = os.path.join(folder_name, file_name)
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=True)
    with open(filename, encoding="utf-8") as f:
        load_dct = json.load(f)
    return load_dct


def save_json(folder_name_lst, file_name, save_dct):
    if isinstance(folder_name_lst, str):
        folder_name = folder_name_lst
    elif isinstance(folder_name_lst, list):
        folder_name = os.path.join(*folder_name_lst)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    filename = os.path.join(folder_name, file_name)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(save_dct, f, ensure_ascii=False, indent=4)


class Minerva:
    """
    Основной класс плагина Minerva.
    """

    name = "minerva"
    version = "2.1.1"
    directory = "settings"
    filename = "plugin.json"

    def __init__(self, tree: ast.AST, filename: str, lines=None):
        self.tree = tree
        self.filename = filename
        if lines is None:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    self.lines = f.readlines()
            except (OSError, IOError):
                self.lines = []
        else:
            self.lines = lines

    @classmethod
    def add_options(cls, parser):
        """
        Регистрация настроек в flake8
        """
        settings = cls.load_settings()

        parser.add_option(
            "--min-var-length",
            action="store",
            type=int,
            default=settings.get("min_length", 2),
            parse_from_config=True,
            help="Минимальная длина имени переменной",
        )
        parser.add_option(
            "--max-var-length",
            action="store",
            type=int,
            default=settings.get("max_length", 40),
            parse_from_config=True,
            help="Максимальная длина имени переменной",
        )
        parser.add_option(
            "--allowed-single-letters",
            action="store",
            type=str,
            default=settings.get("allowed_single_letters", "i,j,x,y,e"),
            parse_from_config=True,
            help="Разрешенные однобуквенные имена через запятую",
        )
        parser.add_option(
            "--enforce-snake-case",
            action="store_true",
            default=settings.get("enforce_snake_case", True),
            parse_from_config=True,
            help="Требовать snake_case для имен переменных",
        )
        parser.add_option(
            "--prohibited-modules",
            action="store",
            type=str,
            default=settings.get("prohibited_modules", "math,re"),
            parse_from_config=True,
            help="Запрещенные модули для импорта через запятую",
        )
        parser.add_option(
            "--max-line-length-custom",
            action="store",
            type=int,
            default=settings.get("max_line_length", 123),
            parse_from_config=True,
            help="Максимальная длина строки (MN005)",
        )
        parser.add_option(
            "--max-char-code",
            action="store",
            type=int,
            default=settings.get("max_char_code", 1000),
            parse_from_config=True,
            help="Максимальный допустимый код символа в строке (MN006)",
        )
        parser.add_option(
            "--prohibited-constructors",
            action="store",
            type=str,
            default=settings.get("prohibited_constructors", "list,set"),
            parse_from_config=True,
            help="Запрещенные конструкторы через запятую (MN007)",
        )
        parser.add_option(
            "--allowed-collections",
            action="store",
            type=str,
            default=settings.get("allowed_collections", ""),
            parse_from_config=True,
            help="Белый список коллекций через запятую (MN008)",
        )
        parser.add_option(
            "--check-constructor",
            action="store",
            type=str,
            default=settings.get("check_constructor", ""),
            parse_from_config=True,
            help="Типы коллекций, которые должны создаваться через литерал (MN009)",
        )

    @classmethod
    def parse_options(cls, options):
        """
        Парсинг полученных опций
        """
        cls.min_length = options.min_var_length
        cls.max_length = options.max_var_length
        cls.allowed_single_letters = set(
            letter.strip() for letter in options.allowed_single_letters.split(",")
        )
        cls.enforce_snake_case = options.enforce_snake_case
        cls.prohibited_modules = set(
            mod.strip() for mod in options.prohibited_modules.split(",") if mod.strip()
        )
        cls.max_line_length = options.max_line_length_custom
        cls.max_char_code = options.max_char_code
        cls.prohibited_constructors = set(
            c.strip() for c in options.prohibited_constructors.split(",") if c.strip()
        )
        cls.allowed_collections = set(
            c.strip() for c in options.allowed_collections.split(",") if c.strip()
        )
        cls.check_constructor = set(
            c.strip() for c in options.check_constructor.split(",") if c.strip()
        )

    def run(self):
        """
        Генератор нарушений
        """
        settings = self.load_settings()
        visitor = MinervaVisitor(**settings)
        visitor.check_lines(self.lines)
        visitor.visit(self.tree)
        for violation in visitor.violations:
            yield violation

    @classmethod
    def load_settings(cls):
        """
        Загрузка настроек из файла
        """
        settings = load_json(cls.directory, cls.filename)
        if settings == {}:
            settings["min_length"] = 2
            settings["max_length"] = 40
            settings["allowed_single_letters"] = "i,j,x,y,e"
            settings["enforce_snake_case"] = True
            settings["prohibited_modules"] = "math,re"
            settings["max_line_length"] = 123
            settings["max_char_code"] = 1000
            settings["prohibited_constructors"] = "list,set"
            settings["allowed_collections"] = "dict"
            settings["check_constructor"] = "list,dict"
            save_json(cls.directory, cls.filename, settings)
        return settings


class MinervaVisitor(ast.NodeVisitor):
    """
    Визитор AST дерева для проверки имен, импортов, строк и коллекций
    """

    def __init__(
        self,
        min_length,
        max_length,
        allowed_single_letters,
        enforce_snake_case,
        prohibited_modules,
        max_line_length=123,
        max_char_code=1000,
        prohibited_constructors="list,set",
        allowed_collections="",
        check_constructor="",
    ):
        self.violations = list()
        self.min_length = min_length
        self.max_length = max_length
        self.max_line_length = max_line_length
        self.max_char_code = max_char_code

        self.allowed_single_letters = (
            set(letter.strip() for letter in allowed_single_letters.split(","))
            if isinstance(allowed_single_letters, str)
            else allowed_single_letters
        )

        self.enforce_snake_case = enforce_snake_case

        self.prohibited_modules = (
            set(mod.strip() for mod in prohibited_modules.split(",") if mod.strip())
            if isinstance(prohibited_modules, str)
            else prohibited_modules
        )

        self.prohibited_constructors = (
            set(c.strip() for c in prohibited_constructors.split(",") if c.strip())
            if isinstance(prohibited_constructors, str)
            else prohibited_constructors
        )

        self.allowed_collections = (
            set(c.strip() for c in allowed_collections.split(",") if c.strip())
            if isinstance(allowed_collections, str) and allowed_collections.strip()
            else set()
        )

        self.check_constructor = (
            set(c.strip() for c in check_constructor.split(",") if c.strip())
            if isinstance(check_constructor, str) and check_constructor.strip()
            else set()
        )

        self.snake_case_pattern = re.compile(r"^_?[a-z][a-z0-9_]*$")

    def check_lines(self, lines):
        """
        Проверка строк исходного кода (вне AST).
        - MN005: строка длиннее max_line_length
        - MN006: в строке есть символ с кодом > max_char_code
        """
        if not lines:
            return

        for lineno, line in enumerate(lines, start=1):
            stripped = line.rstrip("\n\r")
            if self.max_line_length and len(stripped) > self.max_line_length:
                msg = (
                    f"MN005 line too long "
                    f"({len(stripped)} > {self.max_line_length} characters)"
                )
                candidate = (lineno, self.max_line_length, msg, Minerva)
                if candidate not in self.violations:
                    self.violations.append(candidate)

            if self.max_char_code and stripped:
                max_code = max(ord(z) for z in stripped)
                if max_code > self.max_char_code:
                    col = stripped.index(chr(max_code))
                    msg = (
                        f"MN006 suspicious character U+{max_code:04X} "
                        f"(code {max_code} > {self.max_char_code})"
                    )
                    candidate = (lineno, col, msg, Minerva)
                    if candidate not in self.violations:
                        self.violations.append(candidate)

    def _check_name(self, name, lineno, col_offset):
        if not name:
            return

        if name.startswith("__") and name.endswith("__"):
            return

        if len(name) < self.min_length:
            if name not in self.allowed_single_letters:
                msg = f"MN001 variable name too short (min {self.min_length} chars)"
                candidate = (lineno, col_offset, msg, Minerva)
                if candidate not in self.violations:
                    self.violations.append(candidate)
                return

        if len(name) > self.max_length:
            msg = f"MN002 variable name too long (max {self.max_length} chars)"
            candidate = (lineno, col_offset, msg, Minerva)
            if candidate not in self.violations:
                self.violations.append(candidate)
            return

        if name.isupper():
            return

        if self.enforce_snake_case:
            if not self.snake_case_pattern.match(name):
                msg = "MN003 variable name must be in snake_case"
                candidate = (lineno, col_offset, msg, Minerva)
                if candidate not in self.violations:
                    self.violations.append(candidate)

    def _check_import(self, module_name, lineno, col_offset):
        """
        Проверка модуля на наличие в списке ЗАПРЕЩЕННЫХ (Black List)
        """
        if not self.prohibited_modules:
            return

        base_module = module_name.split(".")[0]

        if base_module in self.prohibited_modules:
            msg = f"MN004 import of '{base_module}' is prohibited"
            candidate = (lineno, col_offset, msg, Minerva)
            if candidate not in self.violations:
                self.violations.append(candidate)

    def _check_constructor_call(self, node, constructor_name):
        """
        Проверка вызова конструктора коллекции.
        - MN007: конструктор в списке запрещенных
        - MN009: тип в check_constructor должен создаваться через литерал
        """
        if constructor_name in self.prohibited_constructors:
            msg = f"MN007 use of prohibited constructor: {constructor_name}()"
            candidate = (node.lineno, node.col_offset, msg, Minerva)
            if candidate not in self.violations:
                self.violations.append(candidate)

        if constructor_name in self.check_constructor:
            msg = f"MN009 {constructor_name} must be created via literal, not constructor"
            candidate = (node.lineno, node.col_offset, msg, Minerva)
            if candidate not in self.violations:
                self.violations.append(candidate)

    def _check_literal(self, node, collection_type):
        """
        Проверка литерала коллекции.
        - MN008: тип не в белом списке (если задан)
        """
        if self.allowed_collections:
            if collection_type not in self.allowed_collections:
                allowed_str = ", ".join(sorted(self.allowed_collections))
                msg = (
                    f"MN008 use of non-allowed collection type '{collection_type}'. "
                    f"Allowed types: {allowed_str}"
                )
                candidate = (node.lineno, node.col_offset, msg, Minerva)
                if candidate not in self.violations:
                    self.violations.append(candidate)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self._check_import(alias.name, node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self._check_import(node.module, node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self._check_name(node.id, node.lineno, node.col_offset)
        else:
            self.generic_visit(node)

    def visit_arg(self, node: ast.arg):
        self._check_name(node.arg, node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self._visit_target(node.target)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self._visit_target(node.target)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            self._visit_target(target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            self._check_name(node.target.id, node.target.lineno, node.target.col_offset)
        else:
            self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr):
        if isinstance(node.target, ast.Name):
            self._check_name(node.target.id, node.target.lineno, node.target.col_offset)
        else:
            self.generic_visit(node)

    def _visit_target(self, target: ast.expr):
        """
        Рекурсивный обход целей присваивания
        """
        if isinstance(target, ast.Name):
            self._check_name(target.id, target.lineno, target.col_offset)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._visit_target(elt)

    def visit_Call(self, node: ast.Call):
        """
        Вызовы конструкторов: list(), dict(), set()
        """
        if isinstance(node.func, ast.Name) and node.func.id in (
            "list", "dict", "set"
        ):
            self._check_constructor_call(node, node.func.id)
        self.generic_visit(node)

    def visit_List(self, node: ast.List):
        """
        Литерал списка: [1, 2, 3]
        """
        self._check_literal(node, "list")
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict):
        """
        Литерал словаря: {"a": 1}
        """
        self._check_literal(node, "dict")
        self.generic_visit(node)

    def visit_Set(self, node: ast.Set):
        """
        Литерал множества: {1, 2, 3}
        """
        self._check_literal(node, "set")
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp):
        """
        List comprehension: [x for x in ...]
        """
        self._check_literal(node, "list")
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp):
        """
        Dict comprehension: {k: v for ...}
        """
        self._check_literal(node, "dict")
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp):
        """
        Set comprehension: {x for x in ...}
        """
        self._check_literal(node, "set")
        self.generic_visit(node)