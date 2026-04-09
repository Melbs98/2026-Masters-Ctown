async function loadJson(path) {
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
