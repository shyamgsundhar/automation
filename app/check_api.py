import os
import urllib.request
import urllib.error
import socket
import ssl
from dotenv import load_dotenv

load_dotenv()

APIS = [
    {
        "name": "Groq",
        "url": "https://api.groq.com/openai/v1/models",
        "key": os.getenv("GROQ_API_KEY"),
    },
    {
        "name": "NVIDIA",
        "url": "https://integrate.api.nvidia.com/v1/models",
        "key": os.getenv("NVIDIA_API_KEY"),
    },
]


def check_api(api):
    print(f"\n{'=' * 45}")
    print(f"Checking {api['name']} API")
    print("=" * 45)

    key = api["key"]

    if not key:
        print("❌ API key missing. Check your .env file.")
        return

    request = urllib.request.Request(
        api["url"],
        headers={
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "User-Agent": "TechNewsBot-ConnectionCheck/1.0",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print("✅ Connection successful")
            print(f"HTTP Status: {response.status}")
            print("API endpoint is reachable.")

    except urllib.error.HTTPError as error:
        print("⚠️ Server responded, but returned an HTTP error.")
        print(f"HTTP Status: {error.code}")
        print(f"Reason: {error.reason}")

        if error.code == 401:
            print("Check whether the API key is valid.")
        elif error.code == 403:
            print("API access may be restricted.")
        elif error.code == 429:
            print("Rate limit or quota may have been reached.")

    except urllib.error.URLError as error:
        print("❌ Connection failed.")
        print(f"Reason: {error.reason}")

    except (socket.timeout, TimeoutError):
        print("❌ Connection timed out.")

    except ssl.SSLError as error:
        print("❌ SSL/TLS error.")
        print(f"Reason: {error}")

    except Exception as error:
        print(f"❌ Unexpected error: {type(error).__name__}")
        print(str(error))


if __name__ == "__main__":
    print("TECH NEWS BOT - API CONNECTION TEST")

    for api in APIS:
        check_api(api)

    print("\nConnection checks completed.")
