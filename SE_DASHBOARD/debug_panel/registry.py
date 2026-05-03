"""
registry.py — Debug Panel Function Registry
============================================
Central mapping of module names → function descriptors.

Each function descriptor is a dict with:
  - "description": human-readable summary
  - "params": list of {"name", "type", "default", "help"} dicts
  - "fn": the mock callable (returns realistic dummy data, logs received args)

All implementations are MOCK / DUMMY — they never touch the real server,
database, network, or filesystem. Safe to invoke at any time.

Module groups mirror the two real projects:
  • Server — Auth / Session / Exam Control
  • Protocol — Event Builders
  • Security — Encryption & Signing
  • Process Monitor — Blacklist & Process Scan
  • Incident System — Incident Lifecycle
  • Baris Fork — Legacy API surface from software-enginnering-project
"""

import json
import hashlib
import secrets
import datetime
from typing import Any


# ─────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def _log(fn_name: str, kwargs: dict) -> dict:
    """Return a standard mock envelope with received args logged."""
    return {
        "__mock": True,
        "function": fn_name,
        "received_at": _now(),
        "received_args": kwargs,
    }


# ─────────────────────────────────────────────
#  MODULE: Server — Auth & Login
# ─────────────────────────────────────────────

def _mock_login(login_id: str, password: str) -> dict:
    log = _log("server.login", {"login_id": login_id, "password": "***"})
    if not login_id or not password:
        return {**log, "status": "error", "code": 400, "reason": "login_id and password required"}
    if login_id not in ("student01", "student02", "test_user"):
        return {**log, "status": "error", "code": 403, "reason": "User is not allowed to take this exam."}
    return {**log, "status": "ok", "uuid": "mock-uuid-" + secrets.token_hex(4)}

def _mock_register_user(login_id: str, password: str) -> dict:
    log = _log("server.register_user", {"login_id": login_id})
    uid = "mock-uuid-" + secrets.token_hex(4)
    return {**log, "status": "ok", "uuid": uid, "created": True}

def _mock_ban_user(login_id: str, reason: str) -> dict:
    log = _log("server.ban_user", {"login_id": login_id, "reason": reason})
    return {**log, "status": "ok", "banned": True, "login_id": login_id, "reason": reason, "at": _now()}

def _mock_kick_user(login_id: str, reason: str) -> dict:
    log = _log("server.kick_user", {"login_id": login_id, "reason": reason})
    return {**log, "status": "ok", "kicked": True, "login_id": login_id, "kick_count": 1}


# ─────────────────────────────────────────────
#  MODULE: Server — Session State
# ─────────────────────────────────────────────

def _mock_derive_state(exam_started: bool, exam_finished: bool, admin_paused: bool, banned: bool) -> dict:
    log = _log("session_state.derive_state", locals())
    if banned:
        state = "banned"
    elif exam_started and exam_finished:
        state = "awaiting_submission"
    elif admin_paused:
        state = "admin_paused"
    elif exam_started:
        state = "running"
    else:
        state = "waiting"
    return {**log, "derived_state": state, "display_name": state.replace("_", " ").title()}

def _mock_set_state(login_id: str, new_state: str, reason: str, remaining_seconds: int) -> dict:
    log = _log("session_state.set_state", {"login_id": login_id, "new_state": new_state, "reason": reason, "remaining_seconds": remaining_seconds})
    valid_states = ["waiting", "running", "admin_paused", "disconnected_paused", "violation_paused", "awaiting_submission", "submitted", "banned"]
    if new_state not in valid_states:
        return {**log, "status": "error", "reason": f"Unknown state: {new_state!r}. Valid: {valid_states}"}
    return {**log, "status": "ok", "login_id": login_id, "state": new_state, "reason": reason, "updated_at": _now()}

def _mock_reconnect_resume_allowed(login_id: str, current_state: str, auto_resume_on_reconnect: bool) -> dict:
    log = _log("session_state.reconnect_resume_allowed", locals())
    blocked = {"violation_paused", "awaiting_submission", "submitted", "banned"}
    if current_state in blocked:
        allowed = False
    elif current_state == "disconnected_paused":
        allowed = auto_resume_on_reconnect
    else:
        allowed = True
    return {**log, "resume_allowed": allowed, "current_state": current_state}

def _mock_pause_source(current_state: str) -> dict:
    log = _log("session_state.pause_source", {"current_state": current_state})
    mapping = {"admin_paused": "admin", "disconnected_paused": "disconnect", "violation_paused": "violation"}
    return {**log, "pause_source": mapping.get(current_state, "")}


# ─────────────────────────────────────────────
#  MODULE: Server — Exam Control
# ─────────────────────────────────────────────

def _mock_start_exam(login_id: str, exam_id: str, duration_minutes: int) -> dict:
    log = _log("server.start_exam", {"login_id": login_id, "exam_id": exam_id, "duration_minutes": duration_minutes})
    return {**log, "status": "ok", "exam_phase": "running", "started_at": _now(), "duration_seconds": duration_minutes * 60}

def _mock_add_time(login_id: str, minutes: float) -> dict:
    log = _log("server.add_time", {"login_id": login_id, "minutes": minutes})
    if minutes <= 0:
        return {**log, "status": "error", "reason": "Minutes must be greater than 0"}
    added_seconds = int(minutes * 60)
    return {**log, "status": "ok", "login_id": login_id, "extra_seconds_added": added_seconds, "total_extra_seconds": added_seconds}

def _mock_pause_exam(login_id: str, reason: str) -> dict:
    log = _log("server.pause_exam", {"login_id": login_id, "reason": reason})
    return {**log, "status": "ok", "login_id": login_id, "paused": True, "reason": reason, "at": _now()}

def _mock_resume_exam(login_id: str, reason: str) -> dict:
    log = _log("server.resume_exam", {"login_id": login_id, "reason": reason})
    return {**log, "status": "ok", "login_id": login_id, "resumed": True, "reason": reason, "at": _now()}

def _mock_forgive_violation(login_id: str, incident_id: str, reason: str) -> dict:
    log = _log("server.forgive_violation", {"login_id": login_id, "incident_id": incident_id, "reason": reason})
    return {**log, "status": "ok", "forgiven": True, "login_id": login_id, "incident_id": incident_id, "next_state": "running"}

def _mock_finish_exam_phase(confirm: bool) -> dict:
    log = _log("server.finish_exam_phase", {"confirm": confirm})
    if not confirm:
        return {**log, "status": "aborted", "reason": "confirm was False"}
    return {**log, "status": "ok", "exam_phase": "finished", "finished_at": _now()}

def _mock_exam_config(duration_minutes: int, has_files: bool) -> dict:
    log = _log("server.exam_config", {"duration_minutes": duration_minutes, "has_files": has_files})
    return {**log, "exam_duration_seconds": duration_minutes * 60, "has_files": has_files}


# ─────────────────────────────────────────────
#  MODULE: Protocol — Event Builders
# ─────────────────────────────────────────────

def _mock_build_welcome(client_id: str, server_id: str) -> dict:
    log = _log("events.welcome", {"client_id": client_id, "server_id": server_id})
    payload = json.dumps({"event": "welcome", "data": {"id": client_id, "server_id": server_id}})
    return {**log, "encoded_json": payload, "byte_length": len(payload.encode())}

def _mock_build_sync_time(remaining_seconds: int, timer_state: str, pause_source: str, reason: str) -> dict:
    log = _log("events.sync_time", locals())
    payload = {"event": "sync_time", "data": {"remaining_seconds": remaining_seconds, "timer_state": timer_state}}
    if pause_source: payload["data"]["pause_source"] = pause_source
    if reason: payload["data"]["reason"] = reason
    return {**log, "encoded_json": json.dumps(payload), "valid_timer_states": ["running", "paused", "idle"]}

def _mock_build_session_state(state: str, remaining_seconds: int, resume_allowed: bool, reason: str, policy_version: str) -> dict:
    log = _log("events.session_state", locals())
    payload = {"event": "session_state", "data": {"state": state, "remaining_seconds": remaining_seconds, "resume_allowed": resume_allowed}}
    if reason: payload["data"]["reason"] = reason
    if policy_version: payload["data"]["policy_version"] = policy_version
    return {**log, "encoded_json": json.dumps(payload)}

def _mock_build_pause_exam(remaining_seconds: int, source: str, reason: str) -> dict:
    log = _log("events.pause_exam", locals())
    payload = {"event": "pause_exam", "data": {"remaining_seconds": remaining_seconds, "source": source}}
    if reason: payload["data"]["reason"] = reason
    return {**log, "encoded_json": json.dumps(payload)}

def _mock_build_process_blacklist(entries_csv: str, version: str, usernames_csv: str) -> dict:
    entries = [e.strip() for e in entries_csv.split(",") if e.strip()]
    usernames = [u.strip() for u in usernames_csv.split(",") if u.strip()]
    log = _log("events.process_blacklist", {"entries_count": len(entries), "version": version, "usernames": usernames})
    payload = {"event": "process_blacklist", "data": {"entries": entries, "version": version, "process_usernames": usernames}}
    return {**log, "encoded_json": json.dumps(payload), "entry_count": len(entries)}

def _mock_build_kill_process(pid: int, incident_id: str, process_name: str, reason: str) -> dict:
    log = _log("events.kill_process", locals())
    payload = {"event": "kill_process", "data": {"pid": pid}}
    if incident_id: payload["data"]["incident_id"] = incident_id
    if process_name: payload["data"]["process_name"] = process_name
    if reason: payload["data"]["reason"] = reason
    return {**log, "encoded_json": json.dumps(payload)}

def _mock_build_incident_received(incident_id: str, stored: bool, artifact_path: str) -> dict:
    log = _log("events.incident_received", locals())
    payload = {"event": "incident_received", "data": {"incident_id": incident_id, "stored": stored}}
    if artifact_path: payload["data"]["artifact_path"] = artifact_path
    return {**log, "encoded_json": json.dumps(payload)}


# ─────────────────────────────────────────────
#  MODULE: Security
# ─────────────────────────────────────────────

def _mock_build_session_context(session_uuid: str, password: str) -> dict:
    log = _log("security.build_session_context", {"session_uuid": session_uuid, "password": "***"})
    import hashlib, base64
    signing_key = hashlib.pbkdf2_hmac("sha256", password.encode(), f"signing:{session_uuid}".encode(), 120_000, dklen=32)
    enc_key = base64.urlsafe_b64encode(hashlib.pbkdf2_hmac("sha256", password.encode(), f"encryption:{session_uuid}".encode(), 120_000, dklen=32)).decode()
    return {**log, "session_uuid": session_uuid, "signing_key_hex": signing_key.hex()[:16] + "...", "fernet_key_preview": enc_key[:12] + "...", "encryption_available": True}

def _mock_protect_wire_message(raw_json: str, enable_encryption: bool) -> dict:
    log = _log("security.protect_wire_message", {"raw_length": len(raw_json), "enable_encryption": enable_encryption})
    try:
        parsed = json.loads(raw_json)
        event = parsed.get("event", "unknown")
        secured_events = {"exam_policy", "policy_update", "session_state", "incident_report", "kill_process", "pause_exam", "resume_exam"}
        needs_protection = event in secured_events
    except json.JSONDecodeError:
        return {**log, "status": "error", "reason": "Invalid JSON input"}
    nonce = secrets.token_hex(16)
    ts = _now()
    if needs_protection and enable_encryption:
        envelope = {"_secured": True, "timestamp": ts, "nonce": nonce, "encrypted": True, "ciphertext": "MOCK_CIPHERTEXT_" + secrets.token_hex(8), "signature": secrets.token_hex(32)}
    elif needs_protection:
        import base64
        envelope = {"_secured": True, "timestamp": ts, "nonce": nonce, "encrypted": False, "payload": base64.urlsafe_b64encode(raw_json.encode()).decode(), "signature": secrets.token_hex(32)}
    else:
        envelope = parsed
    return {**log, "event": event, "required_protection": needs_protection, "output_envelope": envelope}

def _mock_decode_wire_message(raw_json: str, has_security_context: bool) -> dict:
    log = _log("security.decode_wire_message", {"raw_length": len(raw_json), "has_security_context": has_security_context})
    try:
        parsed = json.loads(raw_json)
        event = parsed.get("event", "unknown")
        is_secured = parsed.get("_secured", False)
    except json.JSONDecodeError:
        return {**log, "status": "DECODE_ERROR", "reason": "Invalid JSON"}
    if is_secured and not has_security_context:
        return {**log, "status": "DECODE_ERROR", "reason": "Secured message but no security context"}
    return {**log, "status": "ok", "event": event, "data": parsed.get("data", {}), "was_secured": is_secured}

def _mock_derive_key(password: str, session_uuid: str, label: str) -> dict:
    log = _log("security._derive_key", {"password": "***", "session_uuid": session_uuid, "label": label})
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), f"{label}:{session_uuid}".encode(), 120_000, dklen=32)
    return {**log, "derived_key_hex": key.hex(), "key_length_bytes": 32, "algorithm": "PBKDF2-HMAC-SHA256", "iterations": 120_000}


# ─────────────────────────────────────────────
#  MODULE: Process Monitor (Deniz Fork)
# ─────────────────────────────────────────────

def _mock_set_blacklist(entries_csv: str, version: str, usernames_csv: str) -> dict:
    entries = [e.strip() for e in entries_csv.split(",") if e.strip()]
    usernames = [u.strip() for u in usernames_csv.split(",") if u.strip()]
    log = _log("process_monitor.set_blacklist", {"entries_count": len(entries), "version": version})
    return {**log, "status": "ok", "applied": True, "entries": entries, "version": version, "filter_usernames": usernames}

def _mock_scan_processes(include_system: bool, username_filter: str) -> dict:
    log = _log("process_monitor.scan_processes", {"include_system": include_system, "username_filter": username_filter})
    fake_procs = [
        {"pid": 1234, "name": "python.exe", "username": "student01", "memory_mb": 45.2},
        {"pid": 5678, "name": "chrome.exe", "username": "student01", "memory_mb": 210.0},
        {"pid": 9012, "name": "discord.exe", "username": "student01", "memory_mb": 120.5},
        {"pid": 2345, "name": "notepad.exe", "username": "student01", "memory_mb": 5.1},
    ]
    if username_filter:
        fake_procs = [p for p in fake_procs if p["username"] == username_filter]
    if not include_system:
        fake_procs = [p for p in fake_procs if "system" not in p["name"].lower()]
    return {**log, "process_count": len(fake_procs), "processes": fake_procs, "scanned_at": _now()}

def _mock_check_blacklist_matches(process_name: str, entries_csv: str) -> dict:
    entries = [e.strip().lower() for e in entries_csv.split(",") if e.strip()]
    log = _log("process_monitor.check_blacklist_matches", {"process_name": process_name, "entries_count": len(entries)})
    matched = process_name.lower() in entries
    return {**log, "process_name": process_name, "matched": matched, "matched_entry": process_name.lower() if matched else None}

def _mock_kill_pid(pid: int, process_name: str) -> dict:
    log = _log("process_monitor.kill_pid", {"pid": pid, "process_name": process_name})
    if pid <= 0:
        return {**log, "ok": False, "message": "Invalid PID"}
    return {**log, "ok": True, "pid": pid, "process_name": process_name, "message": f"[MOCK] Process {pid} terminated successfully."}


# ─────────────────────────────────────────────
#  MODULE: Incident System (Deniz Fork)
# ─────────────────────────────────────────────

def _mock_open_incident(login_id: str, rule_id: str, severity: str, summary: str, process_name: str) -> dict:
    log = _log("incident_engine.open_incident", locals())
    valid_rules = ["process_blacklist", "focused_window_policy", "rapid_application_switching", "unexpected_process"]
    valid_severities = ["warning", "violation"]
    if rule_id not in valid_rules:
        return {**log, "status": "error", "reason": f"Unknown rule_id. Valid: {valid_rules}"}
    if severity not in valid_severities:
        return {**log, "status": "error", "reason": f"Unknown severity. Valid: {valid_severities}"}
    incident_id = secrets.token_hex(8)
    return {**log, "status": "ok", "incident_id": incident_id, "rule_id": rule_id, "severity": severity, "summary": summary, "login_id": login_id, "opened_at": _now(), "auto_violation_pause": severity == "violation"}

def _mock_resolve_incident(incident_id: str, resolved_by: str, reason: str) -> dict:
    log = _log("incident_engine.resolve_incident", locals())
    if not incident_id:
        return {**log, "status": "error", "reason": "incident_id is required"}
    return {**log, "status": "ok", "incident_id": incident_id, "resolved": True, "resolved_by": resolved_by, "reason": reason, "at": _now()}

def _mock_apply_policy(policy_version: str, rules_json: str) -> dict:
    log = _log("incident_engine.apply_policy", {"policy_version": policy_version, "rules_json_length": len(rules_json)})
    try:
        rules = json.loads(rules_json) if rules_json.strip() else []
        if not isinstance(rules, list):
            raise ValueError("rules must be a JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        return {**log, "ok": False, "reason": f"Policy parse error: {e}"}
    return {**log, "ok": True, "policy_version": policy_version, "rules_applied": len(rules), "applied_at": _now()}


# ─────────────────────────────────────────────
#  MODULE: Baris Fork — Legacy API surface
# ─────────────────────────────────────────────

def _mock_baris_register_exam(exam_id: str, duration_minutes: int, instructor_token: str) -> dict:
    log = _log("baris.register_exam", {"exam_id": exam_id, "duration_minutes": duration_minutes, "token_preview": instructor_token[:8] + "..." if instructor_token else ""})
    if not instructor_token:
        return {**log, "status": "error", "reason": "instructor_token required"}
    return {**log, "action": "register_exam", "exam_id": exam_id, "duration_seconds": duration_minutes * 60, "registered_at": _now()}

def _mock_baris_request_start_exam(student_id: str, exam_id: str, login_id: str, password_hash: str) -> dict:
    log = _log("baris.request_start_exam", {"student_id": student_id, "exam_id": exam_id, "login_id": login_id})
    if not all([student_id, exam_id, login_id, password_hash]):
        return {**log, "status": "error", "reason": "Missing required fields"}
    session_token = secrets.token_hex(16)
    return {**log, "action": "request_start_exam", "status": "ok", "session_token": session_token, "state": "in_progress"}

def _mock_baris_status_update(student_id: str, flags_json: str, risk_score: int) -> dict:
    log = _log("baris.status_update", {"student_id": student_id, "risk_score": risk_score})
    try:
        flags = json.loads(flags_json) if flags_json.strip() else {}
    except json.JSONDecodeError:
        return {**log, "status": "error", "reason": "flags_json must be valid JSON"}
    level = "LOW" if risk_score < 30 else "MEDIUM" if risk_score < 70 else "HIGH"
    return {**log, "action": "status_update", "student_id": student_id, "flags": flags, "total_risk_score": risk_score, "risk_level": level, "logged_at": _now()}

def _mock_baris_resume_student(student_id: str, instructor_token: str) -> dict:
    log = _log("baris.resume_student", {"student_id": student_id})
    if not instructor_token:
        return {**log, "status": "error", "reason": "instructor_token required"}
    return {**log, "action": "resume_student", "student_id": student_id, "new_state": "in_progress", "resumed_at": _now()}

def _mock_baris_school_auth(student_number: str, cats_password: str) -> dict:
    log = _log("baris.school_service.authenticate", {"student_number": student_number, "password": "***"})
    if not student_number.isdigit():
        return {**log, "ok": False, "reason": "student_number must be numeric (CATS eid)"}
    fake_name = "John Mock" if student_number == "12345678" else f"Student {student_number[:4]}***"
    return {**log, "ok": True, "student_number": student_number, "full_name": fake_name, "scrape_source": "CATS/Sakai (mocked)"}

def _mock_baris_payload_builder(active_window: str, banned_process: str, idle_seconds: int, exam_closed: bool) -> dict:
    log = _log("baris.payload_builder.build_flags", locals())
    flags = {}
    if exam_closed:
        flags["EXAM_CLOSED"] = True
    if banned_process:
        flags["BANNED"] = banned_process
    if idle_seconds >= 300:
        flags["IDLE_CRITICAL"] = idle_seconds
    elif idle_seconds >= 60:
        flags["IDLE_WARN"] = idle_seconds
    known_apps = {"exam_app", "python", "java", "vscode", "intellij"}
    if active_window.lower() not in known_apps:
        flags["FOCUS_LOST"] = active_window
    return {**log, "flags": flags, "flag_count": len(flags), "has_violations": bool(flags)}

def _mock_baris_protocol_encode(event: str, data_json: str) -> dict:
    log = _log("baris.protocol.encode", {"event": event})
    try:
        data = json.loads(data_json) if data_json.strip() else {}
    except json.JSONDecodeError:
        return {**log, "status": "error", "reason": "data_json must be valid JSON object"}
    payload = {"event": event, "data": data}
    checksum = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    payload["checksum"] = checksum
    return {**log, "status": "ok", "encoded": json.dumps(payload), "checksum": checksum}


# ─────────────────────────────────────────────
#  REGISTRY DEFINITION
# ─────────────────────────────────────────────

REGISTRY: dict[str, dict[str, Any]] = {

    # ── Server / Auth ──────────────────────────────────────────────────────
    "server.login": {
        "module": "Server — Auth & Login",
        "description": "Authenticate a student with login_id + password and return a session UUID.",
        "params": [
            {"name": "login_id", "type": str, "default": "student01", "help": "Student's login identifier"},
            {"name": "password", "type": str, "default": "pass1234", "help": "Student's plain-text password"},
        ],
        "fn": _mock_login,
    },
    "server.register_user": {
        "module": "Server — Auth & Login",
        "description": "Register a new student account and generate a UUID.",
        "params": [
            {"name": "login_id", "type": str, "default": "new_student", "help": "New student's login ID"},
            {"name": "password", "type": str, "default": "secret", "help": "Initial password"},
        ],
        "fn": _mock_register_user,
    },
    "server.ban_user": {
        "module": "Server — Auth & Login",
        "description": "Permanently ban a student from the exam.",
        "params": [
            {"name": "login_id", "type": str, "default": "student01", "help": "Target login ID"},
            {"name": "reason", "type": str, "default": "Cheating detected", "help": "Ban reason"},
        ],
        "fn": _mock_ban_user,
    },
    "server.kick_user": {
        "module": "Server — Auth & Login",
        "description": "Forcibly disconnect a student (they can reconnect).",
        "params": [
            {"name": "login_id", "type": str, "default": "student01", "help": "Target login ID"},
            {"name": "reason", "type": str, "default": "Admin kick", "help": "Kick reason"},
        ],
        "fn": _mock_kick_user,
    },

    # ── Session State ──────────────────────────────────────────────────────
    "session_state.derive_state": {
        "module": "Server — Session State",
        "description": "Compute the canonical session state from a user record's boolean flags.",
        "params": [
            {"name": "exam_started", "type": bool, "default": False, "help": "Has the student started?"},
            {"name": "exam_finished", "type": bool, "default": False, "help": "Did the exam time expire?"},
            {"name": "admin_paused", "type": bool, "default": False, "help": "Did admin pause this student?"},
            {"name": "banned", "type": bool, "default": False, "help": "Is the student banned?"},
        ],
        "fn": _mock_derive_state,
    },
    "session_state.set_state": {
        "module": "Server — Session State",
        "description": "Transition a student to a new session state with timestamp and synced legacy flags.",
        "params": [
            {"name": "login_id", "type": str, "default": "student01", "help": "Target student"},
            {"name": "new_state", "type": str, "default": "running", "help": "waiting / running / admin_paused / violation_paused / awaiting_submission / submitted / banned"},
            {"name": "reason", "type": str, "default": "Exam started by instructor", "help": "Human-readable reason"},
            {"name": "remaining_seconds", "type": int, "default": 3600, "help": "Remaining exam seconds to snapshot"},
        ],
        "fn": _mock_set_state,
    },
    "session_state.reconnect_resume_allowed": {
        "module": "Server — Session State",
        "description": "Check whether a reconnecting student should be automatically resumed.",
        "params": [
            {"name": "login_id", "type": str, "default": "student01", "help": "Target student"},
            {"name": "current_state", "type": str, "default": "disconnected_paused", "help": "Current session state string"},
            {"name": "auto_resume_on_reconnect", "type": bool, "default": True, "help": "Policy flag from exam_policy.json"},
        ],
        "fn": _mock_reconnect_resume_allowed,
    },
    "session_state.pause_source": {
        "module": "Server — Session State",
        "description": "Return the human-readable pause source label for a given session state.",
        "params": [
            {"name": "current_state", "type": str, "default": "admin_paused", "help": "admin_paused / disconnected_paused / violation_paused / running"},
        ],
        "fn": _mock_pause_source,
    },

    # ── Exam Control ───────────────────────────────────────────────────────
    "server.start_exam": {
        "module": "Server — Exam Control",
        "description": "Start the exam session for a given student.",
        "params": [
            {"name": "login_id", "type": str, "default": "student01", "help": "Target login ID"},
            {"name": "exam_id", "type": str, "default": "CS101-FINAL", "help": "Exam identifier"},
            {"name": "duration_minutes", "type": int, "default": 90, "help": "Exam duration in minutes"},
        ],
        "fn": _mock_start_exam,
    },
    "server.add_time": {
        "module": "Server — Exam Control",
        "description": "Grant extra exam time to a specific student.",
        "params": [
            {"name": "login_id", "type": str, "default": "student01", "help": "Target student"},
            {"name": "minutes", "type": float, "default": 10.0, "help": "Minutes to add (must be > 0)"},
        ],
        "fn": _mock_add_time,
    },
    "server.pause_exam": {
        "module": "Server — Exam Control",
        "description": "Admin-pause an individual student's exam timer.",
        "params": [
            {"name": "login_id", "type": str, "default": "student01", "help": "Target student"},
            {"name": "reason", "type": str, "default": "Suspected violation", "help": "Reason shown to student"},
        ],
        "fn": _mock_pause_exam,
    },
    "server.resume_exam": {
        "module": "Server — Exam Control",
        "description": "Resume a previously admin-paused or disconnected student.",
        "params": [
            {"name": "login_id", "type": str, "default": "student01", "help": "Target student"},
            {"name": "reason", "type": str, "default": "Issue resolved", "help": "Reason shown to student"},
        ],
        "fn": _mock_resume_exam,
    },
    "server.forgive_violation": {
        "module": "Server — Exam Control",
        "description": "Forgive a violation-paused student and move them back to running.",
        "params": [
            {"name": "login_id", "type": str, "default": "student01", "help": "Target student"},
            {"name": "incident_id", "type": str, "default": "", "help": "Optional: incident ID to forgive"},
            {"name": "reason", "type": str, "default": "Reviewed and cleared", "help": "Forgiveness reason"},
        ],
        "fn": _mock_forgive_violation,
    },
    "server.finish_exam_phase": {
        "module": "Server — Exam Control",
        "description": "Transition the server's exam phase to 'finished' (no new logins accepted).",
        "params": [
            {"name": "confirm", "type": bool, "default": True, "help": "Must be True to proceed"},
        ],
        "fn": _mock_finish_exam_phase,
    },
    "server.exam_config": {
        "module": "Server — Exam Control",
        "description": "Return the current exam configuration (duration, file availability).",
        "params": [
            {"name": "duration_minutes", "type": int, "default": 90, "help": "Exam duration in minutes"},
            {"name": "has_files", "type": bool, "default": True, "help": "Whether exam files are available for download"},
        ],
        "fn": _mock_exam_config,
    },

    # ── Protocol / Event Builders ──────────────────────────────────────────
    "events.welcome": {
        "module": "Protocol — Event Builders",
        "description": "Build the 'welcome' message sent to a newly connected client.",
        "params": [
            {"name": "client_id", "type": str, "default": "mock-uuid-1234", "help": "Client's session UUID"},
            {"name": "server_id", "type": str, "default": "EXAM-SERVER-01", "help": "Server's identifier"},
        ],
        "fn": _mock_build_welcome,
    },
    "events.sync_time": {
        "module": "Protocol — Event Builders",
        "description": "Build a sync_time message that updates the client's remaining countdown.",
        "params": [
            {"name": "remaining_seconds", "type": int, "default": 3600, "help": "Seconds left in the exam"},
            {"name": "timer_state", "type": str, "default": "running", "help": "running / paused / idle"},
            {"name": "pause_source", "type": str, "default": "", "help": "admin / disconnect / violation (optional)"},
            {"name": "reason", "type": str, "default": "", "help": "Optional label shown to student"},
        ],
        "fn": _mock_build_sync_time,
    },
    "events.session_state": {
        "module": "Protocol — Event Builders",
        "description": "Build the authoritative session_state message for connect/reconnect flow.",
        "params": [
            {"name": "state", "type": str, "default": "running", "help": "Session state string"},
            {"name": "remaining_seconds", "type": int, "default": 3600, "help": "Remaining seconds"},
            {"name": "resume_allowed", "type": bool, "default": True, "help": "Whether reconnect-resume is permitted"},
            {"name": "reason", "type": str, "default": "", "help": "Optional detail"},
            {"name": "policy_version", "type": str, "default": "abc123", "help": "Applied policy hash"},
        ],
        "fn": _mock_build_session_state,
    },
    "events.pause_exam": {
        "module": "Protocol — Event Builders",
        "description": "Build a pause_exam event sent by the server to freeze a client's timer.",
        "params": [
            {"name": "remaining_seconds", "type": int, "default": 1800, "help": "Remaining seconds at pause"},
            {"name": "source", "type": str, "default": "admin", "help": "admin / violation / disconnect"},
            {"name": "reason", "type": str, "default": "Suspected violation", "help": "Human-readable reason"},
        ],
        "fn": _mock_build_pause_exam,
    },
    "events.process_blacklist": {
        "module": "Protocol — Event Builders",
        "description": "Build a process_blacklist push event sent from server to client.",
        "params": [
            {"name": "entries_csv", "type": str, "default": "discord.exe, steam.exe, cheattool.exe", "help": "Comma-separated process names"},
            {"name": "version", "type": str, "default": "v1.0", "help": "Blacklist version stamp"},
            {"name": "usernames_csv", "type": str, "default": "", "help": "Optional: only scan these OS usernames"},
        ],
        "fn": _mock_build_process_blacklist,
    },
    "events.kill_process": {
        "module": "Protocol — Event Builders",
        "description": "Build a kill_process command sent from server to client targeting a specific PID.",
        "params": [
            {"name": "pid", "type": int, "default": 1234, "help": "Target process ID"},
            {"name": "incident_id", "type": str, "default": "", "help": "Related incident ID (optional)"},
            {"name": "process_name", "type": str, "default": "discord.exe", "help": "Process name (for logging)"},
            {"name": "reason", "type": str, "default": "Blacklisted process", "help": "Kill reason"},
        ],
        "fn": _mock_build_kill_process,
    },
    "events.incident_received": {
        "module": "Protocol — Event Builders",
        "description": "Build the server's acknowledgement of a client-reported incident.",
        "params": [
            {"name": "incident_id", "type": str, "default": "inc-abc123", "help": "Incident UUID"},
            {"name": "stored", "type": bool, "default": True, "help": "Whether incident was persisted"},
            {"name": "artifact_path", "type": str, "default": "", "help": "Path to associated artifact (optional)"},
        ],
        "fn": _mock_build_incident_received,
    },

    # ── Security ───────────────────────────────────────────────────────────
    "security.build_session_context": {
        "module": "Security",
        "description": "Derive PBKDF2 signing and Fernet encryption keys for a session.",
        "params": [
            {"name": "session_uuid", "type": str, "default": "mock-uuid-1234abcd", "help": "The client's session UUID"},
            {"name": "password", "type": str, "default": "exam_password", "help": "Student password used to derive keys"},
        ],
        "fn": _mock_build_session_context,
    },
    "security.protect_wire_message": {
        "module": "Security",
        "description": "Wrap a raw JSON message with HMAC signature (and optionally Fernet encryption).",
        "params": [
            {"name": "raw_json", "type": str, "default": '{"event":"session_state","data":{"state":"running"}}', "help": "Raw JSON message string"},
            {"name": "enable_encryption", "type": bool, "default": True, "help": "Use Fernet encryption for sensitive events"},
        ],
        "fn": _mock_protect_wire_message,
    },
    "security.decode_wire_message": {
        "module": "Security",
        "description": "Decode and verify a (potentially secured) incoming wire message.",
        "params": [
            {"name": "raw_json", "type": str, "default": '{"event":"ping","data":{"message":"hello"}}', "help": "Raw wire message string"},
            {"name": "has_security_context", "type": bool, "default": True, "help": "Whether a session security context is available"},
        ],
        "fn": _mock_decode_wire_message,
    },
    "security.derive_key": {
        "module": "Security",
        "description": "Run PBKDF2-HMAC-SHA256 key derivation for a given label (signing or encryption).",
        "params": [
            {"name": "password", "type": str, "default": "student_password", "help": "Password to derive from"},
            {"name": "session_uuid", "type": str, "default": "mock-uuid-1234abcd", "help": "Session UUID (used as salt prefix)"},
            {"name": "label", "type": str, "default": "signing", "help": "signing / encryption"},
        ],
        "fn": _mock_derive_key,
    },

    # ── Process Monitor ────────────────────────────────────────────────────
    "process_monitor.set_blacklist": {
        "module": "Process Monitor",
        "description": "Apply a new process blacklist to the client-side process monitor.",
        "params": [
            {"name": "entries_csv", "type": str, "default": "discord.exe, steam.exe", "help": "Comma-separated banned process names"},
            {"name": "version", "type": str, "default": "1.0", "help": "Blacklist version string"},
            {"name": "usernames_csv", "type": str, "default": "", "help": "Optional: filter to these OS usernames only"},
        ],
        "fn": _mock_set_blacklist,
    },
    "process_monitor.scan_processes": {
        "module": "Process Monitor",
        "description": "Perform a live scan of running processes on the student's machine.",
        "params": [
            {"name": "include_system", "type": bool, "default": False, "help": "Include system/kernel processes"},
            {"name": "username_filter", "type": str, "default": "", "help": "Only return processes for this OS user (blank = all)"},
        ],
        "fn": _mock_scan_processes,
    },
    "process_monitor.check_blacklist_matches": {
        "module": "Process Monitor",
        "description": "Check whether a given process name matches any blacklist entry.",
        "params": [
            {"name": "process_name", "type": str, "default": "discord.exe", "help": "Process name to check"},
            {"name": "entries_csv", "type": str, "default": "discord.exe, steam.exe, cheattool.exe", "help": "Current blacklist entries (comma-separated)"},
        ],
        "fn": _mock_check_blacklist_matches,
    },
    "process_monitor.kill_pid": {
        "module": "Process Monitor",
        "description": "Attempt to terminate a process by PID on the client machine.",
        "params": [
            {"name": "pid", "type": int, "default": 1234, "help": "Process ID to terminate"},
            {"name": "process_name", "type": str, "default": "discord.exe", "help": "Process name (for logging)"},
        ],
        "fn": _mock_kill_pid,
    },

    # ── Incident System ────────────────────────────────────────────────────
    "incident_engine.open_incident": {
        "module": "Incident System",
        "description": "Open a new incident (violation or warning) for a student.",
        "params": [
            {"name": "login_id", "type": str, "default": "student01", "help": "Affected student"},
            {"name": "rule_id", "type": str, "default": "process_blacklist", "help": "process_blacklist / focused_window_policy / rapid_application_switching / unexpected_process"},
            {"name": "severity", "type": str, "default": "violation", "help": "warning / violation"},
            {"name": "summary", "type": str, "default": "discord.exe detected", "help": "Human-readable description"},
            {"name": "process_name", "type": str, "default": "discord.exe", "help": "Offending process (optional)"},
        ],
        "fn": _mock_open_incident,
    },
    "incident_engine.resolve_incident": {
        "module": "Incident System",
        "description": "Mark an open incident as resolved.",
        "params": [
            {"name": "incident_id", "type": str, "default": "inc-abc123", "help": "Incident to resolve"},
            {"name": "resolved_by", "type": str, "default": "admin", "help": "Who resolved (admin / system)"},
            {"name": "reason", "type": str, "default": "Process no longer running", "help": "Resolution reason"},
        ],
        "fn": _mock_resolve_incident,
    },
    "incident_engine.apply_policy": {
        "module": "Incident System",
        "description": "Apply a versioned exam policy to the client-side incident engine.",
        "params": [
            {"name": "policy_version", "type": str, "default": "abc123", "help": "Policy SHA-256 hash"},
            {"name": "rules_json", "type": str, "default": '[{"rule_id":"process_blacklist","enabled":true,"severity":"violation"}]', "help": "JSON array of rule configs"},
        ],
        "fn": _mock_apply_policy,
    },

    # ── Baris Fork ─────────────────────────────────────────────────────────
    "baris.register_exam": {
        "module": "Baris Fork — Legacy API",
        "description": "[Baris fork] Register an exam session on the server (requires instructor token).",
        "params": [
            {"name": "exam_id", "type": str, "default": "CS101-MIDTERM", "help": "Exam identifier"},
            {"name": "duration_minutes", "type": int, "default": 90, "help": "Exam duration in minutes"},
            {"name": "instructor_token", "type": str, "default": "tok_abc123", "help": "RBAC instructor token"},
        ],
        "fn": _mock_baris_register_exam,
    },
    "baris.request_start_exam": {
        "module": "Baris Fork — Legacy API",
        "description": "[Baris fork] Student requests to begin their exam (joins the session).",
        "params": [
            {"name": "student_id", "type": str, "default": "STU001", "help": "Student identifier"},
            {"name": "exam_id", "type": str, "default": "CS101-MIDTERM", "help": "Target exam ID"},
            {"name": "login_id", "type": str, "default": "student01", "help": "Login ID"},
            {"name": "password_hash", "type": str, "default": "sha256hash_here", "help": "SHA-256 hash of password"},
        ],
        "fn": _mock_baris_request_start_exam,
    },
    "baris.status_update": {
        "module": "Baris Fork — Legacy API",
        "description": "[Baris fork] Student client pushes activity flags and risk score to server.",
        "params": [
            {"name": "student_id", "type": str, "default": "STU001", "help": "Student identifier"},
            {"name": "flags_json", "type": str, "default": '{"FOCUS_LOST":"discord.exe"}', "help": "JSON dict of violation flags"},
            {"name": "risk_score", "type": int, "default": 25, "help": "Cumulative risk score (0-100+)"},
        ],
        "fn": _mock_baris_status_update,
    },
    "baris.resume_student": {
        "module": "Baris Fork — Legacy API",
        "description": "[Baris fork] Instructor resumes a paused student (violation / disconnected).",
        "params": [
            {"name": "student_id", "type": str, "default": "STU001", "help": "Student to resume"},
            {"name": "instructor_token", "type": str, "default": "tok_abc123", "help": "Instructor RBAC token"},
        ],
        "fn": _mock_baris_resume_student,
    },
    "baris.school_service.authenticate": {
        "module": "Baris Fork — Legacy API",
        "description": "[Baris fork] Authenticate a student against the CATS/Sakai LMS via web scraping.",
        "params": [
            {"name": "student_number", "type": str, "default": "12345678", "help": "University student number (eid)"},
            {"name": "cats_password", "type": str, "default": "university_pass", "help": "CATS portal password"},
        ],
        "fn": _mock_baris_school_auth,
    },
    "baris.payload_builder": {
        "module": "Baris Fork — Legacy API",
        "description": "[Baris fork] Build violation flags from activity monitor data.",
        "params": [
            {"name": "active_window", "type": str, "default": "discord", "help": "Currently focused window/process name"},
            {"name": "banned_process", "type": str, "default": "", "help": "Detected banned process name (blank = none)"},
            {"name": "idle_seconds", "type": int, "default": 0, "help": "Seconds student has been idle"},
            {"name": "exam_closed", "type": bool, "default": False, "help": "Whether the exam window is closed"},
        ],
        "fn": _mock_baris_payload_builder,
    },
    "baris.protocol.encode": {
        "module": "Baris Fork — Legacy API",
        "description": "[Baris fork] Encode an event + data dict into a checksum-signed JSON wire message.",
        "params": [
            {"name": "event", "type": str, "default": "PROCESS_CATCH", "help": "Event name constant"},
            {"name": "data_json", "type": str, "default": '{"matches":["discord.exe"],"pid":1234}', "help": "JSON object of event data"},
        ],
        "fn": _mock_baris_protocol_encode,
    },
}
