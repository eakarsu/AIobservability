"""
Custom Feature: Prompt regression detector
Diff prompt versions; auto-evaluate against golden set; flag regressions before deploy
Auto-generated v0 scaffold — review before production use.
"""
import os
import json
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'


def _model() -> str:
    return os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-5-sonnet-20241022')


async def _call_llm(system_prompt: str, user_prompt: str) -> dict:
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        # TODO: configure credentials — set OPENROUTER_API_KEY in your .env
        raise HTTPException(status_code=503, detail='OPENROUTER_API_KEY not configured')
    payload = {
        'model': _model(),
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': 0.4,
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'X-Title': 'AIobservability / cf-prompt-regression-detector',
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f'OpenRouter error: {r.text[:300]}')
        data = r.json()
        return {
            'content': data.get('choices', [{}])[0].get('message', {}).get('content', ''),
            'tokens_used': (data.get('usage') or {}).get('total_tokens', 0),
            'model': data.get('model'),
        }


def _parse_json_loose(text: str) -> Optional[Any]:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    stripped = text.replace('```json', '').replace('```', '').strip()
    try:
        return json.loads(stripped)
    except Exception:
        return None


class RunPayload(BaseModel):
    data: dict = Field(default_factory=dict, description='Free-form input for the feature handler')


@router.post("/cf-prompt-regression-detector/run", tags=["Custom Features"])
async def run_feature(payload: RunPayload):
    system_prompt = (
        "You are an expert assistant helping with the feature: 'Prompt regression detector'. "
        "Context: Diff prompt versions; auto-evaluate against golden set; flag regressions before deploy "
        "Project: AIobservability. "
        "Return concise, actionable JSON with keys: { summary: string, recommendations: string[], risks: string[], next_steps: string[] }. "
        "If input is insufficient, populate sensible defaults and note assumptions in summary."
    )
    user_prompt = f'Input payload:\n{json.dumps(payload.data, indent=2)}'
    result = await _call_llm(system_prompt, user_prompt)
    parsed = _parse_json_loose(result['content'])
    return {
        'ok': True,
        'summary': (parsed or {}).get('summary') if parsed else result['content'][:600],
        'result_json': parsed,
        'raw': result['content'],
        'tokens_used': result['tokens_used'],
        'model': result['model'],
    }
