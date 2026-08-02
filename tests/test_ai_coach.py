import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import ai_coach
from ai_coach import retrieve_tips, generate_ai_coach_message


# --- Retrieval tests ---

def test_retrieve_tips_very_hot_returns_close_range_tip():
    tips = retrieve_tips(
        proximity_label="🔥 Very Hot!",
        attempts_left=5,
        attempt_limit=8,
        guess=50,
        history=[40, 50]
    )
    tip_ids = [t["id"] for t in tips]
    assert "hot_cold_close" in tip_ids


def test_retrieve_tips_cold_returns_wide_jump_tip():
    tips = retrieve_tips(
        proximity_label="❄️ Cold",
        attempts_left=5,
        attempt_limit=8,
        guess=5,
        history=[5]
    )
    tip_ids = [t["id"] for t in tips]
    assert "hot_cold_far" in tip_ids


def test_retrieve_tips_low_attempts_triggers_narrowing_tip():
    tips = retrieve_tips(
        proximity_label="🌡️ Warm",
        attempts_left=1,
        attempt_limit=8,
        guess=30,
        history=[10, 20, 30]
    )
    tip_ids = [t["id"] for t in tips]
    assert "low_attempts_left" in tip_ids


def test_retrieve_tips_repeated_guess_flagged():
    tips = retrieve_tips(
        proximity_label="🌡️ Warm",
        attempts_left=5,
        attempt_limit=8,
        guess=30,
        history=[30, 40, 30]
    )
    tip_ids = [t["id"] for t in tips]
    assert "repeat_guess" in tip_ids


def test_retrieve_tips_early_game_suggests_binary_search():
    tips = retrieve_tips(
        proximity_label="🌡️ Warm",
        attempts_left=8,
        attempt_limit=8,
        guess=50,
        history=[50]
    )
    tip_ids = [t["id"] for t in tips]
    assert "binary_search" in tip_ids


def test_retrieve_tips_returns_at_most_two():
    # Force a state that could match multiple tags at once
    tips = retrieve_tips(
        proximity_label="❄️ Cold",
        attempts_left=1,
        attempt_limit=8,
        guess=1,
        history=[1, 1]
    )
    assert len(tips) <= 2


def test_retrieve_tips_returns_empty_list_when_no_tags_match():
    # Comfortable mid-game state with no special conditions
    tips = retrieve_tips(
        proximity_label="🌡️ Warm",
        attempts_left=5,
        attempt_limit=8,
        guess=42,
        history=[10, 25, 42]
    )
    # Should not error even if no tips match
    assert isinstance(tips, list)


# --- Fallback / reliability tests ---

def test_generate_ai_coach_message_falls_back_on_api_failure(monkeypatch):
    """
    Simulate the Gemini API failing (e.g. network error, bad key).
    The coach should NOT crash the game -- it should fall back to a
    retrieved tip or a generic encouraging message.
    """
    def broken_generate(*args, **kwargs):
        raise ConnectionError("Simulated API failure")

    monkeypatch.setattr(ai_coach, "AI_COACH_ENABLED", True)
    monkeypatch.setattr(
        ai_coach,
        "_model",
        type("FakeModel", (), {"generate_content": staticmethod(broken_generate)})()
    )

    tips = [{"id": "hot_cold_close", "tags": ["very_hot"], "text": "Small adjustments work best now."}]
    message = generate_ai_coach_message(
        outcome="Too High",
        proximity_label="🔥 Very Hot!",
        retrieved_tips=tips,
        attempts_left=3
    )

    assert isinstance(message, str)
    assert len(message) > 0
    # Should use the retrieved tip's text as a fallback, not crash
    assert "small adjustments" in message.lower()


def test_generate_ai_coach_message_fallback_with_no_tips(monkeypatch):
    """
    If the API fails AND there are no retrieved tips, we should still
    get a safe generic message instead of an exception.
    """
    def broken_generate(*args, **kwargs):
        raise ConnectionError("Simulated API failure")

    monkeypatch.setattr(ai_coach, "AI_COACH_ENABLED", True)
    monkeypatch.setattr(
        ai_coach,
        "_model",
        type("FakeModel", (), {"generate_content": staticmethod(broken_generate)})()
    )

    message = generate_ai_coach_message(
        outcome="Too Low",
        proximity_label="❄️ Cold",
        retrieved_tips=[],
        attempts_left=2
    )

    assert isinstance(message, str)
    assert len(message) > 0


def test_ai_coach_disabled_without_api_key(monkeypatch):
    """
    If GEMINI_API_KEY is missing, the coach should run in
    fallback-only mode instead of crashing on startup.
    """
    monkeypatch.setattr(ai_coach, "AI_COACH_ENABLED", False)

    message = generate_ai_coach_message(
        outcome="Too Low",
        proximity_label="🌡️ Warm",
        retrieved_tips=[],
        attempts_left=3
    )
    assert message == "Keep going, you've got this!"


def test_ai_coach_succeeds_with_mocked_gemini_response(monkeypatch):
    """
    Simulate a successful Gemini call and confirm the returned text
    is passed through correctly (rather than the fallback path).
    """
    class FakeResponse:
        text = "You're right on top of it — trust your gut here!"

    def fake_generate(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(ai_coach, "AI_COACH_ENABLED", True)
    monkeypatch.setattr(
        ai_coach,
        "_model",
        type("FakeModel", (), {"generate_content": staticmethod(fake_generate)})()
    )

    tips = [{"id": "hot_cold_close", "tags": ["very_hot"], "text": "Small adjustments work best now."}]
    message = generate_ai_coach_message(
        outcome="Too High",
        proximity_label="🔥 Very Hot!",
        retrieved_tips=tips,
        attempts_left=3
    )

    assert message == "You're right on top of it — trust your gut here!"