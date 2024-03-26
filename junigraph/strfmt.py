"""Perform basic string manipulations."""


def truncate_path(path, max_length=30):
    """Truncate the length of a path."""
    if len(path) <= max_length:
        return path

    head = path[: max_length // 2 - 2]
    tail = path[-(max_length - len(head)) :]

    return head + "..." + tail


def insert_newline_after_comma_except_in_brackets(string):
    """Kind of what the name says."""
    result = ""
    inside_brackets = 0

    for char in string:
        if char == "[":
            inside_brackets += 1
            result += f"{char}\n.... "
            continue
        elif char == "]":
            inside_brackets -= 1
            result += f"\n{char}"
            continue

        if char == "," and inside_brackets == 0:
            result += ",\n"
        elif char == "," and (inside_brackets != 0):
            # indent using 4 spaces
            result += ",\n...."
        else:
            result += char

    return result


def format_dict(dict_instance):
    return insert_newline_after_comma_except_in_brackets(str(dict_instance))
