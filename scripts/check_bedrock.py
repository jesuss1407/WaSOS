#!/usr/bin/env python3
"""Minuto 0: verifica acceso a los modelos Claude por Bedrock Mantle y mide latencia con una imagen sintética.

Uso: uv run --python 3.12 --with "anthropic[bedrock]" --with pillow python scripts/check_bedrock.py [modelo ...]
"""
import base64
import io
import sys
import time

from anthropic import AnthropicBedrockMantle
from PIL import Image, ImageDraw

MODELOS = sys.argv[1:] or ["anthropic.claude-sonnet-5", "anthropic.claude-opus-4-8", "anthropic.claude-opus-5-5"]

img = Image.new("RGB", (640, 480), (90, 120, 160))
ImageDraw.Draw(img).rectangle([0, 300, 640, 480], fill=(110, 90, 60))
buf = io.BytesIO()
img.save(buf, "JPEG", quality=70)
imagen = {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                      "data": base64.b64encode(buf.getvalue()).decode()}}

cliente = AnthropicBedrockMantle(aws_region="us-east-1", timeout=30, max_retries=0)
for modelo in MODELOS:
    t = time.time()
    try:
        r = cliente.messages.create(model=modelo, max_tokens=100,
                                    messages=[{"role": "user", "content": [imagen, {"type": "text", "text": "Describe en 10 palabras."}]}])
        print(f"OK    {modelo:32} {time.time() - t:5.1f} s  {r.content[0].text[:60]!r}")
    except Exception as e:  # noqa: BLE001
        print(f"FALLA {modelo:32} {time.time() - t:5.1f} s  {type(e).__name__}: {str(e)[:120]}")
