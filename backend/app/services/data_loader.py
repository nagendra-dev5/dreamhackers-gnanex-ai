from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class DataLoaderError(Exception):
    pass


_CURRICULUM_CACHE: Optional[Dict[str, Any]] = None
_CANDIDATES_CACHE: Optional[Dict[str, Any]] = None


def _data_dir() -> Path:
    # repo root is three parents up from this file: services -> app -> backend -> repo
    return Path(__file__).resolve().parents[3] / "data"


def _load_json_file(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise DataLoaderError(f"Missing data file: {path}")
    except json.JSONDecodeError as exc:
        raise DataLoaderError(f"Malformed JSON in {path}: {exc.msg}") from exc


def get_curriculum() -> Dict[str, Any]:
    global _CURRICULUM_CACHE
    if _CURRICULUM_CACHE is not None:
        return _CURRICULUM_CACHE

    path = _data_dir() / "curriculum.json"
    data = _load_json_file(path)
    _CURRICULUM_CACHE = data
    return data


def get_all_candidates() -> Dict[str, Any]:
    global _CANDIDATES_CACHE
    if _CANDIDATES_CACHE is not None:
        return _CANDIDATES_CACHE

    path = _data_dir() / "candidates.json"
    data = _load_json_file(path)
    _CANDIDATES_CACHE = data
    return data


def find_candidate(member_id: Optional[str] = None, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    data = get_all_candidates()
    candidates = data.get("candidates", [])
    if member_id:
        for c in candidates:
            member = c.get("member", {})
            if member.get("id") == member_id:
                return c
    if name:
        lname = name.strip().lower()
        for c in candidates:
            member = c.get("member", {})
            if member.get("name", "").strip().lower() == lname:
                return c
    return None


def enrich_candidate_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Given a partial candidate profile (may contain id or name), return enriched dict.

    If no matching candidate is found, return the original profile dict.
    """
    if not profile:
        return {}

    member = profile.get("member") if isinstance(profile.get("member"), dict) else None
    # accept either {"id":...} at top-level or Pydantic model dict (name, role, etc.)
    member_id = None
    name = None
    if member and isinstance(member, dict):
        member_id = member.get("id")
        name = member.get("name")
    else:
        member_id = profile.get("id") or profile.get("memberId") or profile.get("member_id")
        name = profile.get("name") or profile.get("candidateName")

    found = find_candidate(member_id=member_id, name=name)
    if found:
        return found

    # nothing found: try to normalize keys to match expected structure
    normalized = {"member": {}}
    for k, v in profile.items():
        if k in {"id", "memberId", "member_id"}:
            normalized["member"]["id"] = v
        elif k in {"name", "candidateName"}:
            normalized["member"]["name"] = v
        elif k in {"jobRole", "role"}:
            normalized["member"]["jobRole"] = v
        else:
            normalized[k] = v

    return normalized
