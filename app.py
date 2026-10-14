from pathlib import Path
import json
import os
from threading import Lock
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
# Vercel's deployed project directory is read-only. /tmp is writable but
# temporary, so use a real hosted database when scores must persist in production.
DATA_FILE = Path("/tmp/teams.json") if os.environ.get("VERCEL") else BASE_DIR / "teams.json"
SETTINGS_FILE = DATA_FILE.with_name("settings.json")
SCORES_LOG_FILE = DATA_FILE.with_name("scores_log.jsonl")
CHANGES_LOG_FILE = DATA_FILE.with_name("changes.log")

app = FastAPI(title="On the Spot Scoreboard")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
TEAM_WRITE_LOCK = Lock()


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def log_scores(action, teams, details=None):
    entry = {
        "timestamp": timestamp(),
        "action": action,
        "scores": [
            {"id": team["id"], "name": team["name"], "points": team["points"]}
            for team in teams
        ],
    }
    if details:
        entry["details"] = details
    with SCORES_LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")


def log_change(message):
    with CHANGES_LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(f"{timestamp()} | {message}\n")


def default_teams():
    names = [
        "Blackwood", "Redline", "Ironclad", "Deadlock", "Nightfall", "Overdrive",
        "Outlier", "Darkhorse", "Blackout", "Vanguard", "Renegade", "Dominion",
        "Fortune", "Legacy", "Empire", "Reckoning", "Gryffindor", "Slytherin",
        "Ravenclaw", "Hufflepuff", "Illuminati", "Titans", "Demigods", "Eternals",
    ]
    return [{"id": index, "name": name, "points": 0, "version": 0} for index, name in enumerate(names, start=1)]


def load_teams():
    if not DATA_FILE.exists():
        save_teams(default_teams())
    with DATA_FILE.open("r", encoding="utf-8") as file:
        teams = json.load(file)
    for team in teams:
        team.setdefault("version", 0)
    return teams


def save_teams(teams):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(teams, file, indent=2)


def ranked_teams():
    teams = sorted(load_teams(), key=lambda team: team["points"], reverse=True)
    for rank, team in enumerate(teams, start=1):
        team["rank"] = rank
    return teams


def load_settings():
    if not SETTINGS_FILE.exists():
        return {"event_name": "On the Spot"}
    with SETTINGS_FILE.open("r", encoding="utf-8") as file:
        settings = json.load(file)
    return {"event_name": settings.get("event_name", "On the Spot")}


def save_settings(settings):
    with SETTINGS_FILE.open("w", encoding="utf-8") as file:
        json.dump(settings, file, indent=2)


@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse(url="/display")


@app.get("/admin", include_in_schema=False)
def admin(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html", context={"teams": ranked_teams(), "event_name": load_settings()["event_name"], "full_access": False})


@app.get("/main/", include_in_schema=False)
def main_admin(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html", context={"teams": ranked_teams(), "event_name": load_settings()["event_name"], "full_access": True})


@app.get("/display", include_in_schema=False)
def display(request: Request):
    return templates.TemplateResponse(request=request, name="display.html", context={"teams": ranked_teams(), "event_name": load_settings()["event_name"]})


@app.get("/api/teams")
def get_teams():
    return ranked_teams()


@app.get("/api/settings")
def get_settings():
    return load_settings()


@app.put("/api/settings")
async def update_settings(request: Request):
    data = await request.json()
    event_name = str(data.get("event_name", "On the Spot")).strip() or "On the Spot"
    settings = {"event_name": event_name[:100]}
    save_settings(settings)
    log_change(f"Changed event name to: {settings['event_name']}")
    return {"success": True, **settings}


@app.put("/api/teams/{team_id}")
async def update_team(team_id: int, request: Request):
    data = await request.json()
    with TEAM_WRITE_LOCK:
        teams = load_teams()
        for team in teams:
            if team["id"] == team_id:
                submitted_version = data.get("version")
                if submitted_version is not None and int(submitted_version) != team["version"]:
                    return JSONResponse(
                        {"success": False, "conflict": True, "message": "This team was updated by someone else. Refresh and try again."},
                        status_code=409,
                    )
                team["points"] = data.get("points", team["points"])
                team["name"] = data.get("name", team["name"])
                team["version"] += 1
                save_teams(teams)
                log_scores("team_updated", teams, {"team_id": team_id})
                log_change(f"Updated team {team_id}: {team['name']} now has {team['points']} points")
                return {"success": True, "team": team}
    return JSONResponse({"success": False, "message": "Team not found"}, status_code=404)


@app.delete("/api/teams/{team_id}")
def delete_team(team_id: int):
    with TEAM_WRITE_LOCK:
        teams = load_teams()
        remaining = [team for team in teams if team["id"] != team_id]
        if len(remaining) == len(teams):
            return JSONResponse({"success": False, "message": "Team not found"}, status_code=404)
        deleted = next(team for team in teams if team["id"] == team_id)
        save_teams(remaining)
        log_scores("team_deleted", remaining, {"team_id": team_id, "team_name": deleted["name"]})
        log_change(f"Deleted team {team_id}: {deleted['name']}")
        return {"success": True, "team": deleted}


@app.post("/api/reset")
async def reset_teams(request: Request):
    data = await request.json()
    if data.get("confirm") == "reset":
        teams = default_teams()
        save_teams(teams)
        log_scores("scores_reset", teams)
        log_change("Reset all team scores to zero")
        return {"success": True, "message": "Scores reset successfully"}
    return JSONResponse({"success": False, "message": 'Type "reset" to confirm'}, status_code=400)


@app.post("/api/teams")
async def add_team(request: Request):
    data = await request.json()
    teams = load_teams()
    new_id = max((team["id"] for team in teams), default=0) + 1
    new_team = {"id": new_id, "name": data.get("name", f"Team {new_id}"), "points": 0, "version": 0}
    teams.append(new_team)
    save_teams(teams)
    log_scores("team_added", teams, {"team_id": new_id})
    log_change(f"Added team {new_id}: {new_team['name']}")
    return {"success": True, "team": new_team}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
