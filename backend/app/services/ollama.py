import json
import os
from dataclasses import asdict, dataclass
from urllib.parse import urlparse

import requests
from pydantic import BaseModel, ValidationError


@dataclass(frozen=True)
class ModelStatus:
    available: bool
    model: str
    reason: str

    def as_dict(self) -> dict:
        return asdict(self)


class LocalModelError(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _loopback_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("OLLAMA_BASE_URL must be an HTTP loopback address")
    return value.rstrip("/")


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = _loopback_url(base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
        self.model = model or os.getenv("OLLAMA_MODEL", "gemma3:1b")

    def status(self, timeout: float = 1.5) -> ModelStatus:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=timeout)
            response.raise_for_status()
            names = {item.get("name") for item in response.json().get("models", [])}
            available = self.model in names or any(name and name.split(":")[0] == self.model for name in names)
            return ModelStatus(available, self.model, "ready" if available else "model_missing")
        except requests.Timeout:
            return ModelStatus(False, self.model, "timeout")
        except (requests.RequestException, ValueError, TypeError):
            return ModelStatus(False, self.model, "service_unavailable")

    def structured(self, system: str, user: str, schema_model: type[BaseModel], timeout: float) -> BaseModel:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": schema_model.model_json_schema(),
            "options": {"temperature": 0},
        }
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=timeout)
            if response.status_code == 404:
                raise LocalModelError("model_missing")
            response.raise_for_status()
            content = response.json()["message"]["content"]
            return schema_model.model_validate(json.loads(content))
        except requests.Timeout as error:
            raise LocalModelError("timeout") from error
        except LocalModelError:
            raise
        except requests.RequestException as error:
            raise LocalModelError("service_unavailable") from error
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, ValidationError) as error:
            raise LocalModelError("invalid_output") from error


ollama_client = OllamaClient()
