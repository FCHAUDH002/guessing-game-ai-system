"""
ai_coach.py

RAG-based coaching layer for the Game Glitch Investigator.

This module retrieves relevant strategy tips from a small local
knowledge base (knowledge_base.py) based on the current game state,
then asks Gemini to turn those tips into a short, natural-language
coaching message. If the API key is missing or the call fails for
any reason, it falls back to the raw retrieved tip (or a generic
message) so the game never crashes because of the AI layer.
"""

import os
import logging

from dotenv import load_dotenv
import google.generativeai as genai

from knowledge_base import STRATEGY_TIPS

load_dotenv()

logging.basicConfig(
    filename="ai_coach.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    _model = genai.GenerativeModel("gemini-3.5-flash-lite")
    AI_COACH_ENABLED = True
else:
    _model = None
    AI_COACH_ENABLED = False
    logging.warning("GEMINI_API_KEY not found. AI coach running in fallback-only mode.")


def retrieve_tips(proximity_label, attempts_left, attempt_limit, guess, history):
    """
    Retrieve up to 2 relevant strategy tips from the knowledge base
    based on the current game state.

    Args:
        proximity_label: output of get_proximity_hint (e.g. "🔥 Very Hot!")
        attempts_left: int, attempts remaining
        attempt_limit: int, total attempts allowed this game
        guess: the most recent guess
        history: list of all guesses made so far

    Returns:
        list of tip dicts (from STRATEGY_TIPS), max length 2
    """
    tags_present = set()

    if proximity_label == "🔥 Very Hot!":
        tags_present.add("very_hot")
    if proximity_label == "❄️ Cold":
        tags_present.add("cold")

    if attempts_left <= max(1, attempt_limit // 3):
        tags_present.add("low_attempts_left")

    if history.count(guess) > 1:
        tags_present.add("repeated_guess")

    if len(history) <= 1:
        tags_present.add("early_game")
        tags_present.add("wide_range")

    matches = [tip for tip in STRATEGY_TIPS if tags_present & set(tip["tags"])]

    logging.info(
        "retrieve_tips: tags=%s matched=%s",
        sorted(tags_present),
        [t["id"] for t in matches],
    )

    return matches[:2]


def _fallback_message(retrieved_tips):
    """Safe, non-LLM message used when Gemini is unavailable or the call fails."""
    if retrieved_tips:
        return retrieved_tips[0]["text"]
    return "Keep going, you've got this!"


def generate_ai_coach_message(outcome, proximity_label, retrieved_tips, attempts_left):
    """
    Generate a short, encouraging coaching message using retrieved
    strategy tips as grounding context. Falls back to a safe static
    message if the API key is missing or the call fails.

    Args:
        outcome: "Too High", "Too Low", or "Win"
        proximity_label: output of get_proximity_hint
        retrieved_tips: list of tip dicts from retrieve_tips()
        attempts_left: int, attempts remaining

    Returns:
        str: a short coaching message (max ~2 sentences)
    """
    if not AI_COACH_ENABLED:
        return _fallback_message(retrieved_tips)

    tip_text = " ".join(t["text"] for t in retrieved_tips) if retrieved_tips else "No specific tip needed."

    prompt = f"""You are a friendly, concise number-guessing game coach.
Game state: outcome={outcome}, proximity={proximity_label}, attempts_left={attempts_left}.
Relevant strategy tips (retrieved from a knowledge base): {tip_text}

Write ONE short (max 2 sentences) encouraging coaching message that naturally
incorporates the retrieved tip if relevant. Do not repeat the raw tip verbatim."""

    try:
        response = _model.generate_content(prompt)
        message = response.text.strip()
        logging.info("generate_ai_coach_message: success")
        return message

    except Exception as e:
        logging.error("generate_ai_coach_message: API call failed (%s)", e)
        return _fallback_message(retrieved_tips)