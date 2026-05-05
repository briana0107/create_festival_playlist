import threading
import time
import uuid


_jobs = {}
_lock = threading.Lock()
_JOB_TTL_SECONDS = 60 * 60


def create_job(total_count):
    _cleanup_old_jobs()
    job_id = uuid.uuid4().hex
    now = time.time()
    job = {
        "job_id": job_id,
        "status": "queued",
        "total_count": total_count,
        "processed_count": 0,
        "added_count": 0,
        "failed_count": 0,
        "playlist_id": "",
        "playlist_url": "",
        "failed": [],
        "error": "",
        "created_at": now,
        "started_at": None,
        "completed_at": None,
    }
    with _lock:
        _jobs[job_id] = job
    return _snapshot(job)


def update_job(job_id, **updates):
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return None
        job.update(updates)
        return _snapshot(job)


def get_job(job_id):
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return None
        return _snapshot(job)


def _snapshot(job):
    data = dict(job)
    started_at = data.get("started_at")
    ended_at = data.get("completed_at") or time.time()
    data["elapsed_seconds"] = int(ended_at - started_at) if started_at else 0
    return data


def _cleanup_old_jobs():
    cutoff = time.time() - _JOB_TTL_SECONDS
    with _lock:
        expired = [
            job_id
            for job_id, job in _jobs.items()
            if (job.get("completed_at") or job.get("created_at") or 0) < cutoff
        ]
        for job_id in expired:
            _jobs.pop(job_id, None)
