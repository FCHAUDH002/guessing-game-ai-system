import os

from streamlit.testing.v1 import AppTest

from logic_utils import check_guess, get_proximity_hint

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.py")


def _button(at, label_substring):
    for b in at.button:
        if label_substring in b.label:
            return b
    raise AssertionError(f"No button with label containing {label_substring!r}")


def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result, hint = check_guess(50, 50)
    assert result == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result, hint = check_guess(60, 50)
    assert result == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result, hint = check_guess(40, 50)
    assert result == "Too Low"

def test_hint_direction_too_low():
    # If secret is 50 and guess is 40, hint should say to go higher
    result, hint = check_guess(40, 50)
    assert result == "Too Low"
    assert "HIGHER" in hint.upper()

def test_hint_direction_too_high():
    # If secret is 50 and guess is 60, hint should say to go lower
    result, hint = check_guess(60, 50)
    assert result == "Too High"
    assert "LOWER" in hint.upper()


def test_proximity_very_hot_at_zero():
    # Exact distance of 0 is well within the "very hot" band
    assert get_proximity_hint(50, 50) == "🔥 Very Hot!"

def test_proximity_very_hot_at_boundary_5():
    # Difference of exactly 5 is the inclusive upper edge of "very hot"
    assert get_proximity_hint(45, 50) == "🔥 Very Hot!"

def test_proximity_warm_just_past_5():
    # Difference of 6 falls out of "very hot" and into "warm"
    assert get_proximity_hint(44, 50) == "🌡️ Warm"

def test_proximity_warm_at_boundary_15():
    # Difference of exactly 15 is the inclusive upper edge of "warm"
    assert get_proximity_hint(35, 50) == "🌡️ Warm"

def test_proximity_cold_just_past_15():
    # Difference of 16 falls out of "warm" and into "cold"
    assert get_proximity_hint(34, 50) == "❄️ Cold"

def test_proximity_handles_string_secret():
    # The game stringifies the secret on even attempts; proximity must still work
    assert get_proximity_hint(48, "50") == "🔥 Very Hot!"

def test_new_game_button_resets_state(monkeypatch):
    import ai_coach
    monkeypatch.setattr(
        ai_coach, "generate_ai_coach_message",
        lambda *args, **kwargs: "Mocked coach message"
    )

    at = AppTest.from_file(APP_PATH)
    at.run()

    # Pin the secret so every guess we make is wrong (never an accidental win).
    at.session_state["secret"] = 50

    # Lose the round: keep submitting too-low guesses until attempts run out.
    for _ in range(20):
        if at.session_state["status"] != "playing":
            break
        at.text_input[0].set_value("1")
        _button(at, "Submit Guess").click()
        at.run()

    # Sanity check: we actually lost and state drifted away from a fresh game.
    assert at.session_state["status"] == "lost"
    assert at.session_state["score"] < 100
    assert at.session_state["history"] != []

    # Click "New Game" and confirm everything is reset.
    _button(at, "New Game").click()
    at.run()

    assert at.session_state["score"] == 100
    assert at.session_state["status"] == "playing"
    assert at.session_state["history"] == []

def test_check_guess_handles_stringified_secret_correctly():
    # Regression test: secret arrives as a string (as app.py does on even attempts),
    # guess is much higher than secret — must say "Too High"/"Go LOWER", not flip.
    outcome, message = check_guess(100, "14")
    assert outcome == "Too High"
    assert "LOWER" in message.upper()

def test_check_guess_handles_int_secret_correctly():
    outcome, message = check_guess(100, 14)
    assert outcome == "Too High"
    assert "LOWER" in message.upper()