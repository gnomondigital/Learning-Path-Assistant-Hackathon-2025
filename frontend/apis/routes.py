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


def chat(message: str):
    url = "http://localhost:8080/chat"
    try:
        response = requests.post(url, json={"text": message})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")
        return None


def cleanup():
    url = "http://localhost:8080/cleanup"
    try:
        response = requests.post(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")
        return None
