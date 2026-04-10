async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return response.json();
}

function scoreClass(score) {
  if (score === null || score === undefined || score === "") return "";
  const text = String(score).trim().toUpperCase();

  if (text === "E" || text === "0") return "score-even";
  if (text === "CUT" || text === "WD" || text === "DQ") return "score-cut";
  if (text.startsWith("-")) return "score-under";
  if (text.startsWith("+")) return "score-over";

  const num = Number(text);
  if (!Number.isNaN(num)) {
    if (num < 0) return "score-under";
    if (num > 0) return "score-over";
    return "score-even";
  }

  return "";
}

function formatRelativeTime(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMinutes = Math.floor(diffMs / 60000);

  if (diffMinutes < 1) return "just now";
  if (diffMinutes === 1) return "1 minute ago";
  if (diffMinutes < 60) return `${diffMinutes} minutes ago`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours === 1) return "1 hour ago";
  if (diffHours < 24) return `${diffHours} hours ago`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return "1 day ago";
  return `${diffDays} days ago`;
}

function formatLastUpdated(isoString) {
  const date = new Date(isoString);

  const formattedTime = date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    timeZoneName: "short",
  });

  const relativeTime = formatRelativeTime(date);

  return `Last updated: ${formattedTime} (${relativeTime})`;
}

function displayBestTotal(value, label = "Best Total") {
  if (value === null || value === undefined || value === "") return "-";
  if (value > 0) return `+${value}`;
  return String(value);
}

function renderTeams(teams) {
  const grid = document.getElementById("teams-grid");
  grid.innerHTML = "";

  teams.forEach((team, index) => {
    const card = document.createElement("div");
    card.className = "team-card";

    const totalValue =
      team.best3_total ?? team.best4_total ?? null;

    const totalLabel =
      team.best3_total !== undefined ? "Best 3 Total" : "Best 4 Total";

    const golfersRows = team.golfers.map(golfer => {
      const score = golfer.score ?? "";
      const scoreText = score === "" ? "-" : score;
      const scoreCss = scoreClass(score);

      return `
        <tr>
          <td class="player-name">${golfer.player ?? ""}</td>
          <td class="score-cell ${scoreCss}">${scoreText}</td>
        </tr>
      `;
    }).join("");

    card.innerHTML = `
      <div class="team-card-header">
        <div class="team-rank">#${index + 1}</div>
        <div class="team-name">${team.team ?? ""}</div>
      </div>

      <table class="team-table">
        <thead>
          <tr>
            <th>Player</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          ${golfersRows}
        </tbody>
        <tfoot>
          <tr>
            <td>${totalLabel}</td>
            <td class="${scoreClass(totalValue)}">${displayBestTotal(totalValue)}</td>
          </tr>
        </tfoot>
      </table>
    `;

    grid.appendChild(card);
  });
}

function renderScores(scores) {
  const tbody = document.querySelector("#scores-table tbody");
  tbody.innerHTML = "";

  scores.forEach(score => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${score.pos ?? ""}</td>
      <td>${score.player ?? ""}</td>
      <td class="${scoreClass(score.score)}">${score.score ?? ""}</td>
      <td class="${scoreClass(score.today)}">${score.today ?? ""}</td>
      <td>${score.thru ?? ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

function updateTimestamp(meta) {
  document.getElementById("updated").textContent =
    formatLastUpdated(meta.last_updated);
}

async function main() {
  const [teams, scores, meta] = await Promise.all([
    loadJson("./data/teams.json"),
    loadJson("./data/scores.json"),
    loadJson("./data/meta.json")
  ]);

  renderTeams(teams);
  renderScores(scores);
  updateTimestamp(meta);

  // Refresh the "X minutes ago" text every 30 seconds
  setInterval(() => updateTimestamp(meta), 30000);
}

main().catch(error => {
  console.error(error);
  document.getElementById("updated").textContent =
    "Could not load updated data.";
});
