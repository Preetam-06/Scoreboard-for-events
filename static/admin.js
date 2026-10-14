const API_BASE = '/api';

function createTeamRow(team) {
    const row = document.createElement('tr');
    row.className = 'team-row new';
    row.dataset.teamId = team.id;
    row.innerHTML = `
        <td class="rank-cell"></td>
        <td class="name-cell"></td>
        <td class="points-cell"></td>
        <td class="actions-cell">
            <button class="neumorphic-btn-small edit-btn">Edit</button>
            <button class="neumorphic-btn-small danger delete-btn">Delete</button>
        </td>
    `;
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
    const editBtn = row.querySelector('.edit-btn');
    editBtn.dataset.id = team.id;
    editBtn.dataset.name = team.name;
    editBtn.dataset.points = team.points;
    editBtn.dataset.version = team.version ?? 0;
    const deleteBtn = row.querySelector('.delete-btn');
    deleteBtn.dataset.id = team.id;
    deleteBtn.dataset.name = team.name;
}

function animateReorder(rows, oldPositions) {
    requestAnimationFrame(() => {
        rows.forEach(row => {
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
        });
    });
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
    const tbody = document.querySelector('#scoreTable tbody');
    if (!tbody) return;

    const oldPositions = new Map(
        Array.from(tbody.querySelectorAll('.team-row')).map(row => [row.dataset.teamId, row.getBoundingClientRect()])
    );
    const rows = new Map(Array.from(tbody.querySelectorAll('.team-row')).map(row => [row.dataset.teamId, row]));

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

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    document.body.style.overflow = '';
}

async function updateTeam(teamId, data) {
    try {
        const res = await fetch(`${API_BASE}/teams/${teamId}`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
        });
        return await res.json();
    } catch (err) {
        console.error('Failed to update team:', err);
        return { success: false };
    }
}

async function updateEventName(eventName) {
    try {
        const res = await fetch('/api/settings', {
            method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event_name: eventName })
        });
        return await res.json();
    } catch (err) {
        console.error('Failed to update event name:', err);
        return { success: false };
    }
}

async function resetAllScores() {
    try {
        const res = await fetch(`${API_BASE}/reset`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ confirm: 'reset' })
        });
        return await res.json();
    } catch (err) {
        console.error('Failed to reset:', err);
        return { success: false };
    }
}

async function addTeam(name) {
    try {
        const res = await fetch(`${API_BASE}/teams`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name })
        });
        return await res.json();
    } catch (err) {
        console.error('Failed to add team:', err);
        return { success: false };
    }
}

async function deleteTeam(teamId) {
    try {
        const res = await fetch(`${API_BASE}/teams/${teamId}`, { method: 'DELETE' });
        return await res.json();
    } catch (err) {
        console.error('Failed to delete team:', err);
        return { success: false };
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchTeams().then(renderTeams);
    setInterval(() => fetchTeams().then(renderTeams), 3000);

    document.getElementById('saveEventNameBtn').addEventListener('click', async () => {
        const input = document.getElementById('eventNameInput');
        const status = document.getElementById('eventNameStatus');
        const result = await updateEventName(input.value.trim());
        status.textContent = result.success ? 'Event name saved.' : 'Could not save event name.';
        if (result.success) document.title = `${result.event_name} - Admin Panel`;
    });

    document.getElementById('addTeamBtn').addEventListener('click', () => {
        document.getElementById('addForm').reset(); openModal('addModal');
    });
    document.getElementById('cancelAdd').addEventListener('click', () => closeModal('addModal'));
    document.getElementById('addForm').addEventListener('submit', async e => {
        e.preventDefault();
        const name = document.getElementById('addTeamName').value.trim();
        if (!name) return;
        const result = await addTeam(name);
        if (result.success) { closeModal('addModal'); fetchTeams().then(renderTeams); }
        else alert('Failed to add team');
    });

    document.getElementById('resetBtn').addEventListener('click', () => {
        document.getElementById('resetInput').value = '';
        document.getElementById('confirmReset').disabled = true;
        openModal('resetModal');
    });
    document.getElementById('cancelReset').addEventListener('click', () => closeModal('resetModal'));
    document.getElementById('resetInput').addEventListener('input', e => {
        document.getElementById('confirmReset').disabled = e.target.value.toLowerCase() !== 'reset';
    });
    document.getElementById('confirmReset').addEventListener('click', async () => {
        const result = await resetAllScores();
        if (result.success) { closeModal('resetModal'); fetchTeams().then(renderTeams); }
        else alert(result.message || 'Failed to reset');
    });

    document.getElementById('cancelEdit').addEventListener('click', () => closeModal('editModal'));
    document.getElementById('editForm').addEventListener('submit', async e => {
        e.preventDefault();
        const teamId = parseInt(document.getElementById('editTeamId').value, 10);
        const version = parseInt(document.getElementById('editTeamVersion').value, 10);
        const name = document.getElementById('editTeamName').value.trim();
        const points = parseInt(document.getElementById('editTeamPoints').value, 10);
        if (!name || Number.isNaN(points)) return;
        const result = await updateTeam(teamId, { name, points, version });
        if (result.success) { closeModal('editModal'); fetchTeams().then(renderTeams); }
        else alert(result.message || 'Failed to update team');
    });

    document.querySelector('#scoreTable tbody').addEventListener('click', e => {
        if (e.target.classList.contains('delete-btn')) {
            const button = e.target;
            if (!confirm(`Delete ${button.dataset.name}? You can restore all teams with Reset All Scores.`)) return;
            deleteTeam(button.dataset.id).then(result => {
                if (result.success) fetchTeams().then(renderTeams);
                else alert(result.message || 'Failed to delete team');
            });
            return;
        }
        if (!e.target.classList.contains('edit-btn')) return;
        const btn = e.target;
        document.getElementById('editTeamId').value = btn.dataset.id;
        document.getElementById('editTeamVersion').value = btn.dataset.version || 0;
        document.getElementById('editTeamName').value = btn.dataset.name;
        document.getElementById('editTeamPoints').value = btn.dataset.points;
        openModal('editModal');
    });

    document.querySelectorAll('.modal').forEach(modal => modal.addEventListener('click', e => {
        if (e.target === modal) closeModal(modal.id);
    }));
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') document.querySelectorAll('.modal.active').forEach(m => closeModal(m.id));
    });
});
