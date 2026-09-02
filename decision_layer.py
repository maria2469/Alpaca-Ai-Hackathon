"""Decision layer: the LLM (or the human, in manual mode) picks at most one entry.

The decider only ever chooses a symbol from the scored candidate list and a
direction. Strikes, expiration, quantity and price are deterministic code.
Any malformed output means no entry. Errors surface as status codes or
exception type names only — response bodies are never copied into errors.
"""

from __future__ import annotations

import json
from typing import Callable

import httpx

import settings
from data_models import EntryChoice, SymbolFeatures

# OpenRouter URL (commented out in favor of Google Gemini API):
# OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# Google Gemini API endpoint
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
TIMEOUT_SECONDS = 30.0

SYSTEM_PROMPT = """You are the entry-signal module of an institutional multi-agent trading system that buys
debit vertical spreads on liquid US options. Every candidate underlying has fired
at least one technical event on its latest completed bar:
  gap_up / gap_down           - bar opened more than 2 ATR away from the prior close
  breakout_up / breakout_down - bar body (close minus open) exceeded 2 ATR
  macd_cross_up / macd_cross_down - MACD histogram crossed zero
Each candidate also carries its RSI, ATR, MACD histogram readings, and ongoing multi-bar scratchpad thesis.

Pay close attention to 'recent_lessons_and_mistakes_to_avoid' and 'recent_agent_mistakes' — do NOT repeat past false breakout entries into resistance or choppy regimes.

Reply with strict JSON only:
{"action": "enter" | "pass", "symbol": "<one of the candidate symbols>",
 "direction": "CALL" | "PUT", "thesis": "<one sentence>"}

Rules: only pick a symbol from the candidate list. CALL means you expect the
underlying to rise, PUT to fall. The event direction is a hint, not an order;
an exhausted move (e.g. extreme RSI) may argue against following it. Pass when
nothing is convincing - passing is always acceptable."""


class LlmError(Exception):
    pass


def call_gemini(
    messages: list[dict],
    api_key: str,
    transport: httpx.BaseTransport | None = None,
) -> tuple[str, str]:
    """POST to Google Gemini API; returns (content, model_used). Raises LlmError."""
    raw_model = getattr(settings, "PRIMARY_MODEL", "gemini-2.5-flash")
    model_name = "gemini-2.5-flash" if "gemini" in raw_model.lower() else raw_model

    contents = []
    system_instruction = None
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            system_instruction = {"parts": [{"text": content}]}
        else:
            g_role = "user" if role == "user" else "model"
            contents.append({"role": g_role, "parts": [{"text": content}]})

    native_url = f"{GEMINI_API_BASE}/models/{model_name}:generateContent?key={api_key}"
    payload: dict = {
        "contents": contents,
        "generationConfig": {"responseMimeType": "application/json"},
    }
    if system_instruction:
        payload["systemInstruction"] = system_instruction

    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS, transport=transport) as client:
            # 1. Try OpenAI-compatible endpoint first
            openai_url = f"{GEMINI_API_BASE}/openai/chat/completions"
            oai_payload = {
                "model": model_name,
                "messages": messages,
                "response_format": {"type": "json_object"},
            }
            response = client.post(
                openai_url,
                json=oai_payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if response.status_code == 200:
                body = response.json()
                if "choices" in body:
                    content = body["choices"][0]["message"]["content"]
                    model_used = body.get("model", model_name)
                    if isinstance(content, str) and isinstance(model_used, str):
                        return content, model_used

            # 2. Fallback to native generateContent endpoint
            response = client.post(native_url, json=payload)
            if response.status_code == 200:
                body = response.json()
                candidates = body.get("candidates", [])
                if candidates and isinstance(candidates, list):
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"], model_name
                if "choices" in body:
                    content = body["choices"][0]["message"]["content"]
                    model_used = body.get("model", model_name)
                    if isinstance(content, str) and isinstance(model_used, str):
                        return content, model_used
    except Exception as error:
        raise LlmError(f"gemini request failed: {type(error).__name__}") from None

    if response.status_code != 200:
        raise LlmError(f"gemini returned HTTP {response.status_code}") from None

    raise LlmError("gemini response had an unexpected shape")


# Backward-compatible alias for existing tests
def call_openrouter(
    messages: list[dict],
    api_key: str,
    transport: httpx.BaseTransport | None = None,
) -> tuple[str, str]:
    """OpenRouter wrapper (now routes through Gemini client)."""
    return call_gemini(messages, api_key, transport=transport)


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def parse_entry_choice(text: str, allowed_symbols: set[str], model: str) -> EntryChoice | None:
    """Strictly validate the model's reply; anything malformed means no entry."""
    data = _extract_json(text)
    if data is None:
        return None
    if data.get("action") != "enter":
        return None
    symbol = data.get("symbol")
    direction = data.get("direction")
    if not isinstance(symbol, str) or symbol.upper() not in allowed_symbols:
        return None
    if direction not in ("CALL", "PUT"):
        return None
    thesis = data.get("thesis")
    thesis = thesis if isinstance(thesis, str) else ""
    return EntryChoice(symbol=symbol.upper(), direction=direction, thesis=thesis, model=model)


def compute_quantitative_edge_score(c: SymbolFeatures) -> float:
    """Quantitative scoring function. Determines technical qualification before invoking LLM."""
    if not c.events:
        return 0.0
    score = 0.50
    score += len(c.events) * 0.10

    if c.rsi is not None:
        for e in c.events:
            if e.direction == "CALL":
                if 40.0 <= c.rsi <= 68.0:
                    score += 0.15
                elif c.rsi >= settings.RSI_CALL_MAX:
                    score -= 0.25
            elif e.direction == "PUT":
                if 32.0 <= c.rsi <= 60.0:
                    score += 0.15
                elif c.rsi <= settings.RSI_PUT_MIN:
                    score -= 0.25

    if c.macd_hist is not None and c.atr is not None:
        macd_threshold = settings.MACD_MIN_ATR_MULT * c.atr
        if abs(c.macd_hist) >= macd_threshold:
            score += 0.10

    return max(0.0, min(1.0, score))


def decide_entry(
    candidates: list[SymbolFeatures],
    api_key: str,
    transport: httpx.BaseTransport | None = None,
    recent_lessons: list[str] | None = None,
    agent_mistakes: list[str] | None = None,
    working_scratchpad: dict[str, str] | None = None,
) -> EntryChoice | None:
    """Ask the LLM to pick at most one entry, conditioned on past trade lessons and scratchpad."""
    tradeable = [c for c in candidates if c.gate_block is None]
    if not tradeable:
        return None
    
    # Quantitative edge pre-filter: LLM is ONLY invoked on setups with score >= 0.55
    qualified = [c for c in tradeable if compute_quantitative_edge_score(c) >= 0.55]
    if not qualified:
        return None
    
    briefing: dict = {
        "candidates": [
            {
                "symbol": c.symbol,
                "spot": c.mid,
                "events": [{"kind": e.kind, "direction": e.direction} for e in c.events],
                "rsi": c.rsi,
                "atr": c.atr,
                "macd_hist": c.macd_hist,
                "quantitative_edge_score": round(compute_quantitative_edge_score(c), 2),
                "ongoing_scratchpad_thesis": (working_scratchpad or {}).get(c.symbol),
            }
            for c in qualified
        ],
    }

    if recent_lessons:
        briefing["recent_lessons_and_mistakes_to_avoid"] = recent_lessons[-4:]
    if agent_mistakes:
        briefing["recent_agent_mistakes"] = agent_mistakes[-3:]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(briefing)},
    ]
    content, model_used = call_openrouter(messages, api_key, transport=transport)
    return parse_entry_choice(content, {c.symbol for c in tradeable}, model_used)


def manual_decide(
    candidates: list[SymbolFeatures],
    input_fn: Callable[[str], str] | None = None,
    echo: Callable[[str], None] = print,
) -> EntryChoice | None:
    """Manual mode: the human picks which candidate to trade, or passes.

    Anything unparseable — blank, not a number, out of range — is a pass:
    no order ever results from garbage input. The direction defaults to the
    selected candidate's first event; only an explicit CALL/PUT overrides it.
    """
    if input_fn is None:
        input_fn = input  # resolved at call time so tests can patch builtins.input
    tradeable = sorted(
        (c for c in candidates if c.gate_block is None and c.events),
        key=lambda c: c.symbol,
    )
    if not tradeable:
        return None
    echo("Candidates with fired events:")
    for index, c in enumerate(tradeable, start=1):
        events = ", ".join(e.kind for e in c.events)
        echo(
            f"  [{index}] {c.symbol:<6} spot={c.mid} events={events} "
            f"rsi={c.rsi} atr={c.atr} macd_hist={c.macd_hist}"
        )
    raw = input_fn("Select a candidate number to trade (blank to pass): ").strip()
    if not raw.isdigit() or not (1 <= int(raw) <= len(tradeable)):
        return None
    chosen = tradeable[int(raw) - 1]
    default_direction = chosen.events[0].direction
    raw_direction = input_fn(f"Direction CALL or PUT [default {default_direction}]: ").strip().upper()
    direction = raw_direction if raw_direction in ("CALL", "PUT") else default_direction
    event_kinds = ", ".join(e.kind for e in chosen.events)
    return EntryChoice(
        symbol=chosen.symbol,
        direction=direction,
        thesis=f"Manual selection ({event_kinds}).",
        model="manual",
    )
