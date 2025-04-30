"""
Вспомогательные методы
"""


def escape_special_characters(input_string):
    # Словарь с заменами
    special_characters = {
        "\\": "\\\\",
        "\"": "\\\"",
        "\'": "\\\'",
        "\n": "\\n",
        "\t": "\\t",
        "\r": "\\r",
        "/": "_",
        "!": "_",
    }

    # Проход по строке и замена символов
    for character, escaped in special_characters.items():
        input_string = input_string.replace(character, escaped)

    return input_string
