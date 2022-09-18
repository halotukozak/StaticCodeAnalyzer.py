import itertools
import os
import re
import sys
import ast


class SyntaxException(Exception):

    def __init__(self, number, line_index, name=None):
        self.line_index = line_index
        self.number = number
        if number == "S001":
            self.message = "Too long"
        elif number == "S002":
            self.message = "Indentation is not a multiple of four"
        elif number == "S003":
            self.message = "Unnecessary semicolon after a statement"
        elif number == "S004":
            self.message = "Less than two spaces before inline comments"
        elif number == "S005":
            self.message = "TODO found"
        elif number == "S006":
            self.message = "More than two blank lines preceding a code line"
        elif number == "S007":
            self.message = f"Too many spaces after '{name}'"
        elif number == "S008":
            self.message = f"Class name '{name}' should be written in CamelCase"
        elif number == "S009":
            self.message = f"Function name '{name}' should be written in snake_case"
        elif number == "S010":
            self.message = f"Argument name {name} should be written in snake_case"
        elif number == "S011":
            self.message = f"Variable {name} should be written in snake_case"
        elif number == "S012":
            self.message = f"The default argument value is mutable"

    def __str__(self):
        return f'Line {self.line_index}: {self.number} {self.message}'

    def __eq__(self, other):
        return self.number == other.line_index

    def __lt__(self, other):
        return self.line_index < other.line_index

    def __gt__(self, other):
        return self.line_index > other.line_index

    def __le__(self, other):
        return self.line_index <= other.line_index

    def __ge__(self, other):
        return self.line_index >= other.line_index


def too_long(line):
    return len(line) > 79


def indentation_not_dividable_by_four(line):
    return (len(line) - len(line.lstrip(' '))) % 4 != 0


def unnecessary_semicolon(line):
    return line.split('#')[0].strip().endswith(';')


def not_enough_spaces_before_inline_comment(line):
    return '#' in line and not line.startswith("#") and not line.split('#')[0].endswith('  ')


def todo_in_comment(line):
    return "#" in line and "TODO" in line.split("#")[1].upper()


def too_many_spaces_after_constructor(line):
    return re.match(r' *(class|def) {2,}\w+', line)


def valid_camel_case(name):
    return re.match(r'^([A-Z][a-z]*)+?$', name)


def valid_snake_case(name):
    return re.match(r'^[a-z_]+', name)


args = sys.argv[1:]
paths = []
for path in args:
    if os.path.isfile(path) and path.endswith(".py"):
        paths.append(path)
    else:
        paths += [path + "/" + new_path for new_path in os.listdir(path) if new_path.endswith(".py")]

error_bags = {}

for path in paths:
    error_bag = []
    file = open(path, "r")
    file_content = file.read()
    tree = ast.parse(file_content)
    blank_lines = 0
    for i, line in enumerate(file_content.splitlines(), start=1):
        if len(line) > 0:
            if too_long(line):
                error_bag.append(SyntaxException("S001", i))
            if indentation_not_dividable_by_four(line):
                error_bag.append(SyntaxException("S002", i))
            if unnecessary_semicolon(line):
                error_bag.append(SyntaxException("S003", i))
            if not_enough_spaces_before_inline_comment(line):
                error_bag.append(SyntaxException("S004", i))
            if todo_in_comment(line):
                error_bag.append(SyntaxException("S005", i))
            if blank_lines > 2:
                error_bag.append(SyntaxException("S006", i))
            if too_many_spaces_after_constructor(line):
                name = re.search(r'(def|class) +(\w+).*$', line).group(2)
                error_bag.append(SyntaxException("S007", i, name))

            blank_lines = 0
        else:
            blank_lines += 1
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_name = node.name
            if not valid_snake_case(function_name):
                error_bag.append(SyntaxException("S009", node.lineno, function_name))

            for arg in node.args.args:
                arg_name = arg.arg
                if not valid_snake_case(arg_name):
                    error_bag.append(SyntaxException("S010", node.lineno, arg_name))
            for default in node.args.defaults:
                if not hasattr(default, "value"):
                    error_bag.append(SyntaxException("S012", node.lineno))
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            if not valid_camel_case(class_name):
                error_bag.append(SyntaxException("S008", node.lineno, class_name))

        if isinstance(node, ast.Attribute):
            value_name = node.attr
            if not valid_snake_case(value_name):
                error_bag.append(SyntaxException("S010", node.lineno, value_name))

        if isinstance(node, ast.Assign) and hasattr(node.targets[0], "id"):
            value_name = node.targets[0].id
            if not valid_snake_case(value_name):
                error_bag.append(SyntaxException("S011", node.lineno, value_name))

    file.close()
    error_bags[path] = error_bag

for path, error_bag in sorted(error_bags.items()):
    for error in sorted(error_bag):
        print(f'{path}:', error)
