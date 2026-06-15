"""Real LLM reply layer for the CEREBRO chat.

This module ONLY generates the conversational ``reply`` text. The deterministic
intent engine and all governed side effects (missions, FORJA tasks, commercial
drafts, SOMBRA inbox reads) stay in ``services.cerebro`` and are passed in here
as already-executed facts. The model never executes actions; it narrates what
CEREBRO already did, grounded in real state.

Fail-safe by design: if the ``anthropic`` package is not installed, no API key
is configured, the feature is disabled, or the call errors, ``generate_reply``
returns ``None`` and the caller keeps the existing internal canned reply.
"""

from __future__ import annotations

import json
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


def generate_reply(
    message: str,
    intent: str,
    actions: list[dict[str, Any]],
    state: dict[str, Any],
) -> str | None:
    """Return a Claude-generated reply, or ``None`` to fall back to the canned reply."""
    settings = get_settings()
    if not settings.cerebro_llm_enabled or not settings.anthropic_api_key:
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
            messages=[
                {
                    "role": "user",
                    "content": _build_user_prompt(message, intent, actions, state),
                }
            ],
        )
    except Exception:
        # Any SDK/network/auth error must degrade silently to the internal reply.
        return None

    reply = next(
        (block.text for block in response.content if getattr(block, "type", None) == "text"),
        "",
    ).strip()
    return reply or None
