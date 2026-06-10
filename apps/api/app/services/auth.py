from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
import os
import secrets
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.database import connect, get_database_backend, initialize_database, sql_placeholder
from app.core.config import get_settings
from app.core.safe_data import safe_dict, safe_json_value
from app.schemas.auth import (
    AuthAuditEvent,
    AuthSessionPublic,
    AuthenticatedUser,
    ControlCenterRole,
    LoginRequest,
    LoginResponse,
    SessionRevokeRequest,
    SessionStatus,
    UserPublic,
    UserStatus,
)

USERS_TABLE = "control_center_users"
SESSIONS_TABLE = "control_center_sessions"
SESSION_AUDIT_TABLE = "control_center_session_audit"
PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 260000
SESSION_TTL_HOURS = 12
REMEMBER_SESSION_TTL_DAYS = 30
TOKEN_PREFIX = "ccs_"
ADMIN_BOOTSTRAP_FINGERPRINT_KEY = "control_center_admin_bootstrap_fingerprint"


def utc_now_datetime() -> datetime:
    return datetime.now(UTC)


def utc_now() -> str:
    return utc_now_datetime().isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def normalize_email(email: str) -> str:
    return " ".join(str(email or "").strip().lower().split())


def normalize_role(role: str | ControlCenterRole) -> ControlCenterRole:
    value = str(role.value if isinstance(role, ControlCenterRole) else role).strip().upper()
    return ControlCenterRole(value)


def governance_role(role: str | ControlCenterRole) -> str:
    return normalize_role(role).value.lower()


def hash_password(password: str, salt_hex: str | None = None) -> str:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = password_hash.split("$", 3)
        if algorithm != PASSWORD_ALGORITHM:
            return False
        expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(expected.hex(), digest_hex)
    except Exception:
        return False


def new_session_token() -> str:
    return f"{TOKEN_PREFIX}{secrets.token_urlsafe(40)}"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def admin_bootstrap_fingerprint(email: str, password: str, name: str) -> str:
    raw = f"{email}\n{name}\n{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def row_to_user(row: dict) -> UserPublic:
    return UserPublic(
        id=row["id"],
        email=row["email"],
        name=row["name"],
        role=normalize_role(row["role"]),
        status=UserStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_login_at=row.get("last_login_at"),
    )


def row_to_session(row: dict) -> AuthSessionPublic:
    session_status = SessionStatus.active
    if row.get("revoked_at"):
        session_status = SessionStatus.revoked
    elif parse_timestamp(row["expires_at"]) <= utc_now_datetime():
        session_status = SessionStatus.expired
    return AuthSessionPublic(
        id=row["id"],
        user_id=row["user_id"],
        status=session_status,
        created_at=row["created_at"],
        expires_at=row["expires_at"],
        revoked_at=row.get("revoked_at"),
        last_seen_at=row.get("last_seen_at"),
        ip_address=row.get("ip_address"),
        user_agent=row.get("user_agent"),
    )


def ensure_auth_schema() -> None:
    initialize_database()
    placeholder = sql_placeholder()
    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {USERS_TABLE} (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_login_at TEXT
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {SESSIONS_TABLE} (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,
                last_seen_at TEXT,
                ip_address TEXT,
                user_agent TEXT
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {SESSION_AUDIT_TABLE} (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                email TEXT,
                role TEXT,
                session_id TEXT,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                result TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        connection.commit()

    bootstrap_initial_admin(placeholder)


def bootstrap_initial_admin(placeholder: str | None = None) -> UserPublic | None:
    email = normalize_email(os.environ.get("CONTROL_CENTER_ADMIN_EMAIL", ""))
    password = os.environ.get("CONTROL_CENTER_ADMIN_PASSWORD", "")
    name = " ".join(os.environ.get("CONTROL_CENTER_ADMIN_NAME", "").strip().split())
    if not email or not password or not name:
        return None

    placeholder = placeholder or sql_placeholder()
    fingerprint = admin_bootstrap_fingerprint(email, password, name)
    now = utc_now()
    with connect() as connection:
        row = connection.execute(f"SELECT * FROM {USERS_TABLE} WHERE email = {placeholder}", (email,)).fetchone()
        if row:
            metadata_row = connection.execute(
                "SELECT value FROM platform_metadata WHERE key = {placeholder}".format(placeholder=placeholder),
                (ADMIN_BOOTSTRAP_FINGERPRINT_KEY,),
            ).fetchone()
            existing_fingerprint = metadata_row["value"] if metadata_row else None
            if existing_fingerprint == fingerprint:
                return row_to_user(dict(row))

            connection.execute(
                f"""
                UPDATE {USERS_TABLE}
                SET name = {placeholder},
                    role = {placeholder},
                    status = {placeholder},
                    password_hash = {placeholder},
                    updated_at = {placeholder}
                WHERE email = {placeholder}
                """,
                (
                    name,
                    ControlCenterRole.ceo.value,
                    UserStatus.active.value,
                    hash_password(password),
                    now,
                    email,
                ),
            )
            connection.execute(
                """
                INSERT INTO platform_metadata (key, value)
                VALUES ({placeholder}, {placeholder})
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """.format(placeholder=placeholder),
                (ADMIN_BOOTSTRAP_FINGERPRINT_KEY, fingerprint),
            )
            connection.commit()
            updated = connection.execute(f"SELECT * FROM {USERS_TABLE} WHERE email = {placeholder}", (email,)).fetchone()
            user = row_to_user(dict(updated))
            audit_auth_event(
                user_id=user.id,
                email=email,
                role=ControlCenterRole.ceo.value,
                session_id=None,
                action="admin.bootstrap",
                resource="control_center",
                result="updated",
                metadata={"source": "CONTROL_CENTER_ADMIN_*"},
            )
            return user

        user = {
            "id": f"user-{uuid4()}",
            "email": email,
            "name": name,
            "role": ControlCenterRole.ceo.value,
            "status": UserStatus.active.value,
            "password_hash": hash_password(password),
            "created_at": now,
            "updated_at": now,
            "last_login_at": None,
        }
        connection.execute(
            f"""
            INSERT INTO {USERS_TABLE}
                (id, email, name, role, status, password_hash, created_at, updated_at, last_login_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                user["id"],
                user["email"],
                user["name"],
                user["role"],
                user["status"],
                user["password_hash"],
                user["created_at"],
                user["updated_at"],
                user["last_login_at"],
            ),
        )
        connection.execute(
            """
            INSERT INTO platform_metadata (key, value)
            VALUES ({placeholder}, {placeholder})
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """.format(placeholder=placeholder),
            (ADMIN_BOOTSTRAP_FINGERPRINT_KEY, fingerprint),
        )
        connection.commit()
    audit_auth_event(
        user_id=user["id"],
        email=email,
        role=ControlCenterRole.ceo.value,
        session_id=None,
        action="admin.bootstrap",
        resource="control_center",
        result="created",
        metadata={"source": "CONTROL_CENTER_ADMIN_*"},
    )
    return UserPublic(**{key: user[key] for key in ["id", "email", "name", "role", "status", "created_at", "updated_at", "last_login_at"]})


def create_user_for_tests(email: str, password: str, name: str, role: ControlCenterRole) -> UserPublic:
    ensure_auth_schema()
    placeholder = sql_placeholder()
    now = utc_now()
    normalized_email = normalize_email(email)
    user = {
        "id": f"user-{uuid4()}",
        "email": normalized_email,
        "name": name,
        "role": normalize_role(role).value,
        "status": UserStatus.active.value,
        "password_hash": hash_password(password),
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }
    with connect() as connection:
        connection.execute(f"DELETE FROM {USERS_TABLE} WHERE email = {placeholder}", (normalized_email,))
        connection.execute(
            f"""
            INSERT INTO {USERS_TABLE}
                (id, email, name, role, status, password_hash, created_at, updated_at, last_login_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                user["id"],
                user["email"],
                user["name"],
                user["role"],
                user["status"],
                user["password_hash"],
                user["created_at"],
                user["updated_at"],
                user["last_login_at"],
            ),
        )
        connection.commit()
    return UserPublic(**{key: user[key] for key in ["id", "email", "name", "role", "status", "created_at", "updated_at", "last_login_at"]})


def audit_auth_event(
    *,
    user_id: str | None,
    email: str | None,
    role: str | None,
    session_id: str | None,
    action: str,
    resource: str,
    result: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
) -> AuthAuditEvent | None:
    try:
        placeholder = sql_placeholder()
        event = AuthAuditEvent(
            id=f"auth-audit-{uuid4()}",
            user_id=user_id,
            email=email,
            role=role,
            session_id=session_id,
            action=action,
            resource=resource,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=utc_now(),
            metadata=metadata or {},
        )
        with connect() as connection:
            connection.execute(
                f"""
                INSERT INTO {SESSION_AUDIT_TABLE}
                    (id, user_id, email, role, session_id, action, resource, result, ip_address, user_agent, timestamp, metadata_json)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                """,
                (
                    event.id,
                    event.user_id,
                    event.email,
                    event.role,
                    event.session_id,
                    event.action,
                    event.resource,
                    event.result,
                    event.ip_address,
                    event.user_agent,
                    event.timestamp,
                    json.dumps(event.metadata, ensure_ascii=False),
                ),
            )
            connection.commit()
        return event
    except Exception:
        return None


def client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else None


def user_agent(request: Request | None) -> str | None:
    return request.headers.get("user-agent") if request is not None else None


def login(request_data: LoginRequest, request: Request | None = None) -> LoginResponse:
    ensure_auth_schema()
    email = normalize_email(request_data.email)
    placeholder = sql_placeholder()
    ip_address = client_ip(request)
    ua = user_agent(request)
    with connect() as connection:
        row = connection.execute(f"SELECT * FROM {USERS_TABLE} WHERE email = {placeholder}", (email,)).fetchone()
        if row is None:
            audit_auth_event(
                user_id=None,
                email=email,
                role=None,
                session_id=None,
                action="auth.login",
                resource="control_center",
                result="denied_unknown_user",
                ip_address=ip_address,
                user_agent=ua,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "invalid_credentials"})
        user_row = dict(row)
        if user_row["status"] != UserStatus.active.value or not verify_password(request_data.password, user_row["password_hash"]):
            audit_auth_event(
                user_id=user_row["id"],
                email=email,
                role=user_row["role"],
                session_id=None,
                action="auth.login",
                resource="control_center",
                result="denied_invalid_credentials",
                ip_address=ip_address,
                user_agent=ua,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "invalid_credentials"})

        token = new_session_token()
        now = utc_now()
        remember_me = bool(request_data.remember_me)
        session_ttl = timedelta(days=REMEMBER_SESSION_TTL_DAYS) if remember_me else timedelta(hours=SESSION_TTL_HOURS)
        expires_at = (utc_now_datetime() + session_ttl).isoformat().replace("+00:00", "Z")
        session_id = f"session-{uuid4()}"
        connection.execute(
            f"""
            INSERT INTO {SESSIONS_TABLE}
                (id, user_id, token_hash, created_at, expires_at, revoked_at, last_seen_at, ip_address, user_agent)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, NULL, {placeholder}, {placeholder}, {placeholder})
            """,
            (session_id, user_row["id"], hash_token(token), now, expires_at, now, ip_address, ua),
        )
        connection.execute(
            f"UPDATE {USERS_TABLE} SET last_login_at = {placeholder}, updated_at = {placeholder} WHERE id = {placeholder}",
            (now, now, user_row["id"]),
        )
        connection.commit()

    user_row["last_login_at"] = now
    user = row_to_user(user_row)
    session = AuthSessionPublic(
        id=session_id,
        user_id=user.id,
        status=SessionStatus.active,
        created_at=now,
        expires_at=expires_at,
        last_seen_at=now,
        ip_address=ip_address,
        user_agent=ua,
    )
    audit_auth_event(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        session_id=session.id,
        action="auth.login",
        resource="control_center",
        result="success",
        ip_address=ip_address,
        user_agent=ua,
        metadata={
            "remember_me": remember_me,
            "session_ttl_hours": REMEMBER_SESSION_TTL_DAYS * 24 if remember_me else SESSION_TTL_HOURS,
        },
    )
    return LoginResponse(token=token, expires_at=expires_at, user=user, session=session)


def session_from_token(token: str, *, touch: bool = True) -> tuple[UserPublic, AuthSessionPublic] | None:
    ensure_auth_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT s.*, u.email, u.name, u.role, u.status, u.created_at AS user_created_at,
                   u.updated_at AS user_updated_at, u.last_login_at
            FROM {SESSIONS_TABLE} s
            JOIN {USERS_TABLE} u ON u.id = s.user_id
            WHERE s.token_hash = {placeholder}
            """,
            (hash_token(token),),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        session = row_to_session(data)
        if session.status != SessionStatus.active or data["status"] != UserStatus.active.value:
            return None
        if touch:
            now = utc_now()
            connection.execute(
                f"UPDATE {SESSIONS_TABLE} SET last_seen_at = {placeholder} WHERE id = {placeholder}",
                (now, session.id),
            )
            connection.commit()
            data["last_seen_at"] = now
            session = row_to_session(data)
    user = UserPublic(
        id=data["user_id"],
        email=data["email"],
        name=data["name"],
        role=normalize_role(data["role"]),
        status=UserStatus(data["status"]),
        created_at=data["user_created_at"],
        updated_at=data["user_updated_at"],
        last_login_at=data.get("last_login_at"),
    )
    return user, session


def token_from_authorization(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def current_user_from_authorization(authorization: str | None, request: Request | None = None) -> AuthenticatedUser:
    token = token_from_authorization(authorization)
    if not token:
        audit_auth_event(
            user_id=None,
            email=None,
            role=None,
            session_id=None,
            action="auth.access",
            resource=str(request.url.path) if request else "control_center",
            result="denied_missing_session",
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "session_required"})
    resolved = session_from_token(token)
    if resolved is None:
        audit_auth_event(
            user_id=None,
            email=None,
            role=None,
            session_id=None,
            action="auth.access",
            resource=str(request.url.path) if request else "control_center",
            result="denied_invalid_or_expired_session",
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "invalid_or_expired_session"})
    user, session = resolved
    return AuthenticatedUser(**user.model_dump(), session_id=session.id)


def require_control_center_user(
    request: Request,
    authorization: str | None = Header(default=None),
) -> AuthenticatedUser:
    user = current_user_from_authorization(authorization, request)
    audit_auth_event(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        session_id=user.session_id,
        action=f"{request.method} {request.url.path}",
        resource=str(request.url.path),
        result="allowed",
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )
    return user


def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
) -> AuthenticatedUser:
    return require_control_center_user(request, authorization)


def logout_user(user: AuthenticatedUser, request_data: object | None = None, request: Request | None = None) -> dict[str, str]:
    ensure_auth_schema()
    placeholder = sql_placeholder()
    now = utc_now()
    session_id = getattr(request_data, "session_id", None) or user.session_id
    with connect() as connection:
        connection.execute(
            f"""
            UPDATE {SESSIONS_TABLE}
            SET revoked_at = {placeholder}
            WHERE id = {placeholder} AND user_id = {placeholder} AND revoked_at IS NULL
            """,
            (now, session_id, user.id),
        )
        connection.commit()
    audit_auth_event(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        session_id=session_id,
        action="auth.logout",
        resource="control_center",
        result="success",
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )
    return {"status": "ok", "session_id": session_id}


def revoke_session(request_data: SessionRevokeRequest, user: AuthenticatedUser, request: Request | None = None) -> dict[str, str]:
    ensure_auth_schema()
    if user.role not in {ControlCenterRole.ceo, ControlCenterRole.admin} and request_data.session_id != user.session_id:
        audit_auth_event(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            session_id=user.session_id,
            action="auth.session_revoke",
            resource=request_data.session_id,
            result="denied_role_not_allowed",
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "role_not_authorized"})
    placeholder = sql_placeholder()
    now = utc_now()
    with connect() as connection:
        connection.execute(
            f"UPDATE {SESSIONS_TABLE} SET revoked_at = {placeholder} WHERE id = {placeholder}",
            (now, request_data.session_id),
        )
        connection.commit()
    audit_auth_event(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        session_id=user.session_id,
        action="auth.session_revoke",
        resource=request_data.session_id,
        result="success",
        ip_address=client_ip(request),
        user_agent=user_agent(request),
        metadata={"reason": request_data.reason},
    )
    return {"status": "ok", "session_id": request_data.session_id}


def list_sessions(user: AuthenticatedUser) -> list[AuthSessionPublic]:
    ensure_auth_schema()
    placeholder = sql_placeholder()
    params: tuple = (user.id,)
    where = f"WHERE user_id = {placeholder}"
    if user.role in {ControlCenterRole.ceo, ControlCenterRole.admin}:
        where = ""
        params = ()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM {SESSIONS_TABLE}
            {where}
            ORDER BY created_at DESC
            """,
            params,
        ).fetchall()
    return [row_to_session(dict(row)) for row in rows]


def list_auth_audit_events() -> list[AuthAuditEvent]:
    ensure_auth_schema()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM {SESSION_AUDIT_TABLE}
            ORDER BY timestamp DESC
            LIMIT 500
            """
        ).fetchall()
    return [
        AuthAuditEvent(
            id=row["id"],
            user_id=row["user_id"],
            email=row["email"],
            role=row["role"],
            session_id=row["session_id"],
            action=row["action"],
            resource=row["resource"],
            result=row["result"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            timestamp=row["timestamp"],
            metadata=safe_dict(safe_json_value(row["metadata_json"], {})),
        )
        for row in rows
    ]


def database_uses_postgres() -> bool:
    return get_database_backend(get_settings().database_url) == "postgresql"
