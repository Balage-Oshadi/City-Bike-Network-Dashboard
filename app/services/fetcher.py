import requests
import logging
import time
import json
import os

BASE_URL = "http://api.citybik.es/v2/networks"
MAX_RETRIES = 5
BACKOFF_FACTOR = 1.5
CACHE_DIR = "network_cache"

# Optional in-memory cache
network_detail_cache = {}

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def fetch_network_data():
    """Fetch the list of all networks."""
    url = BASE_URL
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get('networks', [])
    except requests.RequestException as e:
        logging.error(f"❌ Error fetching network list: {e}")
        return []

def fetch_network_details(network_id: str) -> dict:
    """Fetch detailed station data for a given network ID, with retry, memory and file caching."""

    # Check in-memory cache
    if network_id in network_detail_cache:
        return network_detail_cache[network_id]

    # Check file cache
    cache_path = os.path.join(CACHE_DIR, f"{network_id}.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
                network_detail_cache[network_id] = data
                return data
        except Exception as e:
            logging.warning(f"⚠️ Failed to load cache for {network_id}: {e}")

    url = f"{BASE_URL}/{network_id}"
    retries = 0

    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 429:
                wait_time = BACKOFF_FACTOR ** retries
                logging.warning(f"🚦 Rate limit hit (429) for {network_id}, retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                retries += 1
                continue

            response.raise_for_status()
            data = response.json().get("network", {})
            network_detail_cache[network_id] = data

            # Write to file cache
            try:
                with open(cache_path, "w") as f:
                    json.dump(data, f)
            except Exception as e:
                logging.warning(f"⚠️ Failed to save cache for {network_id}: {e}")

            return data

        except requests.exceptions.RequestException as e:
            logging.warning(f"⏳ Retry {retries + 1}/{MAX_RETRIES} for {network_id} due to: {e}")
            time.sleep(BACKOFF_FACTOR ** retries)
            retries += 1

    logging.error(f"❌ Failed to fetch details for {network_id} after {MAX_RETRIES} retries.")
    return {}
