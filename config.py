"""Load API credentials from Streamlit secrets or environment."""

import os
import ssl

import httpx
from dotenv import load_dotenv

load_dotenv()


def get_ssl_context() -> ssl.SSLContext:
    """Use the OS trust store (certifi alone fails on some Windows setups)."""
    return ssl.create_default_context()


def get_secret(key: str, default: str = "") -> str:
    try:
        import streamlit as st

        if isinstance(st.secrets, dict) and key in st.secrets:
            return st.secrets[key]
        for section in ("default", "general", "secrets"):
            section_data = st.secrets.get(section, {})
            if isinstance(section_data, dict) and key in section_data:
                return section_data[key]
    except Exception:
        pass
    return os.getenv(key, default)


def make_mistral_http_clients(api_key: str, timeout: int = 120) -> tuple[httpx.Client, httpx.AsyncClient]:
    base_url = get_secret("MISTRAL_BASE_URL", "https://api.mistral.ai/v1")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    ssl_context = get_ssl_context()
    client = httpx.Client(
        base_url=base_url,
        headers=headers,
        timeout=timeout,
        verify=ssl_context,
    )
    async_client = httpx.AsyncClient(
        base_url=base_url,
        headers=headers,
        timeout=timeout,
        verify=ssl_context,
    )
    return client, async_client
