import json
import ast
import re


def int_or_list(data: str):
    data = data.strip()
    if data.startswith("[") and data.endswith("]"):
        data_list = ast.literal_eval(data)
        for element in data_list:
            if not isinstance(element, int):
                raise TypeError(f"Inputted {data} is not a list of int or a single int")
        return data_list
    else:
        return int(data)


def bool_or_list(data: str):
    data = data.strip()
    if data.startswith("[") and data.endswith("]"):
        data_list = ast.literal_eval(data)
        for element in data_list:
            if not isinstance(element, bool):
                raise TypeError(f"Inputted {data} is not a list of int or a single int")
        return data_list
    else:
        try:
            data_eval = ast.literal_eval(data)
        except (ValueError, TypeError, SyntaxError):
            raise TypeError(f"Inputted {data} is not a list of int or a single int")
        if not isinstance(data_eval, bool):
            raise TypeError(f"Inputted {data} is not a list of int or a single int")
        return data_eval


def float_or_list(data: str):
    data = data.strip()
    if data.startswith("[") and data.endswith("]"):
        data_list = ast.literal_eval(data)
        for element in data_list:
            if not isinstance(element, float):
                raise TypeError(f"Inputted {data} is not a list of int or a single int")
        return data_list
    else:
        return float(data)


def json_or_str(data: str):
    try:
        return json.dumps(data)
    except json.JSONDecodeError:
        return str


def extract_parameters(docstring: str):
    """Extract parameters from a NumPy-style docstring as a list of tuples (name, type, description)."""
    pattern = r"Parameters\n-{10,}\n(.*?)(?=\n\S|\Z)"  # Match 'Parameters' section
    match = re.search(pattern, docstring, re.DOTALL)

    if not match:
        return {}

    params_text = match.group(1).strip()
    param_lines = params_text.split("\n")

    params = {}
    param_name, param_type, param_desc = None, None, []

    for line in param_lines:
        line = line.strip()
        if ": " in line:  # This line defines a parameter name and type
            if param_name:  # Store the previous parameter
                params[param_name] = (param_type, " ".join(param_desc).strip())

            param_name, param_type = map(str.strip, line.split(": ", 1))
            param_desc = []  # Reset description buffer
        else:
            param_desc.append(line)  # Append description lines

    if param_name:  # Store the last parameter
        params[param_name] = (param_type, " ".join(param_desc).strip())

    return params


def extract_description(docstring: str) -> str:
    """Extract everything before the 'Parameters' section in a NumPy-style docstring."""
    pattern = (
        r"^(.*?)(?=\nParameters\n-{10,})"  # Capture everything before 'Parameters'
    )
    match = re.search(pattern, docstring, re.DOTALL)
    return match.group(1).strip() if match else docstring.strip()


class BoolFlag:
    def __call__(self, *args, **kwargs):
        return
