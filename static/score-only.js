const API_BASE = '/api';

function createTeamRow(team) {
    const row = document.createElement('tr');
    row.className = 'team-row new';
    row.dataset.teamId = team.id;
    row.innerHTML = '<td class="rank-cell"></td><td class="name-cell"></td><td class="points-cell"></td><td class="actions-cell"><button class="neumorphic-btn-small edit-btn">Edit</button></td>';
    return row;
}

function updateTeamRow(row, team, rank) {
    const pointsCell = row.querySelector('.points-cell');
    const oldPoints = parseInt(pointsCell.textContent, 10);
    row.style.setProperty('--rank', rank);
    row.querySelector('.rank-cell').textContent = rank;
    row.querySelector('.name-cell').textContent = team.name;
    pointsCell.textContent = team.points;
    if (!Number.isNaN(oldPoints) && oldPoints !== team.points) {
        pointsCell.classList.remove('updated');
        void pointsCell.offsetWidth;
        pointsCell.classList.add('updated');
        setTimeout(() => pointsCell.classList.remove('updated'), 650);
    }
    const button = row.querySelector('.edit-btn');
    button.dataset.id = team.id;
    button.dataset.name = team.name;
    button.dataset.points = team.points;
    button.dataset.version = team.version ?? 0;
}

function renderTeams(teams) {
    const tbody = document.querySelector('#scoreTable tbody');
    const rows = new Map(Array.from(tbody.querySelectorAll('.team-row')).map(row => [String(row.dataset.teamId), row]));
    teams.forEach((team, index) => {
        const row = rows.get(String(team.id)) || createTeamRow(team);
        rows.set(String(team.id), row);
        updateTeamRow(row, team, index + 1);
        tbody.appendChild(row);
    });
    rows.forEach((row, id) => { if (!teams.some(team => String(team.id) === id)) row.remove(); });
}

async function fetchTeams() {
    try { return await (await fetch(`${API_BASE}/teams`)).json(); }
    catch (error) { console.error('Failed to fetch teams:', error); return []; }
}

async function saveTeam(teamId, data) {
    try {
        return await (await fetch(`${API_BASE}/teams/${teamId}`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
        })).json();
    } catch (error) { return { success: false }; }
}

document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('editModal');
    fetchTeams().then(renderTeams);
    setInterval(() => fetchTeams().then(renderTeams), 3000);

    document.getElementById('cancelEdit').addEventListener('click', () => modal.classList.remove('active'));
    document.querySelector('#scoreTable tbody').addEventListener('click', event => {
        if (!event.target.classList.contains('edit-btn')) return;
        const button = event.target;
        document.getElementById('editTeamId').value = button.dataset.id;
        document.getElementById('editTeamVersion').value = button.dataset.version || 0;
        document.getElementById('editTeamName').value = button.dataset.name;
        document.getElementById('editTeamPoints').value = button.dataset.points;
        modal.classList.add('active');
    });

    document.getElementById('editForm').addEventListener('submit', async event => {
        event.preventDefault();
        const teamId = parseInt(document.getElementById('editTeamId').value, 10);
        const version = parseInt(document.getElementById('editTeamVersion').value, 10);
        const name = document.getElementById('editTeamName').value.trim();
        const points = parseInt(document.getElementById('editTeamPoints').value, 10);
        if (!name || Number.isNaN(points)) return;
        const result = await saveTeam(teamId, { name, points, version });
        if (result.success) { modal.classList.remove('active'); fetchTeams().then(renderTeams); }
        else alert(result.message || 'Could not update team');
    });
});
