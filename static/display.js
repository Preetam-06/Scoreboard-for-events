const API_BASE = '/api';

function createTeamRow(team) {
    const row = document.createElement('tr');
    row.className = 'display-row new';
    row.dataset.teamId = team.id;
    row.innerHTML = '<td class="rank-cell"></td><td class="name-cell"></td><td class="points-cell"></td>';
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
}

function animateReorder(rows, oldPositions) {
    requestAnimationFrame(() => rows.forEach(row => {
        const oldRect = oldPositions.get(row.dataset.teamId);
        const newRect = row.getBoundingClientRect();
        if (!oldRect) {
            row.classList.add('new');
            setTimeout(() => row.classList.remove('new'), 550);
            return;
        }
        const deltaX = oldRect.left - newRect.left;
        const deltaY = oldRect.top - newRect.top;
        if (Math.abs(deltaX) < 1 && Math.abs(deltaY) < 1) return;
        row.style.transition = 'none';
        row.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
        requestAnimationFrame(() => {
            row.classList.add('reordering');
            row.style.transform = '';
            setTimeout(() => {
                row.classList.remove('reordering');
                row.style.transition = '';
            }, 600);
        });
    }));
}

async function fetchTeams() {
    try {
        const res = await fetch(`${API_BASE}/teams`);
        return await res.json();
    } catch (err) {
        console.error('Failed to fetch teams:', err);
        return [];
    }
}

function renderTeams(teams) {
    const tbody = document.querySelector('#displayTable tbody');
    if (!tbody) return;
    const oldPositions = new Map(
        Array.from(tbody.querySelectorAll('.display-row')).map(row => [row.dataset.teamId, row.getBoundingClientRect()])
    );
    const rows = new Map(Array.from(tbody.querySelectorAll('.display-row')).map(row => [row.dataset.teamId, row]));

    teams.forEach((team, index) => {
        const row = rows.get(String(team.id)) || createTeamRow(team);
        rows.set(String(team.id), row);
        updateTeamRow(row, team, index + 1);
    });
    Array.from(rows.entries()).forEach(([id, row]) => {
        if (!teams.some(team => String(team.id) === id)) row.remove();
    });
    teams.forEach(team => tbody.appendChild(rows.get(String(team.id))));
    animateReorder(teams.map(team => rows.get(String(team.id))), oldPositions);
}

async function pollUpdates() {
    renderTeams(await fetchTeams());
}

document.addEventListener('DOMContentLoaded', () => {
    fetchTeams().then(renderTeams);
    setInterval(pollUpdates, 3000);
});
