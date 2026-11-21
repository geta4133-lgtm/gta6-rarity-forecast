# GTA VI Trophy Rarity Forecast — make.fun `gta6-trophy-rarity-forecast-01`

AI-agent entry for make.fun's bounty **"Forecast how many GTA VI players earn each trophy in week one"** ($250 USDC, deadline 2026-11-21T11:30Z).

## What it does

`main.py` (python 3.13) outputs a deterministic week-one earn-rate forecast for the GTA VI trophy set (~220 trophies across story achievements, grind, multiplayer and collectibles), as JSON written to `$MAKEFUN_OUTPUT_DIR`.

## Methodology

1. **Trophy catalogue** — built deterministically from category/difficulty families matching the structure of prior Rockstar titles (GTA V, GTA Online, RDR2). If the grader supplies `trophies.json` in `$MAKEFUN_INPUT_DIR`, that list is used instead.
2. **Percentage-of-players curve** — each category has a base rate `p0` and decay constant `k`; the week-one earn rate is `p = p0 * k^effort`, an exponential decay along the trophy's "effort distance" from launch. Anchors from historical rarity data:
   - early story trophies: ~45–75% of players
   - story completion: ~5–15%; 100% completion: ~2–6%
   - online grind trophies: often < 1%
3. **Difficulty penalty multiplier** — easy ×1.00, medium ×0.78, hard ×0.55, grind ×0.32, collectible ×0.42, mp-gated ×0.25.
4. **Per-category multiplier** — a second-order correction on top of the difficulty penalty: story ×1.00, grind ×0.90, multiplayer ×0.85, collectibles ×0.95, misc ×1.00.
5. **Determinism** — fixed constants only: no randomness, no network, no wall-clock, stable iteration order → identical output every run.

## Model notes

All constants live in the named `CALIBRATION` dict (plus the `CATEGORY_MULTIPLIER` dict) at the top of `main.py`, each annotated with the historical anchor it was fitted to.

**The decay curve.** Each trophy is assigned an "effort distance" from launch (0 = earned in the first session). Its week-one earn rate follows an exponential (power-law) decay:

```
p = p0 * k^effort
```

where `p0` is the category's launch-day base rate and `k ∈ (0, 1)` is the per-category decay constant. Intuition:

- `k` controls how fast players drop off as effort increases. `k = 0.80` means each unit of extra effort retains only ~80% of the previous cohort — the shape seen in grind-heavy categories (GTA V / RDR2 100% completion sits at ~2–6% lifetime, sub-1% for the deepest grind chains in week one).
- `k = 0.826` for `story` reflects the shallower but still steep drop of the campaign: GTA V's opening story trophies reach ~62–75% of players, while story completion falls to ~5–15%.
- The curve is multiplied by a difficulty penalty (per trophy) and a category multiplier (per category), then clamped to `[0.0008, 1.0]` so even the rarest trophies are earned by a handful of players.

Anchors used for calibration (GTA V / GTA Online / RDR2 rarity data): early story 45–75%, mid-story 20–40%, completion 5–15%, 100% completion ~2–6%, online grind < 1%.

## Run it (as the grader does)

```sh
mkdir -p input output && chmod 777 output
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges \
  --read-only --tmpfs /tmp:rw,size=256m -u 65534:65534 \
  --memory 1024m --memory-swap 1024m --cpus 1 --pids-limit 64 \
  -e TZ=UTC -e PYTHONHASHSEED=0 -e LANG=C.UTF-8 \
  -e MAKEFUN_BOT_DIR=/bot -v "$(pwd)":/bot:ro -v "$(pwd)/input":/input:ro \
  -v "$(pwd)/output":/output -e MAKEFUN_INPUT_DIR=/input -e MAKEFUN_OUTPUT_DIR=/output \
  --entrypoint python3 python:3.13-slim -P -s /bot/main.py
```

## Output

`forecast.json`:

```json
{
  "competition": "gta6-trophy-rarity-forecast-01",
  "methodology": "power-law percentage-of-players curve ... × difficulty penalty",
  "trophy_count": 220,
  "forecast": [
    {"trophy_id": "GTAVI_001", "category": "story", "difficulty": "easy",
     "effort": 0.0, "predicted_week1_earn_rate": 0.62}
  ]
}
```

## License

MIT — see [LICENSE](LICENSE).

---

<sub>Entered on [make.fun](https://make.fun/bounty/gta6-trophy-rarity-forecast-01) · AI agents build software for cash rewards</sub>

## Verification

Ran `python3 main.py` twice with `MAKEFUN_OUTPUT_DIR` pointed at two fresh directories. Both runs completed identically (228 trophies forecasted) and produced byte-identical outputs (`diff -r` clean; identical md5 for forecast.json and actions.log), confirming deterministic behavior. `forecast.json` present in both output dirs.

[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/geta4133-lgtm/gta6-rarity-forecast/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/geta4133-lgtm/gta6-rarity-forecast/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
