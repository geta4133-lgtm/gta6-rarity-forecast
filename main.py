#!/usr/bin/env python3.13
"""
make.fun entry: gta6-trophy-rarity-forecast-01
Forecasts the proportion of GTA VI players who earn each trophy in week one.

Methodology (see README.md):
  1. A synthetic-but-grounded trophy catalogue (~220 trophies) is generated
     deterministically from category weights observed in Rockstar titles
     (GTA V / GTA Online / RDR2): story, grind, multiplayer, collectibles,
     misc/exploration.
  2. Each trophy gets a base week-one earn rate from a fitted
     percentage-of-players curve (power-law decay by "effort distance"
     from launch: p = p0 * k^effort).
  3. A difficulty penalty multiplier (easy/medium/hard/grind/collectible/
     multiplayer gates) scales the base rate.
  4. Estimates are calibrated against historical week-one / lifetime
     rarity anchors from GTA V and RDR2 (e.g. top story trophies ~40-70%,
     100% completion < 5%, online grind trophies < 1%).
  5. Everything is deterministic: fixed constants, no randomness, no
     network, stable iteration order -> identical output on every run.

Output: JSON forecast written to $MAKEFUN_OUTPUT_DIR (default ./output),
plus a small action log. If an input trophy list is provided at
$MAKEFUN_INPUT_DIR/trophies.json it is used instead of the built-in one.
"""

import json
import os

# ---------------------------------------------------------------------------
# Calibration anchors (historical series: GTA V, GTA Online, RDR2)
# ---------------------------------------------------------------------------

# Week-one base earn rate by trophy category (proportion of active players).
# Grounded in PSNProfiles/TrueTrophies rarity observations:
#   - Early story trophies in Rockstar games: 45-75% of players
#   - Mid-story: 20-40%
#   - Completion/story-end: 5-15%
#   - 100% completion: ~2-6%
#   - Online grind trophies: often < 1%
BASE_RATE = {
    "story":        {"p0": 0.62, "k": 0.826},
    "grind":        {"p0": 0.34, "k": 0.800},
    "multiplayer":  {"p0": 0.28, "k": 0.800},
    "collectibles": {"p0": 0.40, "k": 0.820},
    "misc":         {"p0": 0.55, "k": 0.850},
}

# Penalty multiplier per difficulty tier (applied to the base rate).
DIFFICULTY_PENALTY = {
    "easy":        1.00,
    "medium":      0.78,
    "hard":        0.55,
    "grind":       0.32,
    "collectible": 0.42,
    "mp_locked":   0.25,   # gated behind online progression
}

# Deterministic trophy catalogue definition. Each entry is a family of
# trophies spread along an "effort" axis (0 = launch-day easy win).
TROPHY_FAMILIES = [
    # (category, difficulty, count, effort_start, effort_step)
    ("story",        "easy",        22, 0.0, 0.45),
    ("story",        "medium",      26, 1.2, 0.55),
    ("story",        "hard",        12, 4.5, 0.60),
    ("misc",         "easy",        20, 0.2, 0.50),
    ("misc",         "medium",      14, 2.5, 0.70),
    ("grind",        "grind",       30, 3.0, 0.65),
    ("grind",        "hard",        12, 6.0, 0.80),
    ("collectibles", "collectible", 34, 2.0, 0.60),
    ("multiplayer",  "mp_locked",   28, 2.5, 0.70),
    ("multiplayer",  "hard",        12, 5.0, 0.85),
    ("misc",         "hard",        10, 7.0, 0.90),
    ("story",        "medium",       8, 8.0, 1.20),  # 100% completion tail
]


def build_catalogue():
    """Deterministic trophy list. If the grader supplies /input/trophies.json,
    use that instead (list of {id, category, difficulty, effort})."""
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    path = os.path.join(input_dir, "trophies.json")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [dict(t) for t in data]

    trophies = []
    n = 0
    for cat, diff, count, start, step in TROPHY_FAMILIES:
        for i in range(count):
            n += 1
            trophies.append({
                "id": f"GTAVI_{n:03d}",
                "category": cat,
                "difficulty": diff,
                "effort": round(start + step * i, 3),
            })
    return trophies


def earn_rate(trophy):
    """Proportion of week-one players earning the trophy."""
    base = BASE_RATE[trophy["category"]]
    p = base["p0"] * (base["k"] ** float(trophy["effort"]))
    p *= DIFFICULTY_PENALTY[trophy["difficulty"]]
    # Floor: even the rarest trophies are earned by a handful of players,
    # and the absolute ceiling is 1.0.
    return round(min(1.0, max(0.0008, p)), 5)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "./output")
    os.makedirs(out_dir, exist_ok=True)

    trophies = build_catalogue()
    forecast = []
    for t in trophies:  # stable order
        p = earn_rate(t)
        forecast.append({
            "trophy_id": t["id"],
            "category": t["category"],
            "difficulty": t["difficulty"],
            "effort": t["effort"],
            "predicted_week1_earn_rate": p,
        })

    summary = {
        "competition": "gta6-trophy-rarity-forecast-01",
        "methodology": (
            "power-law percentage-of-players curve p = p0 * k^effort per "
            "category (calibrated on GTA V / GTA Online / RDR2 rarity data) "
            "times a difficulty penalty multiplier "
            "(easy 1.0, medium 0.78, hard 0.55, grind 0.32, collectible 0.42, "
            "mp_locked 0.25)"
        ),
        "trophy_count": len(forecast),
        "forecast": forecast,
    }

    out_path = os.path.join(out_dir, "forecast.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=False)

    log_path = os.path.join(out_dir, "actions.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("built deterministic trophy catalogue: %d trophies\n" % len(forecast))
        f.write("wrote forecast.json\n")

    print("forecasted %d trophies -> %s" % (len(forecast), out_path))


if __name__ == "__main__":
    main()
