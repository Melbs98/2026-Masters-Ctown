from pathlib import Path
import json
import re
from datetime import datetime, timezone
from collections import OrderedDict
from openpyxl import load_workbook

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = REPO_ROOT / "data" / "2026 Masters Draft & Scoreboard.xlsx"
OUT_DIR = REPO_ROOT / "docs" / "data"

POS_PATTERN = re.compile(r"^(T?\d+|CUT|WD|DQ)$")
SCORE_PATTERN = re.compile(r"^(E|[+-]?\d+)$")

def score_to_number(value):
    if value is None or value == "":
        return None
    text = str(value).strip().upper()
    if text in {"E", "(E)"}:
        return 0
    if text in {"CUT", "WD", "DQ"}:
        return None
    text = text.replace("(", "").replace(")", "")
    try:
        return int(text)
    except ValueError:
        return None

def is_real_score_row(pos, player, score):
    if not player or not score:
        return False

    player = str(player).strip()
    pos = str(pos).strip() if pos is not None else ""
    score = str(score).strip().upper()

    if len(player) < 3:
        return False
    if player in {"PLAYER", "Yards", "Tournaments", "Previous Winner"}:
        return False
    if not POS_PATTERN.match(pos):
        return False
    if not SCORE_PATTERN.match(score):
        return False

    return True

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    wb = load_workbook(WORKBOOK_PATH, data_only=True)
    scores_ws = wb["Scores"]
    draft_ws = wb["Draft_Import"]

    scores_lookup = {}
    score_rows = []

    for row in scores_ws.iter_rows(min_row=2, max_row=scores_ws.max_row, min_col=1, max_col=10, values_only=True):
        pos = row[1]
        player = row[2]
        score = row[3]

        if not is_real_score_row(pos, player, score):
            continue

        player_name = str(player).strip()
        numeric_score = score_to_number(score)

        entry = {
            "pos": str(pos).strip(),
            "player": player_name,
            "score": str(score).strip(),
            "today": "" if row[4] is None else str(row[4]).strip(),
            "thru": "" if row[5] is None else str(row[5]).strip(),
            "r1": "" if row[6] is None else str(row[6]).strip(),
            "r2": "" if row[7] is None else str(row[7]).strip(),
            "r3": "" if row[8] is None else str(row[8]).strip(),
            "r4": "" if row[9] is None else str(row[9]).strip(),
            "numeric_score": numeric_score,
        }

        scores_lookup[player_name] = entry
        score_rows.append(entry)

    teams_map = OrderedDict()

    for row in draft_ws.iter_rows(min_row=2, max_row=draft_ws.max_row, min_col=1, max_col=5, values_only=True):
        team = row[3]
        player = row[4]

        if not team or not player:
            continue

        team_name = str(team).strip()
        player_name = str(player).strip()

        if team_name not in teams_map:
            teams_map[team_name] = []

        teams_map[team_name].append(player_name)

    teams = []

    for team_name, golfers in teams_map.items():
        golfer_details = []
        valid_scores = []

        for golfer in golfers:
            info = scores_lookup.get(golfer, {
                "pos": "",
                "player": golfer,
                "score": "",
                "today": "",
                "thru": "",
                "r1": "",
                "r2": "",
                "r3": "",
                "r4": "",
                "numeric_score": None,
            })

            golfer_details.append(info)

            if info["numeric_score"] is not None:
                valid_scores.append(info["numeric_score"])

        best_four = sorted(valid_scores)[:4]
        best_four_total = sum(best_four) if len(best_four) >= 4 else None

        teams.append({
            "team": team_name,
            "golfers": golfer_details,
            "best4_total": best_four_total,
            "scores_entered": len(valid_scores),
            "roster_loaded": len(golfers),
        })

    teams_sorted = sorted(
        teams,
        key=lambda t: (99999 if t["best4_total"] is None else t["best4_total"], t["team"])
    )

    with open(OUT_DIR / "teams.json", "w", encoding="utf-8") as f:
        json.dump(teams_sorted, f, indent=2, ensure_ascii=False)

    with open(OUT_DIR / "scores.json", "w", encoding="utf-8") as f:
        json.dump(score_rows, f, indent=2, ensure_ascii=False)

    with open(OUT_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump(
            {"last_updated": datetime.now(timezone.utc).isoformat()},
            f,
            indent=2
        )

    print("Exported website data.")

if __name__ == "__main__":
    main()
