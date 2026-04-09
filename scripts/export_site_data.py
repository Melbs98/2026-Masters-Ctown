from pathlib import Path
import json
from datetime import datetime, timezone
from openpyxl import load_workbook

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = REPO_ROOT / "data" / "2026 Masters Draft & Scoreboard.xlsx"
OUT_DIR = REPO_ROOT / "docs" / "data"

def score_to_number(value):
    if value is None or value == "":
        return None
    text = str(value).strip().upper()
    if text == "E":
        return 0
    if text in {"CUT", "WD", "DQ"}:
        return "CUT"
    try:
        return int(text)
    except ValueError:
        return None

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    wb = load_workbook(WORKBOOK_PATH, data_only=True)
    scores_ws = wb["Scores"]
    teams_ws = wb["Team_Scoring"]

    scores_lookup = {}
    score_rows = []

    for row in scores_ws.iter_rows(min_row=2, max_row=scores_ws.max_row, min_col=1, max_col=10, values_only=True):
        player = row[2]
        score = row[3]
        if not player:
            continue

        player_name = str(player).strip()
        numeric_score = score_to_number(score)

        scores_lookup[player_name] = {
            "pos": row[1],
            "player": player_name,
            "score": score,
            "today": row[4],
            "thru": row[5],
            "r1": row[6],
            "r2": row[7],
            "r3": row[8],
            "r4": row[9],
            "numeric_score": numeric_score,
        }
        score_rows.append(scores_lookup[player_name])

    teams = []
    headers = [cell.value for cell in teams_ws[1]]

    for row in teams_ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue

        team_name = str(row[0]).strip()
        golfers = [str(x).strip() for x in row[1:] if x]

        golfer_details = []
        valid_scores = []

        for golfer in golfers:
            info = scores_lookup.get(golfer, {
                "player": golfer,
                "score": "",
                "pos": "",
                "today": "",
                "thru": "",
                "numeric_score": None
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
