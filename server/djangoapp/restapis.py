import requests

# HARDCODED - NO ENV VARS
backend_url = "http://localhost:3030"
sentiment_analyzer_url = "https://sentianalyzer.24x839ulbxjd.us-south.codeengine.appdomain.cloud"

print("=" * 50)
print(f"BACKEND URL IS: {backend_url}")
print("=" * 50)


def get_request(endpoint, **kwargs):
    # Remove leading slash to avoid double slashes
    if endpoint.startswith('/'):
        endpoint = endpoint[1:]

    # Build URL
    request_url = f"{backend_url}/{endpoint}"

    # Add params if any
    if kwargs:
        params = "&".join([f"{k}={v}" for k, v in kwargs.items()])
        request_url += f"?{params}"

    print(f"GET from {request_url}")

    try:
        response = requests.get(request_url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None


def analyze_review_sentiments(text):
    import urllib.parse
    encoded_text = urllib.parse.quote(text)
    request_url = f"{sentiment_analyzer_url}/analyze/{encoded_text}"

    try:
        response = requests.get(request_url, timeout=5)
        return response.json()
    except Exception as e:
        print(f"Sentiment error: {e}")
        return {"sentiment": "neutral"}


def post_review(data_dict):
    request_url = f"{backend_url}/insert_review"

    try:
        response = requests.post(request_url, json=data_dict, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Post error: {e}")
        return None
