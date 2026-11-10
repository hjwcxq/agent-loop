"""用于自动开发闭环验收的小型计算模块。"""


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def _validate_divisor(divisor):
    if divisor == 0:
        raise ValueError("除数不能为零")


def divide(a, b):
    _validate_divisor(b)
    return a / b


def percentage(part, whole):
    _validate_divisor(whole)
    return part / whole * 100


def clamp(value, minimum, maximum):
    if minimum > maximum:
        raise ValueError("minimum 不能大于 maximum")
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value
