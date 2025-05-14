import logging

import requests

logger = logging.getLogger("routes")


def root():
    url = "http://localhost:8080/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")
        return None
