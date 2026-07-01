import json
import os
import threading
from urllib.request import Request, urlopen


def unload_ollama_models(
    base_url: str,
    models: list[str],
    timeout_seconds: float = 30,
) -> list[str]:
    endpoint = f"{base_url.rstrip('/')}/api/generate"
    unloaded = []

    for model in dict.fromkeys(model for model in models if model):
        payload = json.dumps({
            "model": model,
            "prompt": "",
            "keep_alive": 0,
        }).encode("utf-8")
        request = Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request, timeout=timeout_seconds) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError(
                    f"Ollama returned HTTP {response.status} for {model}."
                )

        unloaded.append(model)

    return unloaded


def schedule_process_exit(delay_seconds: float = 0.75) -> None:
    timer = threading.Timer(delay_seconds, os._exit, args=(0,))
    timer.daemon = True
    timer.start()
