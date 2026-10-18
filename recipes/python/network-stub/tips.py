"""Code under test that calls an HTTP API. The client is passed in, so a test can give it a stub transport."""
import httpx


def fetch_tip(client: httpx.Client) -> str:
    """The tip of the day, or a fallback when the service fails."""
    try:
        response = client.get("https://tips.example.com/today")
        response.raise_for_status()
        return response.json()["text"]
    except (httpx.HTTPError, KeyError, ValueError):
        return "Tip unavailable."
