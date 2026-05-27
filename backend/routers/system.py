import asyncio
import os
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_active_user, get_current_admin_user
from config import settings
from models import UserResponse

router = APIRouter(prefix="/api/system", tags=["系统版本"])

_restart_requested = False


def _project_root() -> Path:
    return Path(settings.PROJECT_ROOT).resolve()


def _run_git(args: list[str], timeout: int = 20) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=_project_root(),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def _read_version() -> str:
    version_file = Path(settings.APP_VERSION_FILE)
    try:
        return version_file.read_text(encoding="utf-8").strip() or "v0.0.0"
    except Exception:
        return "v0.0.0"


def _running_commit() -> Optional[str]:
    commit = os.getenv("APP_COMMIT")
    if commit and commit != "unknown":
        return commit
    return None


def _running_version() -> str:
    version = os.getenv("APP_VERSION")
    if version:
        return version
    return _read_version()


def _read_remote_version() -> Optional[str]:
    try:
        raw_url = (
            f"{settings.SYSTEM_REPO_URL.rstrip('/').replace('github.com/', 'raw.githubusercontent.com/')}"
            f"/{settings.SYSTEM_REPO_BRANCH}/backend/VERSION"
        )
        with urllib.request.urlopen(raw_url, timeout=10) as response:
            return response.read().decode("utf-8").strip() or None
    except Exception:
        return None


async def _exit_process_later(delay: float = 1.0):
    await asyncio.sleep(delay)
    os._exit(0)


@router.get("/version")
async def get_version(_: UserResponse = Depends(get_current_active_user)):
    local_commit = _run_git(["rev-parse", "HEAD"])
    running_commit = _running_commit() or local_commit
    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or settings.SYSTEM_REPO_BRANCH
    version = _running_version()
    local_version = _read_version()
    remote_version = _read_remote_version()
    remote_commit = _run_git(["ls-remote", settings.SYSTEM_REPO_URL, f"refs/heads/{settings.SYSTEM_REPO_BRANCH}"], timeout=30)

    remote_hash = None
    if remote_commit:
        remote_hash = remote_commit.split()[0]

    has_update = bool(remote_hash and local_commit and remote_hash != local_commit)
    restart_required = bool(local_commit and running_commit and local_commit != running_commit)

    if has_update:
        status = "update_available"
    elif restart_required:
        status = "restart_required"
    else:
        status = "up_to_date"

    return {
        "version": version,
        "local_version": local_version,
        "remote_version": remote_version,
        "status": status,
        "has_update": has_update,
        "restart_required": restart_required,
        "branch": branch,
        "running_commit": running_commit[:7] if running_commit else None,
        "local_commit": local_commit[:7] if local_commit else None,
        "remote_commit": remote_hash[:7] if remote_hash else None,
        "can_update": bool(settings.SYSTEM_UPDATE_COMMAND),
        "checked_at": datetime.now().isoformat(),
    }


@router.post("/update")
async def update_system(_: UserResponse = Depends(get_current_admin_user)):
    command = settings.SYSTEM_UPDATE_COMMAND
    if not command:
        raise HTTPException(status_code=400, detail="未配置 SYSTEM_UPDATE_COMMAND，无法从页面自动更新")

    try:
        subprocess.Popen(command, cwd=_project_root(), shell=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"启动更新失败: {exc}")

    return {"message": "更新任务已启动，完成后请刷新状态"}


@router.post("/restart")
async def restart_system(_: UserResponse = Depends(get_current_admin_user)):
    global _restart_requested
    if _restart_requested:
        return {"message": "重启已在执行中"}

    _restart_requested = True
    asyncio.create_task(_exit_process_later())
    return {"message": "后端即将重启"}
