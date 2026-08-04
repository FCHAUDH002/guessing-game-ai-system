cat > README.md << 'EOF'
# Guessing Game AI Coach

An applied AI system that extends a Module 1 debugging project into a retrieval-augmented, reliability-tested number-guessing game with an AI coaching layer, built to explore how grounding an LLM's output in retrieved context reduces generic or unreliable advice, a core challenge in real-world applied AI systems.

## Base Project

This project extends **Game Glitch Investigator** (AI110 Module 1). The original project's goal was to debug an AI-generated Streamlit number-guessing game: the player would guess a number and receive "Too High"/"Too Low" hints until winning or running out of attempts. Its original capabilities were a working guess-check loop, a difficulty selector, and a proximity ("hot/cold") indicator, but it shipped with several logic bugs (inverted hints, a broken game-reset, and no input-range validation) that I diagnosed and fixed as part of that assignment.

## What This System Does

The core game is a number-guessing loop: guess a number, get a "Too High"/"Too Low" hint plus a proximity read ("🔥 Very Hot", "🌡️ Warm", "❄️ Cold"), and win or lose based on your attempts. Layered on top is an **AI coaching feature**:

1. After every non-winning guess, the system checks the current game state (how close the guess was, attempts remaining, whether you've repeated a guess, how early in the game you are).
2. It **retrieves** relevant strategy tips from a small local knowledge base based on that state.
3. It sends those retrieved tips to **Gemini**, which generates a short, natural-language coaching message grounded in that specific tip, not a generic message.
4. If the Gemini API is unavailable, rate-limited, or the call fails, the system **falls back** to the raw tip text (or a generic encouragement) instead of crashing.

This is a Retrieval-Augmented Generation (RAG) pattern: the AI's response is grounded in retrieved, curated content rather than freely generating advice from scratch.

The UI was also reworked from the original Module 1 layout into a themed "Mystery Number Quest" with live stat cards (score, guesses left, difficulty), an attempts progress bar, and a guess-history chip strip.

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

If `GEMINI_API_KEY` is missing, the app still runs, the AI coach automatically falls back to static tips instead of crashing.

## Sample Interactions

**Example 1 — Cold guess, score and stats update correctly on the first click**

Before: Score 100, Guesses Left 8, Attempts used 0/8
Input: guess = 100 (secret = 67, range 1-100)
Output: "❄️ Cold — 📉 Go LOWER! (−15 pts)"
Coach: "That guess was a bit too high and you're still pretty cold,
so try taking a big leap toward the middle of your remaining range.
You've got this — 7 attempts left!"
After: Score 85, Guesses Left 7, Attempts used 1/8

**Example 2 — Very close guess, low attempts remaining**

Input: guess = 15 (secret = 14, 1 attempt left)
Output: "🔥 Very Hot! — 📈 Go LOWER! (−5 pts)"
Coach: "When you're this close, small adjustments (±1-3) work better
than big jumps."
After: Out of guesses. Final score: 5

**Example 3 — API fallback (Gemini unavailable or rate-limited)**

Input: guess = 45 (secret = 50, Gemini free-tier quota exceeded)
Output: "🌡️ Warm — 📉 Go LOWER! (−10 pts)"
Coach: "When you're this close, small adjustments (±1-3) work better
than big jumps."

(This is the raw knowledge-base tip returned directly by the fallback path, confirming the system degrades gracefully instead of crashing when the Gemini API fails.)

## Design Decisions

- **Kept the original `check_guess`/`get_proximity_hint` functions untouched in spirit, but hardened them.** During this project I found that `check_guess`'s fallback branch (handling the case where the secret is stringified on even attempts, a carryover from Module 1) compared values as strings rather than integers, which silently inverted hint direction for guesses like 100 vs. a secret of 14. I fixed this by normalizing both values to `int` before comparing, removing the fragile string-comparison path entirely.
- **Tag-based retrieval instead of embeddings.** Given the small, fixed knowledge base (5 strategy tips), a simple tag-matching system is transparent, fast, and easy to test exhaustively; a vector database would be over-engineering at this scale.
- **Explicit fallback path for the AI coach.** Gemini calls can fail (network issues, rate limits, missing key), so the system always returns a usable message rather than crashing. This was tested with `monkeypatch` to simulate API failures without needing live network access, and was also confirmed against a real Gemini free-tier rate limit encountered during testing (see Testing Summary).
- **Reworked scoring system.** The original cumulative gain/loss scoring was replaced with a fixed starting pool (100 points) and a proximity-based deduction (−5 Very Hot, −10 Warm, −15 Cold), floored at 0. This is more intuitive for players to track than an open-ended score that could go negative.
- **Stat cards rendered via `st.empty()` placeholder.** Streamlit reruns the whole script top-to-bottom on every interaction. Initially the score/attempts/difficulty stat cards were computed and drawn before the guess-processing logic ran, so they displayed the previous guess's numbers instead of the current one. Using a `st.empty()` placeholder reserved near the top of the layout, filled in after guess processing completes, keeps the cards visually anchored at the top while always showing accurate, current-guess data.
- **Logging to `ai_coach.log`.** Every retrieval and coach-generation attempt is logged, so failures and retrieved tags are traceable after the fact.

## Testing Summary

25 automated tests pass (`pytest`), covering:
- Original and hardened game logic (14 tests): win/loss detection, hint direction (including the stringified-secret regression case), proximity scoring, New Game state reset
- AI coach retrieval logic (7 tests): each knowledge-base tag condition tested independently (very hot, cold, low attempts, repeated guess, early game, max 2 tips returned, no-match case)
- AI coach reliability (4 tests): successful Gemini call, API failure fallback with tips available, API failure fallback with no tips available, and missing-API-key fallback

During development, an automated test that submitted many guesses in rapid succession triggered a real Gemini free-tier rate limit (`429`, 15 requests/minute), confirming the fallback path activates correctly under genuine API failure conditions, not just simulated ones. That test was subsequently updated to mock the AI coach call, since its purpose is verifying game-state reset logic, not live API availability.

Two real bugs were also found through manual gameplay testing rather than automated tests: an inverted hint direction on stringified secrets, and a one-guess display lag in the stat cards. Both are described in Design Decisions above and fixed.

One known limitation: the `google.generativeai` SDK used here is deprecated in favor of `google.genai`; functionality is unaffected but a future migration would be worth doing.

## Reflection

This project reinforced that integrating AI into a system is less about the API call itself and more about designing for its failure modes. Grounding the coach's responses in retrieved tips made the output more consistent and relevant than unconstrained generation would have. However, the majority of my effort went into the fallback logic: ensuring that if the Gemini API failed or the key was missing, the game would degrade gracefully rather than crash. This echoed a lesson from the original debugging project, that AI-generated code can appear complete while still containing underlying issues, and showed me that the same principle applies to AI-powered features. Testing failure cases proved just as important as testing successful ones.