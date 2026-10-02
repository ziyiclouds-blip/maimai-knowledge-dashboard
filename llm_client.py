from __future__ import annotations

"""外部 LLM 渠道客户端：openai / openai_responses / claude / gemini 四种协议。"""

import json
from typing import Any


class ExternalLLMError(Exception):
    pass


def _messages(prompt: str, image_base64: str = "") -> list[dict]:
    if image_base64:
        return [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                {"type": "text", "text": prompt},
            ],
        }]
    return [{"role": "user", "content": prompt}]


def _claude_messages(prompt: str, image_base64: str = "") -> list[dict]:
    if image_base64:
        return [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64}},
                {"type": "text", "text": prompt},
            ],
        }]
    return [{"role": "user", "content": prompt}]


def _gemini_contents(prompt: str, image_base64: str = "") -> list[dict]:
    parts: list[dict] = [{"text": prompt}]
    if image_base64:
        parts.insert(0, {"inline_data": {"mime_type": "image/jpeg", "data": image_base64}})
    return [{"role": "user", "parts": parts}]


def _join(base: str, path: str) -> str:
    return base.rstrip("/") + path


async def _post(url: str, headers: dict, payload: dict, timeout: int) -> dict:
    try:
        import aiohttp
    except ImportError:
        raise ExternalLLMError("宿主环境缺少 aiohttp，无法调用自定义渠道")
    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, headers=headers, json=payload,
                             timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            text = await resp.text()
            if resp.status >= 400:
                raise ExternalLLMError(f"HTTP {resp.status}: {text[:300]}")
            try:
                return json.loads(text)
            except Exception as e:
                raise ExternalLLMError(f"响应非 JSON: {e}; body={text[:200]}")


async def call_openai(base_url: str, api_key: str, model: str, prompt: str,
                      image_base64: str = "", max_tokens: int = 1536,
                      temperature: float = 0.3, timeout: int = 60) -> str:
    url = _join(base_url, "/v1/chat/completions")
    payload = {
        "model": model,
        "messages": _messages(prompt, image_base64),
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    data = await _post(url, {"Authorization": f"Bearer {api_key}"}, payload, timeout)
    try:
        return data["choices"][0]["message"]["content"] or ""
    except Exception as e:
        raise ExternalLLMError(f"openai 响应解析失败: {e}")


async def call_openai_responses(base_url: str, api_key: str, model: str, prompt: str,
                                image_base64: str = "", max_tokens: int = 1536,
                                temperature: float = 0.3, timeout: int = 60) -> str:
    url = _join(base_url, "/v1/responses")
    if image_base64:
        inp = [{
            "role": "user",
            "content": [
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_base64}"},
                {"type": "input_text", "text": prompt},
            ],
        }]
    else:
        inp = [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}]
    payload = {
        "model": model,
        "input": inp,
        "max_output_tokens": max_tokens,
        "temperature": temperature,
    }
    data = await _post(url, {"Authorization": f"Bearer {api_key}"}, payload, timeout)
    # output 里找 type=message 的 text
    for item in data.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") in ("output_text", "text"):
                    return part.get("text", "")
    raise ExternalLLMError("openai_responses 未返回文本")


async def call_claude(base_url: str, api_key: str, model: str, prompt: str,
                      image_base64: str = "", max_tokens: int = 1536,
                      temperature: float = 0.3, timeout: int = 60) -> str:
    url = _join(base_url, "/v1/messages")
    payload = {
        "model": model,
        "messages": _claude_messages(prompt, image_base64),
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    data = await _post(url, headers, payload, timeout)
    for block in data.get("content", []):
        if block.get("type") == "text":
            return block.get("text", "")
    raise ExternalLLMError("claude 未返回文本")


async def call_gemini(base_url: str, api_key: str, model: str, prompt: str,
                      image_base64: str = "", max_tokens: int = 1536,
                      temperature: float = 0.3, timeout: int = 60) -> str:
    url = _join(base_url, f"/v1beta/models/{model}:generateContent?key={api_key}")
    payload = {
        "contents": _gemini_contents(prompt, image_base64),
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
    }
    data = await _post(url, {}, payload, timeout)
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)
    except Exception as e:
        raise ExternalLLMError(f"gemini 响应解析失败: {e}")


_DISPATCH = {
    "openai": call_openai,
    "openai_responses": call_openai_responses,
    "openai-responses": call_openai_responses,
    "responses": call_openai_responses,
    "claude": call_claude,
    "anthropic": call_claude,
    "gemini": call_gemini,
    "google": call_gemini,
}


async def call_external(protocol: str, base_url: str, api_key: str, model: str,
                        prompt: str, image_base64: str = "", max_tokens: int = 1536,
                        temperature: float = 0.3, timeout: int = 60) -> str:
    fn = _DISPATCH.get(str(protocol or "").strip().lower())
    if fn is None:
        raise ExternalLLMError(f"未知协议: {protocol}")
    if not base_url or not model:
        raise ExternalLLMError("base_url 或 model 为空")
    return await fn(base_url, api_key, model, prompt, image_base64=image_base64,
                    max_tokens=max_tokens, temperature=temperature, timeout=timeout)
