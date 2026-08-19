#!/usr/bin/env python3
"""
Zero-dependency 1-click Python script for quants to verify SHA-256 ledger commitments and settlement metrics.
"""

import hashlib
import json
import os
import sys


def compute_canonical_sha256(payload_dict: dict) -> str:
    """Computes deterministic key-sorted SHA-256 hash of a JSON payload dictionary."""

    def format_floats(obj):
        if isinstance(obj, float):
            return f"{obj:.4f}"
        elif isinstance(obj, dict):
            return {k: format_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [format_floats(v) for v in obj]
        return obj

    formatted_payload = format_floats(payload_dict)
    canonical_json = json.dumps(formatted_payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def verify_ledger(repo_root: str = ".") -> dict:
    """
    Verifies all commitments and reveals in the single-file WORM audit ledger.
    Scans `[league_slug]/[season_year]/*.json` files.
    Returns verification stats dictionary.
    """
    # Exclude system/config JSON files at root or in hidden folders
    json_files = []
    for root_dir, dirs, files in os.walk(repo_root):
        # Skip hidden folders like .git
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        rel_root = os.path.relpath(root_dir, repo_root)
        parts = rel_root.split(os.sep)
        # We expect [league_slug]/[season_year] (depth 2)
        if len(parts) == 2 and not parts[0].startswith("."):
            for f in files:
                if f.endswith(".json") and "-vs-" in f:
                    json_files.append(os.path.join(root_dir, f))

    total_commits = 0
    verified_hashes = 0
    mismatched_hashes = 0
    missing_reveals = 0
    settled_matches = 0

    print(f"🔍 Discovered {len(json_files)} WORM ledger fixtures in '{repo_root}'.")
    print("-" * 75)

    for match_file in sorted(json_files):
        rel_path = os.path.relpath(match_file, repo_root)
        try:
            with open(match_file, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception as e:
            mismatched_hashes += 1
            print(f"❌ [ERROR] {rel_path}: Failed to parse JSON ({e})")
            continue

        status = doc.get("status")
        total_commits += 1

        if status == "COMMITTED":
            missing_reveals += 1
            expected_hash = doc.get("sha256_hash", "")
            fixture = doc.get("fixture", rel_path)
            kickoff = doc.get("kickoff_utc", "")
            print(f"⏳ [PENDING] {rel_path} ({fixture} @ {kickoff}): Committed ({expected_hash[:12]}...), awaiting kickoff.")
            continue

        if status == "REVEALED":
            expected_hash = doc.get("sha256_hash", "")
            canonical_payload = doc.get("canonical_payload")
            if not canonical_payload:
                fixture = doc.get("fixture", "")
                if " vs " in fixture:
                    home_team, away_team = fixture.split(" vs ", 1)
                else:
                    home_team = doc.get("home_team", "")
                    away_team = doc.get("away_team", "")
                rev_probs = doc.get("revealed_probabilities", {})
                probs = {
                    "home": rev_probs.get("home_win") or rev_probs.get("home", 0.0),
                    "away": rev_probs.get("away_win") or rev_probs.get("away", 0.0),
                }
                if "draw" in rev_probs and rev_probs["draw"] is not None:
                    probs["draw"] = rev_probs["draw"]

                canonical_payload = {
                    "match_id": doc.get("match_id", ""),
                    "home_team": home_team,
                    "away_team": away_team,
                    "kickoff_time": doc.get("kickoff_utc", ""),
                    "market": "1X2",
                    "model_version": doc.get("model_version", "Veritas-v1.0"),
                    "probabilities": probs,
                    "salt": doc.get("salt", ""),
                }

            actual_hash = compute_canonical_sha256(canonical_payload)
            if actual_hash.lower() == expected_hash.lower():
                verified_hashes += 1
                settled_matches += 1
                status_str = "✅ [VERIFIED]"
            else:
                mismatched_hashes += 1
                status_str = "❌ [HASH MISMATCH]"

            settlement = doc.get("settlement", {})
            actual_res = settlement.get("actual_result", "")
            brier = settlement.get("brier_score")
            brier_str = f" | Brier: {brier:.4f}" if brier is not None else ""
            clv_str = " | CLV: BEAT" if settlement.get("clv_beat") else ""
            fixture = doc.get("fixture", rel_path)

            print(f"{status_str} {rel_path} ({fixture} -> {actual_res}): Hash ({actual_hash[:12]}...){brier_str}{clv_str}")

    print("-" * 75)
    print("📊 VERIFICATION SUMMARY:")
    print(f"   • Total Match Fixtures: {total_commits}")
    print(f"   • Verified Hashes:     {verified_hashes}")
    print(f"   • Pending Reveals:     {missing_reveals}")
    print(f"   • Hash Mismatches:     {mismatched_hashes}")
    print(f"   • Settled Matches:     {settled_matches}")

    return {
        "total_commits": total_commits,
        "verified_hashes": verified_hashes,
        "mismatched_hashes": mismatched_hashes,
        "missing_reveals": missing_reveals,
        "settled_matches": settled_matches,
    }


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    res = verify_ledger(root)
    if res["mismatched_hashes"] > 0:
        sys.exit(1)
    sys.exit(0)
