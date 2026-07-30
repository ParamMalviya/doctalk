import os
import sys
from urllib.parse import urlparse

import requests
from langchain_core.tools import tool

from doctalk.logger import logger
from doctalk.exception import CustomException


def _parse_repo_url(repo_url: str) -> str:
    '''
    pull "owner/repo" out of whatever github url the user pasted.
    handles trailing slash, a .git suffix, and a missing http scheme.
    returns e.g. "pallets/flask".
    '''
    # urlparse needs a scheme to split correctly; add one if missing
    if "//" not in repo_url:
        repo_url = "//" + repo_url

    path = urlparse(repo_url).path
    parts = [p for p in path.split("/") if p]

    if len(parts) < 2:
        raise ValueError(f"could not read owner/repo from url: {repo_url}")

    owner = parts[0]
    repo = parts[1]

    # strip a trailing .git if present
    if repo.endswith(".git"):
        repo = repo[:-4]

    return f"{owner}/{repo}"


def _github_headers() -> dict:
    '''
    build request headers. adds the token if one is set, which raises
    the rate limit from 60/hr to 5000/hr. works fine without it too.
    '''
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "doctalk",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


@tool
def github_repo_info(repo_url: str) -> str:
    '''
    Get live information about a public GitHub repository from its URL,
    including its description, star count, primary language, and the
    most recent commit. Use this when the user asks about a GitHub repo,
    a repository link, or the latest commit/activity on a repo.
    '''
    try:
        repo = _parse_repo_url(repo_url)
        headers = _github_headers()

        # 1. repo metadata
        info_resp = requests.get(
            f"https://api.github.com/repos/{repo}",
            headers=headers,
            timeout=10,
        )

        if info_resp.status_code == 404:
            return f"Repository '{repo}' was not found. Check the URL is a real public repo."
        if info_resp.status_code == 403:
            return "GitHub API rate limit hit. Try again in a little while."
        if info_resp.status_code != 200:
            return f"GitHub returned an unexpected status ({info_resp.status_code})."

        info = info_resp.json()

        # 2. latest commit (one item)
        commit_resp = requests.get(
            f"https://api.github.com/repos/{repo}/commits",
            headers=headers,
            params={"per_page": 1},
            timeout=10,
        )
        latest_commit = "unavailable"
        if commit_resp.status_code == 200:
            commits = commit_resp.json()
            if commits:
                c = commits[0]
                message = c["commit"]["message"].splitlines()[0]
                date = c["commit"]["author"]["date"]
                latest_commit = f"{message} (on {date})"

        # build a clean text summary for the model to use
        summary = (
            f"Repository: {info.get('full_name')}\n"
            f"Description: {info.get('description') or 'none'}\n"
            f"Language: {info.get('language') or 'not specified'}\n"
            f"Stars: {info.get('stargazers_count')}\n"
            f"Forks: {info.get('forks_count')}\n"
            f"Open issues: {info.get('open_issues_count')}\n"
            f"Last pushed: {info.get('pushed_at')}\n"
            f"Latest commit: {latest_commit}"
        )

        logger.info(f"github tool fetched info for {repo}")
        return summary

    except Exception as e:
        raise CustomException(e, sys) from e