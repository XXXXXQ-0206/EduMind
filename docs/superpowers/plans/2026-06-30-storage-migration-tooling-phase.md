# Storage Migration Tooling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a safe, repeatable migration script for moving legacy local JSON state and local artifact files into the configured KV/ObjectStore adapters.

**Architecture:** The script reads legacy files from a source storage directory and writes to the currently configured adapters only when `--write` is provided. It restores known EduMind KV keys from sanitized JSON filenames, and migrates artifact files from known object directories using their storage-relative paths.

**Tech Stack:** asyncio, existing `JsonFileKeyValueStore`, `create_kv_store`, `create_object_store`, pytest.

---

## File Structure

- Create `scripts/migrate_storage_to_adapters.py`: migration CLI and reusable scanning/key-restore helpers.
- Modify `tests/backend/test_infrastructure_adapters.py`: tests for key restoration, KV scanning, and object scanning.
- Modify `docs/architecture/backend-service-boundaries.md`: document the migration command and dry-run behavior.
- Test with backend pytest, compileall, and Compose config validation.

---

### Task 1: Migration CLI

**Files:**
- Create: `scripts/migrate_storage_to_adapters.py`

- [x] **Step 1: Add key restoration**

```python
restore_legacy_kv_key("note_abc_payload") == "note:abc:payload"
restore_legacy_kv_key("files_teacher_user_2") == "files_teacher:user:2"
```

- [x] **Step 2: Add scanning helpers**

```python
iter_legacy_kv_files(source_dir)
iter_legacy_object_files(source_dir)
```

- [x] **Step 3: Add dry-run-first CLI**

```powershell
python scripts/migrate_storage_to_adapters.py --source-dir storage
python scripts/migrate_storage_to_adapters.py --source-dir storage --write
```

---

### Task 2: Tests

**Files:**
- Modify: `tests/backend/test_infrastructure_adapters.py`

- [x] **Step 1: Test key restoration**

Cover `note`, `podcast`, `files`, `planner`, `debate`, and `flashcard_deck` key shapes.

- [x] **Step 2: Test scanners**

Use a temporary storage directory and verify root JSON files are KV items while files under `uploads/` are object items.

---

### Task 3: Docs And Verification

**Files:**
- Modify: `docs/architecture/backend-service-boundaries.md`

- [x] **Step 1: Document migration command**

Mention dry-run default and `--write` requirement.

- [x] **Step 2: Verify**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend -q
.\.venv\Scripts\python.exe -m compileall backend\core backend\infrastructure backend\utils backend\api\routes backend\worker_app.py scripts tests\backend
```

From `C:\Users\熊骞\Desktop\EduMind`, run:

```powershell
docker compose config --quiet
```
