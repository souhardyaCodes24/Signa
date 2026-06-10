"""
client.py — sends a SHA-256 hash to the Signa API and returns the verdict.
"""

import httpx


API_BASE_URL = "http://127.0.0.1:8000"


def lookup_hash(hash_value: str) -> dict:
    """
    GET /api/lookup/{hash} from the FastAPI backend.
    Returns JSON dict, or raises a clean error message string.
    """
    url = f"{API_BASE_URL}/api/lookup/{hash_value}"

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
        resp.raise_for_status()
        return resp.json()

    except httpx.ConnectError:
        raise ConnectionError(
            "Cannot connect to Signa API at {}. "
            "Make sure the server is running (python -m api.main)".format(API_BASE_URL)
        )
    except httpx.TimeoutException:
        raise TimeoutError("Signa API did not respond within 10 seconds")
    except httpx.HTTPStatusError as e:
        # The API returned a 4xx/5xx — forward its error detail
        detail = "unknown error"
        try:
            detail = e.response.json().get("detail", detail)
        except Exception:
            pass
        raise ConnectionError("API returned error: {}".format(detail))
