"""
password_checker.py
===================
Function for assessing the strength of a password string.
"""


def check_strength(password: str) -> str:
    """Return the strength of a password as "weak", "medium", or "strong".

    Classification rules (applied in this order):
      1. "weak"   -- the password is strictly shorter than 8 characters
                     (i.e., length 0 through 7 inclusive gives "weak").
      2. "strong" -- the password is at least 12 characters long AND satisfies
                     ALL FOUR of the following character-class requirements:
                       - at least one lowercase ASCII letter (a-z)
                       - at least one uppercase ASCII letter (A-Z)
                       - at least one ASCII digit (0-9)
                       - at least one symbol, defined as any printable non-alphanumeric
                         ASCII character (i.e., any character in string.punctuation,
                         for example: ! @ # $ % ^ & * ( ) - _ = + etc.)
                     A password of exactly 12 characters that meets all four requirements
                     is "strong".  Length alone (>= 12) is not sufficient.
      3. "medium" -- every password that is not "weak" and not "strong".
                     This includes passwords of length 8 to 11, and passwords of
                     length >= 12 that are missing one or more character classes.

    Parameters
    ----------
    password : str
        The password string to evaluate.

    Returns
    -------
    str
        One of "weak", "medium", or "strong".

    Raises
    ------
    TypeError
        If ``password`` is not a str.

    Examples
    --------
    >>> check_strength("abc")
    'weak'
    >>> check_strength("abcdefgh")
    'medium'
    >>> check_strength("Abcdefgh1!")
    'medium'
    >>> check_strength("Abcdefgh12!")
    'strong'
    >>> check_strength("")
    'weak'
    """
    if not isinstance(password, str):
        raise TypeError(f"password must be a str, got {type(password).__name__}")

    if len(password) < 8:
        return "weak"

    if len(password) >= 12:
        has_lower  = any(c.islower() for c in password)
        has_upper  = any(c.isupper() for c in password)
        has_digit  = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() and c.isprintable() for c in password)
        if has_lower and has_upper and has_digit and has_symbol:
            return "strong"

    return "medium"
