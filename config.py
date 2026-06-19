"""Load Neo4j and API credentials from Streamlit secrets or environment."""

import os

from dotenv import load_dotenv

load_dotenv()


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


def get_neo4j_config() -> tuple[str, str, str]:
    uri = get_secret("NEO4J_URI")
    username = get_secret("NEO4J_USERNAME")
    password = get_secret("NEO4J_PASSWORD")
    return uri, username, password
