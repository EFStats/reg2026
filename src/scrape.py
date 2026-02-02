import json
import os
import requests
import sys


def query_endpoint() -> dict:
    ''' Query registration server. Endpoint must be stored
    in environment variable ENDPOINT. '''
    try:
        url = os.environ["ENDPOINT"]
    except KeyError as e:
        sys.exit(f"query_endpoint: Exception while requesting endpoint: {e}")

    try:
        resp = requests.get(url)
    except requests.exceptions.RequestException as e:
        sys.exit(f"query_endpoint: Exception while querying: {e}")
    
    if not resp.ok:
        sys.exit(f"query_endpoint: HTTP status code: {resp.status_code}")

    if not resp.json()["ok"]:
        sys.exit(f"query_endpoint: Response not flagged as okay: {resp}")

    return resp.json()


def append_to_file(result: dict, filename: str = "./data/log.txt") -> None:
    ''' Append a JSON dict to the log file. '''
    try:
        with open(filename, "a") as f:
            f.write(json.dumps(result) + "\n")
    except IOError as e:
        sys.exit(f"append_to_file: Error opening file: {e}")


if __name__ == "__main__":
    append_to_file(query_endpoint())
    sys.exit(0)
