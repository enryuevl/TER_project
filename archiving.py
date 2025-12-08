import os
import shutil
import zipfile
import pickle
from typing import Optional

import db
import utils


BASE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "MyWork")
SCAN_ROOT = os.path.join(BASE_DIR, "Scan")
SUMMARY_ROOT = os.path.join(BASE_DIR, "Summaries")
ARCHIVE_ROOT = os.path.join(BASE_DIR, "Archive")


def _ensure_archive_root() -> str:
    os.makedirs(ARCHIVE_ROOT, exist_ok=True)
    return ARCHIVE_ROOT


def _get_department_name(dept_id: int) -> str:
    try:
        with db.connect() as conn:
            row = conn.execute("SELECT name FROM departments WHERE id=?", (dept_id,)).fetchone()
        return row[0] if row else f"Dept{dept_id}"
    except Exception:
        return f"Dept{dept_id}"


def _copy_scans(dept_name: str, ay: str, sem: str, dest_root: str):
    active_scan_root = os.path.join(SCAN_ROOT, dept_name, ay, sem)
    if os.path.exists(active_scan_root):
        shutil.copytree(active_scan_root, os.path.join(dest_root, "scans"), dirs_exist_ok=True)


def _copy_summaries(ay: str, sem: str, dest_root: str):
    dest = os.path.join(dest_root, "summaries")
    os.makedirs(dest, exist_ok=True)
    if not os.path.exists(SUMMARY_ROOT):
        return

    for root, _dirs, files in os.walk(SUMMARY_ROOT):
        for fname in files:
            if ay in fname and sem in fname:
                src = os.path.join(root, fname)
                shutil.copy2(src, os.path.join(dest, fname))


def _snapshot_results(dest_root: str):
    db_path = db.get_default_db_path()
    pkl_path = os.path.join(os.path.dirname(db_path), db.PKL_FILENAME)
    if not os.path.exists(pkl_path):
        return
    try:
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)
        processed_results = data.get("results", data)
        out_path = os.path.join(dest_root, "results.pkl")
        with open(out_path, "wb") as f:
            pickle.dump({"results": processed_results}, f)
    except Exception:
        # fail silently; archive will still be created
        pass


def _zip_archive(folder: str, zip_name: str) -> str:
    zip_path = os.path.join(folder, zip_name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(folder):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, folder)
                if full == zip_path:
                    continue
                zf.write(full, rel)
    return zip_path


def create_archive_for_semester(
    department_id: int,
    academic_year: str,
    semester: str,
    created_by: str,
    notes: Optional[str] = None,
) -> tuple[str, str]:
    """
    Create a read-only archive bundle for a Department + AY + Sem.
    Returns (zip_path, archive_sem_root).
    """
    _ensure_archive_root()

    # prevent duplicates
    existing = db.get_archive_if_exists(department_id, academic_year, semester)
    if existing:
        raise RuntimeError("This semester is already archived.")

    dept_name = _get_department_name(department_id)
    archive_sem_root = os.path.join(ARCHIVE_ROOT, dept_name, academic_year, semester)
    os.makedirs(archive_sem_root, exist_ok=True)

    _copy_scans(dept_name, academic_year, semester, archive_sem_root)
    _copy_summaries(academic_year, semester, archive_sem_root)
    _snapshot_results(archive_sem_root)

    zip_name = f"TER_{dept_name}_{academic_year}_{semester}.zip"
    zip_path = _zip_archive(archive_sem_root, zip_name)

    db.insert_archive_record(
        department_id=department_id,
        academic_year=academic_year,
        semester=semester,
        archive_path=zip_path,
        created_by=created_by or "Unknown",
        notes=notes,
    )

    try:
        user = utils.get_current_user()
        db.log_activity(
            action="archive_created",
            actor_name=user.get("name"),
            actor_role=user.get("role"),
            department_id=department_id,
            details={
                "academic_year": academic_year,
                "semester": semester,
                "archive_path": zip_path,
            },
        )
    except Exception:
        pass

    return zip_path, archive_sem_root

