# utils.py
def money(value: float) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = 0.0
    # Формат: 12 345 678.00
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")

def format_number_for_edit(value: float) -> str:
    """Формат числа с пробелами как разрядностью для полей ввода: 1 000 000 или 1 000 000,50."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return ""
    if v == int(v):
        return f"{int(v):,}".replace(",", " ")
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")

def to_float(text: str) -> float:
    if not text:
        return 0.0
    # поддержим ввод с пробелами и запятыми
    t = text.strip().replace(" ", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return 0.0
