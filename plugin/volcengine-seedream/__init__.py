"""
volcengine-seedream — Hermes Agent 火山引擎 Seedream 文生图插件

在 Hermes Agent 中使用 image_generate 工具调用火山方舟 Ark / 豆包 Seedream 生成图片。
支持负向提示词、CFG scale、步数控制、调试日志等增强功能。
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_b64_image,
    success_response,
)

logger = logging.getLogger(__name__)

# 火山 API 要求的最小像素数（经验值）
MIN_PIXELS = 921600


def _is_debug() -> bool:
    return os.environ.get("SEEDREAM_DEBUG", "").lower() in {"1", "true", "yes"}


def _log(msg: str) -> None:
    if _is_debug():
        logger.info("[volcengine-seedream] %s", msg)


def _parse_size(size_str: str) -> tuple[int, int]:
    """Parse 'WxH' string into (width, height). Returns None on failure."""
    try:
        parts = size_str.strip().lower().split("x")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return 0, 0


def _validate_size(size_str: str) -> Optional[str]:
    """Validate that a size string meets the API minimum pixel requirement.
    Returns an error message if invalid, None if OK."""
    w, h = _parse_size(size_str)
    if w <= 0 or h <= 0:
        return f"Invalid size format: {size_str!r} (expected WxH, e.g. 1024x1024)"
    if w * h < MIN_PIXELS:
        return (
            f"Size {size_str} ({w}x{h}={w*h}px) is too small. "
            f"The API requires at least {MIN_PIXELS} pixels. "
            f"Try 1024x1024, 1280x720, 960x960, etc."
        )
    return None


def _size_for_aspect(aspect_ratio: str) -> str:
    aspect_ratio = resolve_aspect_ratio(aspect_ratio)
    if aspect_ratio == "portrait":
        return os.environ.get("SEEDREAM_PORTRAIT_SIZE", "1024x1536")
    if aspect_ratio == "square":
        return os.environ.get("SEEDREAM_SQUARE_SIZE", "1024x1024")
    return os.environ.get("SEEDREAM_LANDSCAPE_SIZE", "1536x1024")


def _extract_image(data: Any) -> Optional[str]:
    """Accept common OpenAI-compatible and Volcengine response shapes."""
    if not isinstance(data, dict):
        return None

    items = data.get("data")
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict):
            for key in ("url", "image_url", "b64_json", "base64", "binary_data_base64"):
                value = first.get(key)
                if value:
                    if key in {"b64_json", "base64", "binary_data_base64"}:
                        return str(save_b64_image(value, prefix="volcengine_seedream", extension="png"))
                    return value
        elif isinstance(first, str):
            return first

    for key in ("url", "image_url"):
        value = data.get(key)
        if value:
            return value

    for key in ("b64_json", "base64", "binary_data_base64"):
        value = data.get(key)
        if value:
            if isinstance(value, list):
                value = value[0] if value else None
            if value:
                return str(save_b64_image(value, prefix="volcengine_seedream", extension="png"))

    for container_key in ("result", "output"):
        nested = data.get(container_key)
        if isinstance(nested, dict):
            found = _extract_image(nested)
            if found:
                return found

    return None


def _parse_api_error(resp: requests.Response) -> str:
    """Extract a human-readable error message from an API response."""
    try:
        body = resp.json()
    except Exception:
        return f"HTTP {resp.status_code}: {resp.text[:500]}"

    error = body.get("error") or body.get("message") or {}
    if isinstance(error, dict):
        code = error.get("code", "")
        msg = error.get("message", "")
        if code or msg:
            return f"[{code}] {msg}" if code else msg
    elif isinstance(error, str):
        return error

    return f"HTTP {resp.status_code}: {body}"


class VolcengineSeedreamProvider(ImageGenProvider):
    @property
    def name(self) -> str:
        return "volcengine-seedream"

    @property
    def display_name(self) -> str:
        return "Volcengine Seedream"

    def is_available(self) -> bool:
        return bool(os.environ.get("ARK_API_KEY") and os.environ.get("SEEDREAM_MODEL_ID"))

    def default_model(self) -> Optional[str]:
        return os.environ.get("SEEDREAM_MODEL_ID") or "doubao-seedream-4-0-250828"

    def list_models(self) -> List[Dict[str, Any]]:
        model = self.default_model() or "doubao-seedream-4-0-250828"
        return [
            {
                "id": model,
                "display": "Doubao Seedream 4.0",
                "speed": "seconds",
                "strengths": "Chinese/English prompt image generation, photorealistic and design use cases",
                "price": "Volcengine billing",
            }
        ]

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Volcengine Seedream",
            "badge": "paid",
            "tag": "火山方舟 Doubao Seedream 文生图",
            "env_vars": [
                {
                    "key": "ARK_API_KEY",
                    "prompt": "Volcengine Ark API Key",
                    "url": "https://console.volcengine.com/ark",
                },
                {
                    "key": "SEEDREAM_MODEL_ID",
                    "prompt": "Seedream model ID (e.g. doubao-seedream-4-0-250828)",
                    "url": "https://console.volcengine.com/ark",
                },
                {
                    "key": "ARK_BASE_URL",
                    "prompt": "Ark base URL",
                    "default": "https://ark.cn-beijing.volces.com/api/v3",
                },
            ],
        }

    def capabilities(self) -> Dict[str, Any]:
        return {"modalities": ["text"], "max_reference_images": 0}

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        *,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect_ratio = resolve_aspect_ratio(aspect_ratio)
        model = kwargs.get("model") or self.default_model()

        _log(f"generate() called: prompt={prompt!r}, aspect_ratio={aspect_ratio}, model={model}")

        # --- Input validation ---

        if not prompt:
            return error_response(
                error="Prompt is required",
                error_type="invalid_input",
                provider=self.name,
                model=model,
                prompt="",
                aspect_ratio=aspect_ratio,
            )

        if image_url or reference_image_urls:
            return error_response(
                error="volcengine-seedream is currently configured for text-to-image only",
                error_type="unsupported_modality",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )

        api_key = os.environ.get("ARK_API_KEY")
        if not api_key:
            return error_response(
                error="ARK_API_KEY is not set. Run: hermes config set ARK_API_KEY \"your-key\"",
                error_type="missing_credentials",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )

        # --- Size validation ---

        size = _size_for_aspect(aspect_ratio)
        size_error = _validate_size(size)
        if size_error:
            return error_response(
                error=size_error,
                error_type="invalid_size",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )

        # --- Build request ---

        base_url = os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
        endpoint = os.environ.get("SEEDREAM_IMAGE_ENDPOINT", "/images/generations")
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        url = f"{base_url}{endpoint}"

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "response_format": os.environ.get("SEEDREAM_RESPONSE_FORMAT", "url"),
            "watermark": os.environ.get("SEEDREAM_WATERMARK", "false").lower() in {"1", "true", "yes"},
        }

        # Optional: negative prompt
        negative_prompt = kwargs.get("negative_prompt") or os.environ.get("SEEDREAM_NEGATIVE_PROMPT")
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
            _log(f"negative_prompt={negative_prompt!r}")

        # Optional: CFG scale
        cfg_scale = kwargs.get("cfg_scale") or os.environ.get("SEEDREAM_CFG_SCALE")
        if cfg_scale is not None and cfg_scale != "":
            try:
                payload["cfg_scale"] = float(cfg_scale)
                _log(f"cfg_scale={payload['cfg_scale']}")
            except (TypeError, ValueError):
                pass

        # Optional: steps
        steps = kwargs.get("steps") or os.environ.get("SEEDREAM_STEPS")
        if steps is not None and steps != "":
            try:
                payload["steps"] = int(steps)
                _log(f"steps={payload['steps']}")
            except (TypeError, ValueError):
                pass

        # Optional: seed
        seed = kwargs.get("seed") or os.environ.get("SEEDREAM_SEED")
        if seed not in (None, ""):
            try:
                payload["seed"] = int(seed)
            except (TypeError, ValueError):
                payload["seed"] = seed

        # Optional: number of images (n)
        n_val = os.environ.get("SEEDREAM_N", "")
        if n_val:
            try:
                payload["n"] = int(n_val)
            except (TypeError, ValueError):
                pass

        _log(f"POST {url}  payload={ {k: v for k, v in payload.items() if k != 'prompt'} }")

        # --- Execute request ---

        try:
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=int(os.environ.get("SEEDREAM_TIMEOUT", "180")),
            )

            # Parse response body regardless of status
            try:
                data = resp.json()
            except Exception:
                data = {"raw_text": resp.text}

            # If non-200, build a detailed error
            if not resp.ok:
                api_error = _parse_api_error(resp)
                hint = ""
                if "InvalidParameter" in api_error and "size" in api_error:
                    hint = (
                        " The API requires images with at least 921600 total pixels "
                        "(e.g. 1024x1024, 1280x720, 960x960). "
                        "Configure sizes via SEEDREAM_SQUARE_SIZE / SEEDREAM_PORTRAIT_SIZE / SEEDREAM_LANDSCAPE_SIZE."
                    )
                return error_response(
                    error=f"{api_error}{hint}",
                    error_type="provider_response_error",
                    provider=self.name,
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                )

            # --- Extract image ---

            image = _extract_image(data)
            if not image:
                return error_response(
                    error=f"No image URL or base64 payload found in response: {data}",
                    error_type="provider_response_error",
                    provider=self.name,
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                )

            _log(f"generate() success: image={image[:80] if isinstance(image, str) else 'b64'}")

            return success_response(
                image=image,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                provider=self.name,
                modality="text",
                extra={"size": payload["size"]},
            )

        except requests.exceptions.Timeout:
            return error_response(
                error="Request timed out. Increase SEEDREAM_TIMEOUT (default 180s).",
                error_type="timeout",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
        except requests.exceptions.ConnectionError as exc:
            return error_response(
                error=f"Cannot connect to {url}: {exc}. Check ARK_BASE_URL.",
                error_type="connection_error",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
        except Exception as exc:
            _log(f"generate() exception: {type(exc).__name__}: {exc}")
            return error_response(
                error=str(exc),
                error_type=type(exc).__name__,
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )


def register(ctx) -> None:
    ctx.register_image_gen_provider(VolcengineSeedreamProvider())