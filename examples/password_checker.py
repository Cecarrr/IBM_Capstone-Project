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
                       - at least one lowercase ASCII letter, defined as a character in
                         string.ascii_lowercase (a-z only; accented letters do NOT count)
                       - at least one uppercase ASCII letter, defined as a character in
                         string.ascii_uppercase (A-Z only)
                       - at least one ASCII digit, defined as a character in
                         string.digits (0-9 only)
                       - at least one symbol, defined as a character in
                         string.punctuation (printable non-alphanumeric ASCII;
                         a space does NOT count as a symbol)
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
    >>> check_strength("Abcdefgh123!")
    'strong'
    >>> check_strength("")
    'weak'
    """
    if not isinstance(password, str):
        raise TypeError(f"password must be a str, got {type(password).__name__}")

    if len(password) < 8:
        return "weak"

    if len(password) >= 12:
        import string as _string
        has_lower  = any(c in _string.ascii_lowercase for c in password)
        has_upper  = any(c in _string.ascii_uppercase for c in password)
        has_digit  = any(c in _string.digits for c in password)
        has_symbol = any(c in _string.punctuation for c in password)
        if has_lower and has_upper and has_digit and has_symbol:
            return "strong"

    return "medium"
