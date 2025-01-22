def is_positive_number_as_str(value: str) -> str:
    if not value.isnumeric():
        raise ValueError("Value must be a positive number.")

    return value
