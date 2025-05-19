import logging
from typing import AsyncGenerator

import httpx
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


async def chat_streaming(message: str) -> AsyncGenerator[str, None]:
    url = "http://localhost:8000/chat_streaming"
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST", url, json={"text": message}
        ) as response:
            async for line in response.aiter_lines():
                if line.strip():
                    yield line
