"""
Dispatcharr Timeshift Plugin - Version Check

Checks the GitHub Releases API to determine if a newer version
of the plugin is available. Results are cached in-memory for 24h
to avoid excessive API calls (unauthenticated limit: 60 req/h).

WHY IN-MEMORY CACHE?
    Each uWSGI worker is a separate process, so each caches independently.
    With 4 workers, that's max 4 API calls per 24h period (well within limit).
    Simpler than file/DB cache with no persistence dependency.

GitHub: https://github.com/cedric-marcoux/dispatcharr_timeshift
"""

import time
import logging
import requests

logger = logging.getLogger("plugins.dispatcharr_timeshift.version_check")

# In-memory cache: {repo: {"data": {...}, "timestamp": float}}
_cache = {}
CACHE_TTL = 86400  # 24 hours in seconds
API_TIMEOUT = 5    # seconds - prevents hanging if GitHub is slow


def check_for_update(repo, current_version):
    """
    Check GitHub releases for a newer version of the plugin.

    Queries the public GitHub Releases API (no auth required) and compares
    the latest release tag with the installed version.

    Args:
        repo: GitHub repository in "owner/repo" format
              (e.g., "cedric-marcoux/dispatcharr_timeshift")
        current_version: Currently installed version string (e.g., "1.2.4")

    Returns:
        dict with keys:
            has_update (bool): True if a newer version exists
            current (str): Installed version
            latest (str): Latest version from GitHub
            release_url (str): URL to the latest release page
            release_notes (str): First 200 chars of release notes
            checked_at (str): Timestamp of the check
            error (str|None): Error message if check failed
    """
    # Return cached result if still valid
    cached = _cache.get(repo)
    if cached and (time.time() - cached["timestamp"]) < CACHE_TTL:
        return cached["data"]

    result = {
        "has_update": False,
        "current": current_version,
        "latest": current_version,
        "release_url": f"https://github.com/{repo}/releases",
        "release_notes": "",
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": None,
    }

    try:
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        resp = requests.get(url, timeout=API_TIMEOUT, headers={
            "Accept": "application/vnd.github.v3+json"
        })

        if resp.status_code == 200:
            data = resp.json()
            # Strip leading "v" from tag (e.g., "v1.3.0" → "1.3.0")
            latest = data.get("tag_name", "").lstrip("v")
            result["latest"] = latest
            result["release_url"] = data.get("html_url", result["release_url"])
            body = data.get("body", "") or ""
            result["release_notes"] = body[:200] + ("..." if len(body) > 200 else "")
            result["has_update"] = _is_newer(latest, current_version)
        elif resp.status_code == 404:
            result["error"] = "No releases found"
        else:
            result["error"] = f"GitHub API returned {resp.status_code}"

    except requests.exceptions.Timeout:
        result["error"] = "GitHub API timeout"
        logger.debug("[Timeshift] Version check: GitHub API timeout after %ds", API_TIMEOUT)
    except requests.exceptions.ConnectionError:
        result["error"] = "Cannot reach GitHub"
        logger.debug("[Timeshift] Version check: cannot reach api.github.com")
    except Exception as e:
        result["error"] = str(e)
        logger.debug("[Timeshift] Version check error: %s", e)

    # Cache result (including errors) to avoid hammering GitHub
    _cache[repo] = {"data": result, "timestamp": time.time()}
    return result


def _is_newer(latest, current):
    """
    Compare two semver version strings.

    Returns True if latest > current using numeric tuple comparison.
    Falls back to string comparison if versions aren't valid semver.

    Args:
        latest: Latest version string (e.g., "1.3.0")
        current: Current version string (e.g., "1.2.4")

    Returns:
        bool: True if latest is newer than current
    """
    try:
        latest_parts = [int(x) for x in latest.split(".")]
        current_parts = [int(x) for x in current.split(".")]
        return latest_parts > current_parts
    except (ValueError, AttributeError):
        # Non-numeric version parts: fall back to string comparison
        return latest != current


def clear_cache(repo=None):
    """
    Clear the version check cache.

    Useful for testing or forcing a fresh check.

    Args:
        repo: Specific repo to clear, or None to clear all
    """
    if repo:
        _cache.pop(repo, None)
    else:
        _cache.clear()
