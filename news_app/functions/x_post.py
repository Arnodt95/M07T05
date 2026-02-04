import os
import requests


def post_to_x(text: str) -> bool:
    """
    Post a short status update to X (Twitter).

    Uses:
    - X_BEARER_TOKEN (env)
    - X_TWEET_ENDPOINT (env; defaults to v2 endpoint)

    If credentials are missing, the function returns False and does nothing.
    """
    token = os.getenv("AAAAAAAAAAAAAAAAAAAAAOVg7QEAAAAA0rQMzqdimXXiz%2Fd%2F"
                      "q%2BxGbgN%2FHV0%3D6tDcHa6cp06heeW"
                      "bzfbJYEG2LSrJtw9rMTss4Iqfo891iE0Bhe", "").strip()
    if not token:
        return False

    url = os.getenv("X_TWEET_ENDPOINT", "https://api.x.com/2/tweets").strip()
    headers = {"Authorization": f"Bearer {token}", "Content-Type":
               "application/json"}
    payload = {"text": text[:280]}

    r = requests.post(url, headers=headers, json=payload, timeout=10)
    return r.status_code in (200, 201)
