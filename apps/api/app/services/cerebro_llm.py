"""Real LLM reply layer for the CEREBRO chat.

Primary path  : OpenRouter cascade - DeepSeek -> Gemini Flash -> Groq/Llama -> Claude Sonnet.
                Uses OpenRouter's native ``models`` fallback list so a single HTTP call
                handles the full cascade server-side.
Fallback path : Anthropic SDK direct (used when OpenRouter is unavailable).

Fail-safe by design: any network/auth/parse error returns None and the caller
keeps the existing internal canned reply. No exception ever propagates outward.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from app.core.config import get_settings

CEREBRO_SYSTEM_PROMPT = (
    "Eres CEREBRO, el jefe de gabinete interno del ecosistema de Daniel. "
    "Respondes en espanol, te diriges a Daniel, con tono ejecutivo, directo y breve. "
    "Reglas inquebrantables:\n"
    "- NUNCA ejecutas acciones externas ni afirmas haberlas ejecutado. Solo describes "
    "lo que CEREBRO ya hizo internamente (las acciones que se te entregan como hechas).\n"
    "- NUNCA revelas fuentes de SOMBRA, payloads sensibles, secretos ni tokens.\n"
    "- NUNCA prometes publicacion automatica: LinkedIn/PLUMA/MARCA PERSONAL quedan en "
    "borrador hasta que el CEO lo autorice.\n"
    "- Si no hay datos, dilo; no inventes metricas ni resultados.\n"
    "- Mantente dentro de la operacion interna: misiones, tareas para FORJA, lectura de "
    "CENTINELA, borradores comerciales sanitizados.\n"
    "- Cuando recibas o detectes inteligencia externa, bug bounty, recompensas, plata, "
    "reclamar, reportes, ultimo escaneo o sistema discreto, debes leer datos reales del "
    "inbox interno cuando la accion indique sombra_inbox; no respondas generico y produce "
    "salidas accionables para CEO, FORJA, PLUMA, MARCA PERSONAL, CENTINELA y AUDITORIA.\n"
    "Resume de forma util para que el CEO decida; no repitas literalmente los datos crudos."
)


def _build_user_prompt(
    message: str,
    intent: str,
    actions: list[dict[str, Any]],
    state: dict[str, Any],
) -> str:
    """Assemble a grounded prompt from the real turn data."""
    actions_text = (
        json.dumps(actions, ensure_ascii=False, sort_keys=True)
        if actions
        else "ninguna"
    )
    state_text = json.dumps(state, ensure_ascii=False, sort_keys=True)
    return (
        f"Instruccion del CEO: {message}\n\n"
        f"Intencion detectada por CEREBRO: {intent}\n"
        f"Acciones que CEREBRO YA ejecuto en este turno: {actions_text}\n"
        f"Estado interno real de CEREBRO: {state_text}\n\n"
        "Redacta la respuesta de CEREBRO al CEO basandote unicamente en lo anterior."
    )


def _call_openrouter(
    api_key: str,
    models: tuple[str, ...],
    user_prompt: str,
    max_tokens: int = 1024,
    timeout: int = 30,
) -> str:
    """POST to OpenRouter with a native model fallback list.

    OpenRouter tries each model in order and returns the first successful response,
    so a single HTTP call handles DeepSeek -> Gemini Flash -> Groq/Llama -> Claude.
    """
    payload = json.dumps(
        {
            "models": list(models),
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": CEREBRO_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ecosystem-foundation.vercel.app",
            "X-Title": "CEREBRO · Ecosistema CEO",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data["choices"][0]["message"]["content"].strip()


def generate_reply(
    message: str,
    intent: str,
    actions: list[dict[str, Any]],
    state: dict[str, Any],
) -> str | None:
    """Return an LLM-generated reply, or None to fall back to the canned reply.

    Precedence:
    1. OpenRouter cascade  (OPENROUTER_API_KEY present)
       DeepSeek -> Gemini Flash -> Groq/Llama -> Claude Sonnet  (server-side fallback)
    2. Anthropic SDK direct  (ANTHROPIC_API_KEY present, OpenRouter absent or failed)
    """
    settings = get_settings()

    if not settings.cerebro_llm_enabled:
        return None

    user_prompt = _build_user_prompt(message, intent, actions, state)

    # --- Primary: OpenRouter cascade ---
    if settings.openrouter_api_key:
        try:
            reply = _call_openrouter(
                api_key=settings.openrouter_api_key,
                models=settings.cerebro_openrouter_models,
                user_prompt=user_prompt,
            )
            return reply or None
        except Exception:
            # Network / auth / quota error — fall through to Anthropic
            pass

    # --- Fallback: Anthropic SDK direct ---
    if not settings.anthropic_api_key:
        return None

    try:
        import anthropic
    except ImportError:
        return None

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.cerebro_llm_model,
            max_tokens=1024,
            system=CEREBRO_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception:
        return None

    reply = next(
        (
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ),
        "",
    ).strip()
    return reply or None
