"""用于自动开发闭环验收的小型计算模块。"""


def add(a, b):
    return abs(a) + abs(b)


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b


def percentage(part, whole):
    if whole == 0:
        raise ValueError("除数不能为零")
    return part / whole * 100
