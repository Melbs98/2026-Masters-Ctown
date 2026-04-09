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

function displayBestFourTotal(value) {
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
            <td>Best 4 Total</td>
            <td class="${scoreClass(team.best4_total)}">${displayBestFourTotal(team.best4_total)}</td>
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

async function main() {
  const [teams, scores, meta] = await Promise.all([
    loadJson("./data/teams.json"),
    loadJson("./data/scores.json"),
    loadJson("./data/meta.json")
  ]);

  renderTeams(teams);
  renderScores(scores);

  document.getElementById("updated").textContent =
    `Last updated: ${meta.last_updated}`;
}

main().catch(error => {
  console.error(error);
  document.getElementById("updated").textContent =
    "Could not load updated data.";
});async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return response.json();
}

function renderTeams(teams) {
  const tbody = document.querySelector("#teams-table tbody");
  tbody.innerHTML = "";

  teams.forEach((team, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${team.team ?? ""}</td>
      <td>${team.best4_total ?? ""}</td>
      <td>${team.scores_entered ?? ""}</td>
      <td>${team.roster_loaded ?? ""}</td>
    `;
    tbody.appendChild(tr);
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
      <td>${score.score ?? ""}</td>
      <td>${score.today ?? ""}</td>
      <td>${score.thru ?? ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function main() {
  const [teams, scores, meta] = await Promise.all([
    loadJson("./data/teams.json"),
    loadJson("./data/scores.json"),
    loadJson("./data/meta.json")
  ]);

  renderTeams(teams);
  renderScores(scores);

  document.getElementById("updated").textContent =
    `Last updated: ${meta.last_updated}`;
}

main().catch(error => {
  console.error(error);
  document.getElementById("updated").textContent =
    "Could not load updated data.";
});
