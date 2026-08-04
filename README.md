# Guessing Game AI Coach

An applied AI system that extends a Module 1 debugging project into a retrieval-augmented, reliability-tested number-guessing game with an AI coaching layer built to explore how grounding an LLM's output in retrieved context reduces generic or unreliable advice, a core challenge in real-world applied AI systems.

## Base Project

This project extends **Game Glitch Investigator** (AI110 Module 1). The original project's goal was to debug an AI-generated Streamlit number-guessing game: the player would guess a number and receive "Too High"/"Too Low" hints until winning or running out of attempts. Its original capabilities were a working guess-check loop, a difficulty selector, and a proximity ("hot/cold") indicator — but it shipped with several logic bugs (inverted hints, a broken game-reset, and no input-range validation) that I diagnosed and fixed as part of that assignment.

## What This System Does

The game itself is unchanged: guess a number, get a "Too High"/"Too Low" hint, win or lose based on your attempts. What's new is an **AI coaching layer** that sits on top of the existing hint system:

1. After every non-winning guess, the system checks the current game state (how close the guess was, attempts remaining, whether you've repeated a guess, how early in the game you are).
2. It **retrieves** relevant strategy tips from a small local knowledge base based on that state.
3. It sends those retrieved tips to **Gemini**, which generates a short, natural-language coaching message grounded in that specific tip.
4. If the Gemini API is unavailable or the call fails, the system **falls back** to the raw tip text or a generic encouragement instead of crashing.

This is a Retrieval-Augmented Generation (RAG) pattern: the AI's response is grounded in retrieved, curated content rather than freely generating advice from scratch.

## Architecture Overview

See `diagrams/architecture.mmd` for the full system diagram (Mermaid source).

The flow: **player guess → game logic → proximity hint → tip retrieval (knowledge base) → Gemini-generated coaching message → displayed to player**, with a fallback path if Gemini is unreachable. A separate reliability layer (two pytest suites) checks the game logic and the AI coaching logic independently.

## Setup Instructions

1. Clone this repo and install dependencies:
```bash
   git clone https://github.com/FCHAUDH002/guessing-game-ai-system.git
   cd guessing-game-ai-system
   pip install -r requirements.txt
```

2. Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/api-keys).

3. Create a `.env` file in the project root:

   GEMINI_API_KEY=your_api_key_here

4. Run the app:
```bash
   streamlit run app.py
```

5. Run the test suite:
```bash
   pytest
```

If `GEMINI_API_KEY` is missing, the app still runs. The AI coach automatically falls back to static tips instead of crashing.

## Sample Interactions

**Example 1 — Cold guess, early game**

Input: guess = 5 (secret = 82, range 1-100)
Output: "❄️ Cold"
Coach: "You're pretty far off right now — try jumping toward the middle
of the remaining range instead of guessing nearby numbers."

**Example 2 — Very close guess, low attempts remaining**

Input: guess = 79 (secret = 82, 1 attempt left)
Output: "🔥 Very Hot!"
Coach: "You're extremely close — with only one guess left, trust this
range and make a small adjustment rather than a big jump."

**Example 3 — API fallback (Gemini unavailable)**

Input: guess = 45 (secret = 50, GEMINI_API_KEY removed to simulate failure)
Output: "🌡️ Warm"
Coach: "When you're this close, small adjustments (±1-3) work better
than big jumps."

(This is the raw knowledge-base tip returned directly, confirming the fallback works without crashing the game.)

## Design Decisions

- **Kept the original `check_guess`/`get_proximity_hint` functions untouched.** The new AI layer builds on top of proven, tested logic rather than replacing it, reducing risk of reintroducing old bugs.
- **Tag-based retrieval instead of embeddings.** Given the small, fixed knowledge base (5 strategy tips), a simple tag-matching system is transparent, fast, and easy to test exhaustively — a vector database would be over-engineering at this scale.
- **Explicit fallback path.** Since Gemini calls can fail (network issues, rate limits, missing key), the system always returns a usable message rather than crashing. This was intentionally tested with `monkeypatch` to simulate API failures without needing live network access during test runs.
- **Logging to `ai_coach.log`.** Every retrieval and coach-generation attempt is logged, so failures and retrieved tags are traceable after the fact.

## Testing Summary

23 automated tests pass (`pytest`), covering:
- Original game logic (11 tests): win/loss detection, hint direction, proximity scoring, New Game state reset
- AI coach retrieval logic (7 tests): each knowledge-base tag condition tested independently (very hot, cold, low attempts, repeated guess, early game, max 2 tips returned, no-match case)
- AI coach reliability (3 tests): successful Gemini call, API failure fallback with tips available, API failure fallback with no tips available, and missing-API-key fallback

All 23 tests currently pass. One known limitation: the `google.generativeai` SDK used here is deprecated in favor of `google.genai` — functionality is unaffected but a future migration would be worth doing.

## Reflection

This project reinforced that integrating AI into a system is less about the API call itself and more about designing for its failure modes. Grounding the coach's responses in retrieved tips made the output more consistent and relevant than unconstrained generation would have. However, the majority of my effort went into the fallback logic: ensuring that if the Gemini API failed or the key was missing, the game would degrade gracefully rather than crash. This echoed a lesson from the original debugging project, that AI-generated code can appear complete while still containing underlying issues, and showed me that the same principle applies to AI-powered features. Testing failure cases proved just as important as testing successful ones.