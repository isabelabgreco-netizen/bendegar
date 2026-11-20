#!/usr/bin/env python3
"""
watch.py - send a video file to Gemini and get back what it sees and hears.

Uploads the file with the Gemini File API, waits until it is processed, asks
the prompt, prints the answer, then deletes the uploaded copy.

Reads the key from GEMINI_API_KEY. Never prints it.

Usage
  python3 watch.py VIDEO [VIDEO ...] [--prompt TEXT | --prompt-file FILE]
                   [--model NAME] [--keep]
"""

import argparse
import json
import mimetypes
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

BASE = "https://generativelanguage.googleapis.com"
DEFAULT_MODELS = ["gemini-3.1-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash"]

DEFAULT_PROMPT = """Você é um diretor de vídeo analisando um reel de Instagram (provavelmente de um tatuador).
Responda em português do Brasil. Assista o vídeo inteiro COM O ÁUDIO.

1. LINHA DO TEMPO: liste cada cena com tempo de início e fim (mm:ss.s), o que aparece,
   o enquadramento (close, plano aberto, macro), se a câmera se mexe, e todo texto na tela, palavra por palavra.
2. ÁUDIO: é música, fala, som ambiente ou som da máquina? Se tiver fala, transcreva tudo com tempos.
   Descreva a música (gênero, ritmo, se os cortes caem na batida) e momentos de som original.
3. PRIMEIROS 2 SEGUNDOS: o que exatamente prende a atenção? Por que alguém pararia de rolar?
4. RITMO: duração média dos cortes em cada parte; onde acelera, onde segura.
5. O QUE TORNA ESSE VÍDEO BOM (ou fraco), em pontos objetivos.
6. RECEITA: um roteiro plano a plano que outra tatuadora poderia gravar copiando o FORMATO, não o conteúdo.
Seja específico e não invente o que não dá pra ver ou ouvir; quando não tiver certeza, diga."""


def ctx():
    cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if not cafile and os.path.exists("/root/.ccr/ca-bundle.crt"):
        cafile = "/root/.ccr/ca-bundle.crt"
    return ssl.create_default_context(cafile=cafile) if cafile else ssl.create_default_context()


def req(method, url, key, data=None, headers=None, raw=False):
    h = {"x-goog-api-key": key}
    h.update(headers or {})
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, context=ctx(), timeout=600) as resp:
            body = resp.read()
            return (resp, body) if raw else json.loads(body or b"{}")
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:800]
        raise SystemExit(f"Gemini API error {e.code} on {method} {url.split('?')[0]}: {msg}")


def upload(path, key):
    size = os.path.getsize(path)
    mime = mimetypes.guess_type(path)[0] or "video/mp4"
    if path.lower().endswith(".mov"):
        mime = "video/quicktime"
    start, _ = req(
        "POST", f"{BASE}/upload/v1beta/files", key,
        data=json.dumps({"file": {"display_name": os.path.basename(path)}}).encode(),
        headers={
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": mime,
            "Content-Type": "application/json",
        }, raw=True)
    upload_url = start.headers.get("X-Goog-Upload-URL")
    if not upload_url:
        raise SystemExit("Gemini did not return an upload URL")
    with open(path, "rb") as f:
        data = f.read()
    _, body = req("POST", upload_url, key, data=data, headers={
        "Content-Length": str(size),
        "X-Goog-Upload-Offset": "0",
        "X-Goog-Upload-Command": "upload, finalize",
    }, raw=True)
    info = json.loads(body)["file"]
    name = info["name"]
    for _ in range(120):
        if info.get("state") == "ACTIVE":
            return info
        if info.get("state") == "FAILED":
            raise SystemExit(f"Gemini failed to process {path}")
        time.sleep(3)
        info = req("GET", f"{BASE}/v1beta/{name}", key)
    raise SystemExit(f"Timed out waiting for Gemini to process {path}")


def ask(files, prompt, model, key):
    parts = [{"file_data": {"mime_type": f["mimeType"], "file_uri": f["uri"]}} for f in files]
    parts.append({"text": prompt})
    out = req("POST", f"{BASE}/v1beta/models/{model}:generateContent", key,
              data=json.dumps({"contents": [{"role": "user", "parts": parts}]}).encode(),
              headers={"Content-Type": "application/json"})
    cands = out.get("candidates") or []
    if not cands:
        raise SystemExit(f"No answer from {model}: {json.dumps(out)[:500]}")
    return "".join(p.get("text", "") for p in cands[0].get("content", {}).get("parts", []))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--model", help="default: first available of " + ", ".join(DEFAULT_MODELS))
    ap.add_argument("--keep", action="store_true", help="do not delete the uploaded copy")
    a = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set")
    prompt = a.prompt or (open(a.prompt_file, encoding="utf-8").read() if a.prompt_file else DEFAULT_PROMPT)

    files = []
    try:
        for v in a.videos:
            print(f"[upload] {os.path.basename(v)}", file=sys.stderr)
            files.append(upload(v, key))
        models = [a.model] if a.model else DEFAULT_MODELS
        last = None
        for m in models:
            try:
                print(f"[ask] {m}", file=sys.stderr)
                print(ask(files, prompt, m, key))
                return
            except SystemExit as e:
                last = e
                print(f"[fallback] {m}: {str(e)[:200]}", file=sys.stderr)
        raise last
    finally:
        if not a.keep:
            for f in files:
                try:
                    req("DELETE", f"{BASE}/v1beta/{f['name']}", key)
                except SystemExit:
                    pass


if __name__ == "__main__":
    main()
