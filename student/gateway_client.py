import gzip
import json

import requests
from django.conf import settings


class GatewayError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _gateway_url(path: str) -> str:
    base = settings.API_GATEWAY_URL.rstrip("/")
    clean_path = path if path.startswith("/") else f"/{path}"
    return f"{base}{clean_path}"


def _parse_json_safe(resp: requests.Response) -> dict:
    raw = resp.content
    if raw[:2] == b"\x1f\x8b":  # still gzip after requests' decode
        raw = gzip.decompress(raw)
        print(raw[:4], resp.headers)


def login_student(email: str, password: str) -> dict:
    try:
        resp = requests.post(
            _gateway_url("/api/v1/auth/login"),
            json={"email": email, "password": password},
            headers={"Accept": "application/json"},
            timeout=settings.API_GATEWAY_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise GatewayError(
            "Unable to reach the authentication gateway. Please try again."
        ) from exc

    if resp.status_code == 429:
        raise GatewayError(
            "Too many login attempts. Please wait a moment and try again.",
            status_code=429,
        )

    if resp.status_code in (400, 401):
        detail = ""
        if resp.content and resp.content.strip():
            try:
                parsed = json.loads(resp.content.decode("utf-8"))
                if isinstance(parsed, dict):
                    detail = parsed.get("message") or parsed.get("detail") or ""
            except (UnicodeDecodeError, ValueError):
                detail = ""
        raise GatewayError(
            detail or "Invalid student email or password.",
            status_code=resp.status_code,
        )

    if not resp.ok:
        raise GatewayError(
            f"Authentication gateway error (HTTP {resp.status_code}).",
            status_code=resp.status_code,
        )

    return _parse_json_safe(resp)


def get_current_user(access_token: str) -> tuple[int, dict | None]:
    try:
        resp = requests.get(
            _gateway_url("/api/v1/auth/me"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            timeout=settings.API_GATEWAY_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise GatewayError("Unable to load student profile from gateway.") from exc

    if resp.status_code == 200:
        return 200, _parse_json_safe(resp)
    return resp.status_code, None


def refresh_access_token(refresh_token: str) -> dict | None:
    try:
        resp = requests.post(
            _gateway_url("/api/v1/auth/refresh"),
            json={"refreshToken": refresh_token},
            headers={"Accept": "application/json"},
            timeout=settings.API_GATEWAY_TIMEOUT,
        )
    except requests.RequestException:
        return None

    if resp.status_code == 200:
        try:
            return _parse_json_safe(resp)
        except GatewayError:
            return None
    return None
