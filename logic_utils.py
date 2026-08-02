def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"
    """
    if guess == secret:
        return "Win", "🎉 Correct!"

    # FIX: Hint messages were swapped, fixed with Claude Code and verified with new tests
    try:
        if guess > secret:
            return "Too High", "📉 Go LOWER!"
        else:
            return "Too Low", "📈 Go HIGHER!"
    except TypeError:
        g = str(guess)
        if g == secret:
            return "Win", "🎉 Correct!"
        if g > secret:
            return "Too High", "📉 Go LOWER!"
        return "Too Low", "📈 Go HIGHER!"


def get_proximity_hint(guess, secret):
    """
    Return a Hot/Cold proximity message based on how close guess is to secret.

    - difference <= 5:  "🔥 Very Hot!"
    - difference <= 15: "🌡️ Warm"
    - otherwise:        "❄️ Cold"
    """
    diff = abs(int(guess) - int(secret))
    if diff <= 5:
        return "🔥 Very Hot!"
    if diff <= 15:
        return "🌡️ Warm"
    return "❄️ Cold"


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")

