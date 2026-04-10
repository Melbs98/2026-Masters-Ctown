from pathlib import Path
import json
import re
import unicodedata
from datetime import datetime, timezone
from collections import OrderedDict
from openpyxl import load_workbook

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = REPO_ROOT / "data" / "2026 Masters Draft & Scoreboard.xlsx"
OUT_DIR = REPO_ROOT / "docs" / "data"

ALIASES = {
    "sam stevens": "samuel stevens",
    "nico echavarria": "nicolas echavarria",
    "johnny keefer": "john keefer",
}

def normalize_player_name(name):
    if name is None:
        return ""

    text = str(name).strip()
    text = re.sub(r"\s*\((a|A)\)\s*", "", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)

    return ALIASES.get(text, text)

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

def round_score_to_number(value):
    if value is None or value == "":
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None

def is_real_score_row(pos, player, score, thru):
    if not player or score is None:
        return False

    player = str(player).strip()
    pos = str(pos).strip() if pos is not None else ""
    score = str(score).strip().upper()
    thru = str(thru).strip().upper() if thru is not None else ""

    banned_players = {"PLAYER", "YARDS", "TOURNAMENTS", "PREVIOUS WINNER", "HIDDEN"}
    if player.upper() in banned_players:
        return False

    if player.isdigit():
        return False

    if any(ch.isdigit() for ch in player):
        return False

    if not re.fullmatch(r"(T?\d+|CUT|WD|DQ)", pos):
        return False

    if not re.fullmatch(r"(E|[+-]?\d+|CUT|WD|DQ)", score):
        return False

    if thru and not re.fullmatch(r"(\d+|F|CUT|WD|DQ)", thru):
        return False

    return True

def split_payout(label, winners, total_amount):
    if not winners:
        return None

    share = round(total_amount / len(winners), 2)
    return {
        "label": label,
        "winners": [{"name": winner, "amount": share} for winner in winners]
    }

def rank_with_ties(items, score_key):
    valid = [item for item in items if item.get(score_key) is not None]
    valid.sort(key=lambda x: (x[score_key], x["name"]))

    ranked_groups = []
    i = 0
    place = 1

    while i < len(valid):
        score = valid[i][score_key]
        tied = [valid[i]]
        i += 1
        while i < len(valid) and valid[i][score_key] == score:
            tied.append(valid[i])
            i += 1

        ranked_groups.append({
            "place": place,
            "score": score,
            "items": tied
        })
        place += len(tied)

    return ranked_groups

def get_group_starting_at_place(groups, place):
    for g in groups:
        if g["place"] == place:
            return g
    return None

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
        thru = row[5]

        if not is_real_score_row(pos, player, score, thru):
            continue

        lookup_name = normalize_player_name(player)
        numeric_score = score_to_number(score)

        r1 = round_score_to_number(row[6])
        r2 = round_score_to_number(row[7])
        r3 = round_score_to_number(row[8])
        r4 = round_score_to_number(row[9])

        day2_total = (r1 + r2) if r1 is not None and r2 is not None else None
        day3_total = (r1 + r2 + r3) if r1 is not None and r2 is not None and r3 is not None else None

        entry = {
            "pos": str(pos).strip(),
            "player": str(player).strip(),
            "score": str(score).strip(),
            "today": "" if row[4] is None else str(row[4]).strip(),
            "thru": "" if row[5] is None else str(row[5]).strip(),
            "r1": "" if row[6] is None else str(row[6]).strip(),
            "r2": "" if row[7] is None else str(row[7]).strip(),
            "r3": "" if row[8] is None else str(row[8]).strip(),
            "r4": "" if row[9] is None else str(row[9]).strip(),
            "numeric_score": numeric_score,
            "day2_total": day2_total,
            "day3_total": day3_total,
        }

        scores_lookup[lookup_name] = entry
        score_rows.append(entry)

    teams_map = OrderedDict()

    for row in draft_ws.iter_rows(min_row=2, max_row=draft_ws.max_row, min_col=1, max_col=5, values_only=True):
        team = row[3]
        player = row[4]

        if not team or not player:
            continue

        team_name = str(team).strip()
        player_name = normalize_player_name(player)

        if team_name not in teams_map:
            teams_map[team_name] = []

        teams_map[team_name].append(player_name)

    teams = []
    team_day2 = []
    team_day3 = []

    for team_name, golfers in teams_map.items():
        golfer_details = []
        valid_scores = []
        valid_day2 = []
        valid_day3 = []

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
                "day2_total": None,
                "day3_total": None,
            })

            golfer_details.append(info)

            if info["numeric_score"] is not None:
                valid_scores.append(info["numeric_score"])

            if info["day2_total"] is not None:
                valid_day2.append(info["day2_total"])

            if info["day3_total"] is not None:
                valid_day3.append(info["day3_total"])

        best_four = sorted(valid_scores)[:4]
        best_four_total = sum(best_four) if len(best_four) >= 4 else None

        best_four_day2 = sorted(valid_day2)[:4]
        best_four_day2_total = sum(best_four_day2) if len(best_four_day2) >= 4 else None

        best_three_day3 = sorted(valid_day3)[:3]
        best_three_day3_total = sum(best_three_day3) if len(best_three_day3) >= 3 else None

        teams.append({
            "team": team_name,
            "golfers": golfer_details,
            "best4_total": best_four_total,
            "scores_entered": len(valid_scores),
            "roster_loaded": len(golfers),
        })

        team_day2.append({
            "name": team_name,
            "score": best_four_day2_total,
        })

        team_day3.append({
            "name": team_name,
            "score": best_three_day3_total,
        })

    teams_sorted = sorted(
        teams,
        key=lambda t: (99999 if t["best4_total"] is None else t["best4_total"], t["team"])
    )

    payouts = []

    # Leader after Day 2 - $50
    day2_players = [{"name": s["player"], "score": s["day2_total"]} for s in score_rows if s["day2_total"] is not None]
    if day2_players:
        best_day2 = min(p["score"] for p in day2_players)
        winners = [p["name"] for p in day2_players if p["score"] == best_day2]
        item = split_payout("Leader after Day 2", winners, 50)
        if item:
            payouts.append(item)

    # Best 4-man team after Day 2 - $50
    valid_team_day2 = [t for t in team_day2 if t["score"] is not None]
    if valid_team_day2:
        best_score = min(t["score"] for t in valid_team_day2)
        winners = [t["name"] for t in valid_team_day2 if t["score"] == best_score]
        item = split_payout("Best 4-Man Team after Day 2", winners, 50)
        if item:
            payouts.append(item)

    # Leader after Day 3 - $50
    day3_players = [{"name": s["player"], "score": s["day3_total"]} for s in score_rows if s["day3_total"] is not None]
    if day3_players:
        best_day3 = min(p["score"] for p in day3_players)
        winners = [p["name"] for p in day3_players if p["score"] == best_day3]
        item = split_payout("Leader after Day 3", winners, 50)
        if item:
            payouts.append(item)

    # Best 3-man team after Day 3 - $50
    valid_team_day3 = [t for t in team_day3 if t["score"] is not None]
    if valid_team_day3:
        best_score = min(t["score"] for t in valid_team_day3)
        winners = [t["name"] for t in valid_team_day3 if t["score"] == best_score]
        item = split_payout("Best 3-Man Team after Day 3", winners, 50)
        if item:
            payouts.append(item)

    # Final overall payouts: 1st $275, 2nd $150, 3rd $100
    final_team_rank_items = [{"name": t["team"], "final_score": t["best4_total"]} for t in teams if t["best4_total"] is not None]
    ranked = rank_with_ties(final_team_rank_items, "final_score")

    first_group = get_group_starting_at_place(ranked, 1)
    if first_group:
        payouts.append(split_payout("1st Overall", [i["name"] for i in first_group["items"]], 275))

    second_group = get_group_starting_at_place(ranked, 2)
    third_group = get_group_starting_at_place(ranked, 3)

    if second_group:
        if len(second_group["items"]) > 1:
            combined = 150 + 100
            payouts.append(split_payout("Tied for 2nd Overall", [i["name"] for i in second_group["items"]], combined))
        else:
            payouts.append(split_payout("2nd Overall", [i["name"] for i in second_group["items"]], 150))
            if third_group:
                payouts.append(split_payout("3rd Overall", [i["name"] for i in third_group["items"]], 100))

    # Final best 3-man team - $175
    if valid_team_day3:
        best_score = min(t["score"] for t in valid_team_day3)
        winners = [t["name"] for t in valid_team_day3 if t["score"] == best_score]
        payouts.append(split_payout("Final Best 3-Man Team", winners, 175))

    payouts = [p for p in payouts if p is not None]

    with open(OUT_DIR / "teams.json", "w", encoding="utf-8") as f:
        json.dump(teams_sorted, f, indent=2, ensure_ascii=False)

    with open(OUT_DIR / "scores.json", "w", encoding="utf-8") as f:
        json.dump(score_rows, f, indent=2, ensure_ascii=False)

    with open(OUT_DIR / "payouts.json", "w", encoding="utf-8") as f:
        json.dump({"items": payouts}, f, indent=2, ensure_ascii=False)

    with open(OUT_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump(
            {"last_updated": datetime.now(timezone.utc).isoformat()},
            f,
            indent=2
        )

    print("Exported website data with payouts.")

if __name__ == "__main__":
    main()
