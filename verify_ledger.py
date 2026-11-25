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


def _validate_v2_payload(canonical_payload: dict) -> bool:
    """Validates schema_version '2.0' envelope structure, provenance, diagnostics, and 1.0000 probability conservation."""
    if not isinstance(canonical_payload, dict) or canonical_payload.get("schema_version") != "2.0":
        return False
    required_keys = (
        "schema_version",
        "sport",
        "league",
        "match_id",
        "home_team",
        "away_team",
        "kickoff_utc",
        "commit_window",
        "lineup_confirmed",
        "model_provenance",
        "markets",
        "model_diagnostics",
        "salt",
    )
    if any(k not in canonical_payload or canonical_payload[k] is None for k in required_keys):
        return False
    raw_str = json.dumps(canonical_payload).lower()
    if any(
        f'"{fk}"' in raw_str
        for fk in (
            "dynamic_alpha",
            "physics_anchor",
            "ml_ensemble",
            "model_telemetry",
            "base_learners",
            "stacking_weights",
            "meta_weights",
            "xgb",
            "lgbm",
            "lstm",
            "random_forest",
        )
    ):
        return False

    prov = canonical_payload.get("model_provenance")
    if not isinstance(prov, dict) or set(prov.keys()) != {"model_version", "bundle_id", "artifact_sha256"}:
        return False
    if any(not prov.get(pk) or not isinstance(prov.get(pk), str) for pk in ("model_version", "bundle_id", "artifact_sha256")):
        return False

    diag = canonical_payload.get("model_diagnostics")
    if not isinstance(diag, dict) or set(diag.keys()) != {"distribution_family", "entropy_score", "parameters"}:
        return False
    if diag.get("distribution_family") != "dixon_coles_poisson":
        return False
    try:
        if float(diag.get("entropy_score") or 0.0) <= 0.0:
            return False
    except (TypeError, ValueError):
        return False

    params = diag.get("parameters")
    expected_param_keys = {
        "lambda_home_struct",
        "lambda_away_struct",
        "lambda_home_final",
        "lambda_away_final",
        "rho",
    }
    if not isinstance(params, dict) or set(params.keys()) != expected_param_keys:
        return False
    try:
        for lk in ("lambda_home_struct", "lambda_away_struct", "lambda_home_final", "lambda_away_final"):
            if params.get(lk) is None or float(params[lk]) <= 0.0:
                return False
        if params.get("rho") is None:
            return False
        float(params["rho"])
    except (TypeError, ValueError):
        return False

    markets = canonical_payload.get("markets")
    if not isinstance(markets, dict):
        return False
    for m_key in ("1x2", "ou_2_5", "btts"):
        m_dict = markets.get(m_key)
        if not isinstance(m_dict, dict):
            return False
        if m_key == "1x2":
            subkeys = ("home_win", "draw", "away_win") if "draw" in m_dict else ("home_win", "away_win")
        elif m_key == "ou_2_5":
            subkeys = ("over", "under")
        else:
            subkeys = ("yes", "no")
        try:
            vals = [float(m_dict[sk]) for sk in subkeys]
        except (KeyError, TypeError, ValueError):
            return False
        tot = sum(vals)
        if any(v <= 0.0 for v in vals) or abs(round(tot, 4) - 1.0) > 1e-6 or abs(tot - 1.0) > 1e-6:
            return False
    return True


def verify_ledger(repo_root: str = ".") -> dict:
    """
    Verifies all commitments and reveals in the single-file WORM audit ledger.
    Auto-detects `schema_version` ("1.0" legacy vs "2.0" Veritas v2.0).
    Scans `[league_slug]/[season_year]/*.json` files.
    Returns verification stats dictionary.
    """
    # Exclude system/config JSON files at root or in hidden folders
    json_files = []
    for root_dir, dirs, files in os.walk(repo_root):
        # Skip hidden folders like .git
        dirs[:] = [d for d in dirs if not d.startswith(".")]
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
            print(
                f"⏳ [PENDING] {rel_path} ({fixture} @ {kickoff}): Committed ({expected_hash[:12]}...), awaiting kickoff."
            )
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

            schema_version = str(canonical_payload.get("schema_version") or doc.get("schema_version") or "1.0")
            actual_hash = compute_canonical_sha256(canonical_payload)

            if schema_version == "2.0":
                schema_valid = _validate_v2_payload(canonical_payload)
                hash_matches = schema_valid and (actual_hash.lower() == expected_hash.lower())
            else:
                if actual_hash.lower() != expected_hash.lower():
                    # Check if commitment was hashed under legacy reference_odds schema
                    p_copy = dict(canonical_payload)
                    if "reference_odds" in p_copy and isinstance(p_copy["reference_odds"], dict):
                        ro = p_copy["reference_odds"]
                        legacy_ro = {}
                        if "away_win" in ro or "away" in ro:
                            legacy_ro["away"] = ro.get("away_win") if ro.get("away_win") is not None else ro.get("away")
                        if "draw" in ro or "tie" in ro:
                            legacy_ro["draw"] = ro.get("draw") if ro.get("draw") is not None else ro.get("tie")
                        if "home_win" in ro or "home" in ro:
                            legacy_ro["home"] = ro.get("home_win") if ro.get("home_win") is not None else ro.get("home")
                        sb = ro.get("sportsbook") or ro.get("provider") or "pinnacle"
                        legacy_ro["provider"] = str(sb).lower()
                        p_copy["reference_odds"] = legacy_ro
                        legacy_hash = compute_canonical_sha256(p_copy)
                        if legacy_hash.lower() == expected_hash.lower():
                            actual_hash = expected_hash
                hash_matches = actual_hash.lower() == expected_hash.lower()

            if hash_matches:
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

            print(
                f"{status_str} {rel_path} ({fixture} -> {actual_res}): Hash ({actual_hash[:12]}...){brier_str}{clv_str}"
            )

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
