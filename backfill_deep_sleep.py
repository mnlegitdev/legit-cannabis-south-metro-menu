"""
One-off backfill: add a Claude-rated deep_sleep score to strains that were
enriched before deep_sleep was added to enrich_strains.py's RATINGS_PROMPT.
Only writes the deep_sleep field — leaves every other field untouched.
Safe to re-run; skips strains that already have deep_sleep.

Usage:
  ANTHROPIC_API_KEY=sk-ant-... python backfill_deep_sleep.py
"""

import json
import os
import sys

import anthropic

from enrich_strains import PRODUCTS_PATH, STRAINS_PATH, rate_moods


def run():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    with open(PRODUCTS_PATH) as f:
        db = json.load(f)
    with open(STRAINS_PATH) as f:
        existing = json.load(f)

    client = anthropic.Anthropic(api_key=api_key)

    missing = [k for k in existing if "deep_sleep" not in (existing[k].get("mood_ratings") or {})]
    if not missing:
        print("All strains already have a deep_sleep rating.")
        return

    print(f"Backfilling deep_sleep for {len(missing)} strain(s)...")
    for key in missing:
        product = db["products"].get(key, {"name": key})
        print(f"  → {product.get('name')}")
        ratings = rate_moods(client, product, existing[key])
        if ratings and "deep_sleep" in ratings:
            existing[key].setdefault("mood_ratings", {})["deep_sleep"] = ratings["deep_sleep"]
            print(f"    ✓ deep_sleep = {ratings['deep_sleep']}")
            with open(STRAINS_PATH, "w") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
        else:
            print("    ✗ failed, skipping")

    print(f"\nDone. Saved → {STRAINS_PATH}")


if __name__ == "__main__":
    run()
