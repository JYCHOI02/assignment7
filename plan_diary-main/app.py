import uuid
import os
import passkey_service
from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import json
from datetime import datetime, date, timedelta, timezone
import calendar

# 서울 표준시 (KST, UTC+9) 지원 (T06-C30)
KST = timezone(timedelta(hours=9))


def get_kst_now():
    return datetime.now(KST)


def get_kst_today_str():
    return get_kst_now().strftime("%Y-%m-%d")


app = Flask(__name__)
# [T07] 보안 세션 설정 (XSS/CSRF 방어 및 세션 수명 관리)
app.secret_key = "aleph-pds-diary-assignment7-security-key-2026"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)

DATABASE = "database.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    # [T08 / Passkey] 패스키(생체인증/스마트폰 FIDO2) 자격증명 저장 테이블
    conn.execute("""
        CREATE TABLE IF NOT EXISTS passkeys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            credential_id TEXT UNIQUE NOT NULL,
            public_key TEXT NOT NULL,
            sign_count INTEGER NOT NULL DEFAULT 0,
            device_name TEXT NOT NULL DEFAULT '스마트폰 / 생체인증 기기',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # [T07-C94~C96] 사용자(Users) 테이블 생성
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,

            title TEXT NOT NULL,
            original_title TEXT NOT NULL DEFAULT '',

            original_priority TEXT NOT NULL DEFAULT '보통',
            original_start_date TEXT NOT NULL,
            original_end_date TEXT NOT NULL,
            original_success_criteria TEXT NOT NULL,
            original_expected_minutes INTEGER NOT NULL,

            current_priority TEXT NOT NULL DEFAULT '보통',
            current_start_date TEXT NOT NULL,
            current_end_date TEXT NOT NULL,
            current_success_criteria TEXT NOT NULL,
            current_expected_minutes INTEGER NOT NULL,

            status TEXT NOT NULL DEFAULT '진행중',
            tags TEXT NOT NULL DEFAULT '',

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 수정 이력 보존을 위한 별도 테이블 생성 (T06-C08 준수)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            title TEXT NOT NULL,
            priority TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            success_criteria TEXT NOT NULL,
            expected_minutes INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT '진행중',
            tags TEXT NOT NULL DEFAULT '',
            modified_at TEXT NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE
        )
    """)

    # 실행 기록(Do) 보존을 위한 별도 테이블 생성
    conn.execute("""
        CREATE TABLE IF NOT EXISTS execution_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            actual_minutes INTEGER NOT NULL,
            blocker_reason TEXT NOT NULL DEFAULT '',
            memo TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE
        )
    """)

    # 동일한 계획(plan_id)에 같은 시작 시각 및 끝 시각을 가진 실행 기록 중복 방지 인덱스
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_exec_plan_times
        ON execution_records (plan_id, start_time, end_time)
    """)

    # 완료 기록 단일 보존을 위한 별도 테이블 생성 (plan_id UNIQUE로 중복 생성 방지)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS completion_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL UNIQUE,
            completed_at TEXT NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE
        )
    """)

    # 돌아보기(See)에서 다음 계획(Plan)으로 넘길 한 줄(개선 액션) 보존을 위한 테이블
    conn.execute("""
        CREATE TABLE IF NOT EXISTS next_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action_text TEXT NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'custom',
            source_plan_id INTEGER,
            created_at TEXT NOT NULL,
            applied_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 계획에 딸린 세부 할 일(Subtasks) 관리를 위한 테이블 생성
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plan_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            is_completed INTEGER NOT NULL DEFAULT 0,
            due_date TEXT NOT NULL DEFAULT '',
            order_num INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE
        )
    """)

    # 기존 '완료' 상태인 계획이 있을 경우 completion_records 동기화 (중복 없이 1회만 등록)
    cursor_comp = conn.execute("SELECT id, updated_at FROM plans WHERE status = '완료'")
    for comp_row in cursor_comp.fetchall():
        conn.execute("""
            INSERT OR IGNORE INTO completion_records (plan_id, completed_at)
            VALUES (?, ?)
        """, (comp_row["id"], comp_row["updated_at"]))

    # 테이블 호환성 및 컬럼 추가 (PRAGMA table_info)
    cursor = conn.execute("PRAGMA table_info(plans)")
    columns = [row["name"] for row in cursor.fetchall()]

    if "user_id" not in columns:
        conn.execute("ALTER TABLE plans ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")
    if "status" not in columns:
        conn.execute("ALTER TABLE plans ADD COLUMN status TEXT NOT NULL DEFAULT '진행중'")
    if "original_title" not in columns:
        conn.execute("ALTER TABLE plans ADD COLUMN original_title TEXT NOT NULL DEFAULT ''")
        conn.execute("UPDATE plans SET original_title = title WHERE original_title = '' OR original_title IS NULL")
    if "original_priority" not in columns:
        conn.execute("ALTER TABLE plans ADD COLUMN original_priority TEXT NOT NULL DEFAULT '1순위'")
    if "current_priority" not in columns:
        conn.execute("ALTER TABLE plans ADD COLUMN current_priority TEXT NOT NULL DEFAULT '1순위'")
    if "tags" not in columns:
        conn.execute("ALTER TABLE plans ADD COLUMN tags TEXT NOT NULL DEFAULT ''")

    # next_actions user_id 추가
    cursor_na = conn.execute("PRAGMA table_info(next_actions)")
    na_cols = [row["name"] for row in cursor_na.fetchall()]
    if "user_id" not in na_cols:
        conn.execute("ALTER TABLE next_actions ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")

    # plan_history 테이블 컬럼 호환성 유지
    cursor_hist = conn.execute("PRAGMA table_info(plan_history)")
    hist_cols = [row["name"] for row in cursor_hist.fetchall()]
    if "tags" not in hist_cols:
        conn.execute("ALTER TABLE plan_history ADD COLUMN tags TEXT NOT NULL DEFAULT ''")

    # [T07-C94/요구사항 5] 기존 과제 6 샘플 데이터를 관리자(admin) 계정으로 마이그레이션
    admin_row = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not admin_row:
        now_str = get_kst_now().strftime("%Y-%m-%d %H:%M:%S")
        admin_hash = generate_password_hash("admin1234!")
        cur = conn.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)", ("admin", admin_hash, now_str))
        admin_id = cur.lastrowid
    else:
        admin_id = admin_row["id"]

    # user_id가 NULL인 기존 과제 6 샘플 데이터들을 admin 계정으로 마이그레이션 연동
    conn.execute("UPDATE plans SET user_id = ? WHERE user_id IS NULL", (admin_id,))
    conn.execute("UPDATE next_actions SET user_id = ? WHERE user_id IS NULL", (admin_id,))

    conn.commit()
    conn.close()


# ==============================================================================
# [T07] 보안 & 인증 헬퍼 함수
# ==============================================================================

def login_required(f):
    """비로그인 사용자의 접근을 차단하는 데코레이터 (T07-C97)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # API 요청인 경우 JSON 401 반환
            if request.path.startswith("/api/"):
                return jsonify({
                    "error": "Unauthorized",
                    "message": "로그인이 필요한 요청입니다."
                }), 401
            # 페이지 접근인 경우 로그인 페이지로 강제 리다이렉트 (T07-C97)
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function


def check_plan_ownership(conn, plan_id, user_id):
    """지정된 plan_id가 해당 user_id의 소유인지 검증 (타인 데이터 침범 방지)"""
    try:
        plan = conn.execute("SELECT * FROM plans WHERE id = ? AND user_id = ?", (int(plan_id), int(user_id))).fetchone()
        return plan
    except (ValueError, TypeError):
        return None


# ==============================================================================
# [T07-C94~C99] 인증 라우트 (회원가입, 로그인, 로그아웃, 상태 확인)
# ==============================================================================

@app.route("/login")
def login_page():
    # 이미 로그인된 상태라면 메인 화면으로 이동
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username:
        return jsonify({"success": False, "message": "아이디를 입력해 주세요."}), 400
    if len(username) < 2 or len(username) > 30:
        return jsonify({"success": False, "message": "아이디는 2자 이상 30자 이하로 입력해 주세요."}), 400
    if not password or len(password) < 4:
        return jsonify({"success": False, "message": "비밀번호는 최소 4자 이상 입력해 주세요."}), 400

    conn = get_db()
    # [T07-C98] 중복 아이디 가입 방지
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({
            "success": False,
            "message": "이미 사용 중인 아이디입니다. 다른 아이디를 입력해 주세요."
        }), 409

    now_str = get_kst_now().strftime("%Y-%m-%d %H:%M:%S")
    pw_hash = generate_password_hash(password)
    conn.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)", (username, pw_hash, now_str))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "회원가입이 완료되었습니다! 로그인해 주세요."
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        # [T07-C99] 계정 열거 방지
        return jsonify({"success": False, "message": "아이디 또는 비밀번호가 올바르지 않습니다."}), 401

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    # [T07-C99] 로그인 실패 시 보안 처리 (계정 열거 방지)
    # 아이디가 없는 경우와 비밀번호가 틀린 경우 동일한 에러 메시지 반환
    if not user or not check_password_hash(user["password_hash"], password):
        conn.close()
        return jsonify({
            "success": False,
            "message": "아이디 또는 비밀번호가 올바르지 않습니다."
        }), 401

    conn.close()

    # 세션 수립 (세션 고정 공격 방지용 session.clear 후 등록)
    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "message": f"{user['username']}님, 환영합니다!",
        "user": {
            "id": user["id"],
            "username": user["username"]
        }
    })


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    # [T07-C96] 로그아웃 시 세션 파기
    session.clear()
    return jsonify({
        "success": True,
        "message": "성공적으로 로그아웃되었습니다."
    })


@app.route("/api/auth/me", methods=["GET"])
def api_me():
    if "user_id" in session:
        return jsonify({
            "authenticated": True,
            "user": {
                "id": session["user_id"],
                "username": session["username"]
            }
        })
    return jsonify({"authenticated": False, "user": None}), 401


# ==============================================================================
# 메인 페이지 (T07-C97 로그인 필수)
# ==============================================================================


# ==============================================================================
# [Passkey / WebAuthn] 스마트폰 & 생체인증 (FIDO2) 엔드포인트
# ==============================================================================

@app.route("/api/auth/passkey/register-options", methods=["POST"])
@login_required
def passkey_register_options():
    """패스키 등록 옵션 생성 (로그인된 상태에서 내 폰/기기 등록)"""
    user_id = session["user_id"]
    username = session["username"]

    # 32바이트 무작위 챌린지 생성
    challenge = passkey_service.b64url_encode(os.urandom(32))
    session["passkey_reg_challenge"] = challenge

    user_handle = passkey_service.b64url_encode(str(user_id).encode("utf-8"))

    options = {
        "challenge": challenge,
        "rp": {
            "name": "플랜두씨 다이어리",
            "id": "localhost" if request.host.split(":")[0] in ["127.0.0.1", "localhost"] else request.host.split(":")[0]
        },
        "user": {
            "id": user_handle,
            "name": username,
            "displayName": f"{username}님의 플랜두씨 계정"
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7},   # ES256 (P-256)
            {"type": "public-key", "alg": -257}  # RS256
        ],
        "authenticatorSelection": {
            "residentKey": "preferred",
            "userVerification": "preferred"
        },
        "timeout": 60000,
        "attestation": "none"
    }

    return jsonify(options)


@app.route("/api/auth/passkey/register-verify", methods=["POST"])
@login_required
def passkey_register_verify():
    """브라우저의 WebAuthn 생성 결과 검증 및 패스키 등록"""
    user_id = session["user_id"]
    data = request.get_json() or {}

    expected_challenge = session.get("passkey_reg_challenge")
    if not expected_challenge:
        return jsonify({"success": False, "message": "세션이 만료되었습니다. 다시 시도해 주세요."}), 400

    resp = data.get("response", {})
    attestation_b64 = resp.get("attestationObject")
    client_data_b64 = resp.get("clientDataJSON")
    device_name = data.get("device_name", "").strip() or "스마트폰 / 생체인증 기기"

    if not attestation_b64 or not client_data_b64:
        return jsonify({"success": False, "message": "인증 데이터가 누락되었습니다."}), 400

    try:
        # 1. clientDataJSON 챌린지 검증
        client_data_bytes = passkey_service.b64url_decode(client_data_b64)
        client_data = json.loads(client_data_bytes.decode("utf-8"))

        if client_data.get("type") != "webauthn.create":
            return jsonify({"success": False, "message": "올바르지 않은 인증 타입입니다."}), 400

        c_challenge = client_data.get("challenge", "").replace("-", "+").replace("_", "/").rstrip("=")
        e_challenge = expected_challenge.replace("-", "+").replace("_", "/").rstrip("=")
        if c_challenge != e_challenge:
            return jsonify({"success": False, "message": "챌린지 검증에 실패했습니다."}), 400

        # 2. attestationObject 파싱 및 공개키 추출
        att_bytes = passkey_service.b64url_decode(attestation_b64)
        parsed = passkey_service.parse_attestation_object(att_bytes)

        cred_id_b64 = parsed["credential_id_b64"]
        pub_key_pem = parsed["public_key_pem"]

        now_str = get_kst_now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db()
        conn.execute("""
            INSERT INTO passkeys (user_id, credential_id, public_key, device_name, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, cred_id_b64, pub_key_pem, device_name, now_str))
        conn.commit()
        conn.close()

        # 사용한 챌린지 제거
        session.pop("passkey_reg_challenge", None)

        return jsonify({
            "success": True,
            "message": "스마트폰 / 생체인증(패스키) 등록이 성공적으로 완료되었습니다!"
        }), 201

    except Exception as err:
        return jsonify({"success": False, "message": f"패스키 등록 실패: {str(err)}"}), 400


@app.route("/api/auth/passkey/login-options", methods=["POST"])
def passkey_login_options():
    """패스키 로그인 챌린지 생성"""
    data = request.get_json() or {}
    username = data.get("username", "").strip()

    challenge = passkey_service.b64url_encode(os.urandom(32))
    session["passkey_login_challenge"] = challenge

    allow_credentials = []
    if username:
        conn = get_db()
        user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if user:
            keys = conn.execute("SELECT credential_id FROM passkeys WHERE user_id = ?", (user["id"],)).fetchall()
            for k in keys:
                allow_credentials.append({
                    "type": "public-key",
                    "id": k["credential_id"]
                })
        conn.close()

    options = {
        "challenge": challenge,
        "timeout": 60000,
        "rpId": "localhost" if request.host.split(":")[0] in ["127.0.0.1", "localhost"] else request.host.split(":")[0],
        "userVerification": "preferred",
        "allowCredentials": allow_credentials
    }

    return jsonify(options)


@app.route("/api/auth/passkey/login-verify", methods=["POST"])
def passkey_login_verify():
    """패스키 생체인증 서명 검증 후 세션 수립 (1초 로그인)"""
    data = request.get_json() or {}
    expected_challenge = session.get("passkey_login_challenge")

    if not expected_challenge:
        return jsonify({"success": False, "message": "로그인 세션이 만료되었습니다. 다시 시도해 주세요."}), 400

    cred_id = data.get("id")
    resp = data.get("response", {})
    auth_data_b64 = resp.get("authenticatorData")
    client_data_b64 = resp.get("clientDataJSON")
    sig_b64 = resp.get("signature")

    if not cred_id or not auth_data_b64 or not client_data_b64 or not sig_b64:
        return jsonify({"success": False, "message": "인증 파라미터가 누락되었습니다."}), 400

    conn = get_db()
    # 등록된 패스키 및 소유자 조회
    row = conn.execute("""
        SELECT p.*, u.username, u.id AS uid
        FROM passkeys p
        JOIN users u ON p.user_id = u.id
        WHERE p.credential_id = ?
    """, (cred_id,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "message": "등록되지 않은 패스키 기기입니다."}), 401

    try:
        # 서명 검증 수행
        is_valid = passkey_service.verify_assertion(
            public_key_pem=row["public_key"],
            authenticator_data_b64=auth_data_b64,
            client_data_json_b64=client_data_b64,
            signature_b64=sig_b64,
            expected_challenge_b64=expected_challenge
        )

        if not is_valid:
            conn.close()
            return jsonify({"success": False, "message": "생체인증 서명 검증에 실패했습니다."}), 401

        # 로그인 성공 -> 세션 수립
        session.clear()
        session.permanent = True
        session["user_id"] = row["uid"]
        session["username"] = row["username"]

        conn.close()
        return jsonify({
            "success": True,
            "message": f"🔑 {row['username']}님, 스마트폰/생체인증으로 환영합니다!",
            "user": {
                "id": row["uid"],
                "username": row["username"]
            }
        })

    except Exception as err:
        conn.close()
        return jsonify({"success": False, "message": f"패스키 검증 오류: {str(err)}"}), 400


@app.route("/api/auth/passkeys", methods=["GET"])
@login_required
def get_user_passkeys():
    """현재 사용자가 등록한 패스키 기기 목록 반환"""
    user_id = session["user_id"]
    conn = get_db()
    rows = conn.execute("""
        SELECT id, device_name, created_at
        FROM passkeys
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()
    conn.close()

    return jsonify({
        "passkeys": [dict(r) for r in rows],
        "count": len(rows)
    })


@app.route("/api/auth/passkey/<int:passkey_id>", methods=["DELETE"])
@login_required
def delete_user_passkey(passkey_id):
    """패스키 기기 삭제"""
    user_id = session["user_id"]
    conn = get_db()
    conn.execute("DELETE FROM passkeys WHERE id = ? AND user_id = ?", (passkey_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "패스키 기기가 삭제되었습니다."})



# ==============================================================================
# [QR Remote Approval] 스마트폰 지문인증으로 컴퓨터 자동 로그인 (카카오톡/토스 방식)
# ==============================================================================

@app.route("/api/auth/qr/create", methods=["POST"])
def qr_create():
    """PC 화면에 띄울 일회용 로그인 세션 토큰 및 QR URL 생성"""
    token = str(uuid.uuid4())
    now_kst = get_kst_now()
    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")
    expires_str = (now_kst + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS qr_login_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            user_id INTEGER,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        INSERT INTO qr_login_sessions (token, status, created_at, expires_at)
        VALUES (?, 'PENDING', ?, ?)
    """, (token, now_str, expires_str))
    conn.commit()
    conn.close()

    # 터널 URL 우선, 없으면 request.host_url
    base_url = "https://fixtures-choosing-integrated-concentrate.trycloudflare.com"
    approve_url = f"{base_url}/mobile-approve?token={token}"

    return jsonify({
        "success": True,
        "token": token,
        "approve_url": approve_url,
        "expires_in": 300
    })


@app.route("/api/auth/qr/poll", methods=["GET"])
def qr_poll():
    """PC 브라우저가 1초마다 상태 확인 (스마트폰 승인 시 PC 자동 로그인)"""
    token = request.args.get("token")
    if not token:
        return jsonify({"status": "INVALID"}), 400

    conn = get_db()
    row = conn.execute("""
        SELECT q.*, u.username
        FROM qr_login_sessions q
        LEFT JOIN users u ON q.user_id = u.id
        WHERE q.token = ?
    """, (token,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"status": "NOT_FOUND"}), 404

    now_str = get_kst_now().strftime("%Y-%m-%d %H:%M:%S")
    if row["expires_at"] < now_str:
        conn.close()
        return jsonify({"status": "EXPIRED"})

    if row["status"] == "APPROVED" and row["user_id"]:
        # 스마트폰에서 지문 인증 승인 완료 -> PC 세션 자동 수립!
        session.clear()
        session.permanent = True
        session["user_id"] = row["user_id"]
        session["username"] = row["username"]

        # 1회 사용 후 토큰 폐기 (재사용 방지)
        conn.execute("UPDATE qr_login_sessions SET status = 'CONSUMED' WHERE token = ?", (token,))
        conn.commit()
        conn.close()

        return jsonify({
            "status": "APPROVED",
            "message": f"🔑 {row['username']}님, 스마트폰 지문인증으로 컴퓨터에 로그인되었습니다!",
            "username": row["username"]
        })

    conn.close()
    return jsonify({"status": row["status"]})


@app.route("/mobile-approve")
def mobile_approve_page():
    """스마트폰에서 QR을 찍었을 때 열리는 모바일 지문 승인 화면"""
    token = request.args.get("token", "")
    conn = get_db()
    # 패스키가 1개 이상 등록된 사용자만 승인 가능
    users_with_passkeys = conn.execute("""
        SELECT u.id, u.username, COUNT(p.id) as passkey_count
        FROM users u
        LEFT JOIN passkeys p ON u.id = p.user_id
        GROUP BY u.id
        ORDER BY u.id ASC
    """).fetchall()
    conn.close()

    user_list = []
    for u in users_with_passkeys:
        user_list.append({
            "id": u["id"],
            "username": u["username"],
            "has_passkey": bool(u["passkey_count"] > 0)
        })

    return render_template("mobile_approve.html", token=token, users=user_list)


@app.route("/api/auth/qr/approve-options", methods=["POST"])
def qr_approve_options():
    """스마트폰 지문 인증을 위한 WebAuthn Assertion 챌린지 생성"""
    data = request.get_json() or {}
    token = data.get("token")
    username = data.get("username", "").strip()

    conn = get_db()
    user = conn.execute("SELECT id, username FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"success": False, "message": "존재하지 않는 계정입니다."}), 404

    # 해당 유저의 등록된 패스키 조회
    keys = conn.execute("SELECT credential_id FROM passkeys WHERE user_id = ?", (user["id"],)).fetchall()
    conn.close()

    if not keys:
        return jsonify({
            "success": False,
            "message": f"'{username}' 계정에는 등록된 패스키 기기가 없습니다. 먼저 컴퓨터나 스마트폰에서 패스키를 등록해 주세요."
        }), 400

    # 챌린지 발급
    challenge = passkey_service.b64url_encode(os.urandom(32))
    session[f"qr_challenge_{token}"] = challenge

    allow_credentials = [{"type": "public-key", "id": k["credential_id"]} for k in keys]

    return jsonify({
        "success": True,
        "challenge": challenge,
        "allowCredentials": allow_credentials,
        "rpId": "fixtures-choosing-integrated-concentrate.trycloudflare.com" if "trycloudflare.com" in request.host else "localhost",
        "timeout": 60000,
        "userVerification": "required"
    })


@app.route("/api/auth/qr/approve", methods=["POST"])
def qr_approve():
    """스마트폰에서 실제 암호학적 지문 서명(WebAuthn) 검증 후 컴퓨터 로그인 승인"""
    data = request.get_json() or {}
    token = data.get("token")
    username = data.get("username", "").strip()

    expected_challenge = session.get(f"qr_challenge_{token}")
    if not expected_challenge:
        return jsonify({"success": False, "message": "승인 세션이 만료되었습니다. 다시 시도해 주세요."}), 400

    cred_id = data.get("id")
    resp = data.get("response", {})
    auth_data_b64 = resp.get("authenticatorData")
    client_data_b64 = resp.get("clientDataJSON")
    sig_b64 = resp.get("signature")

    if not cred_id or not auth_data_b64 or not client_data_b64 or not sig_b64:
        return jsonify({
            "success": False,
            "message": "스마트폰 지문 인증(서명) 데이터가 누락되었습니다. 등록된 지문으로 인증해야 합니다."
        }), 400

    conn = get_db()
    # 등록된 패스키 확인 및 소유자 검증
    passkey_row = conn.execute("""
        SELECT p.*, u.username, u.id AS uid
        FROM passkeys p
        JOIN users u ON p.user_id = u.id
        WHERE p.credential_id = ? AND u.username = ?
    """, (cred_id, username)).fetchone()

    if not passkey_row:
        conn.close()
        return jsonify({
            "success": False,
            "message": f"이 기기는 '{username}' 계정에 등록된 패스키가 아닙니다. 본인이 등록한 기기에서만 승인할 수 있습니다."
        }), 403

    # 암호학적 서명 검증 수행
    try:
        is_valid = passkey_service.verify_assertion(
            public_key_pem=passkey_row["public_key"],
            authenticator_data_b64=auth_data_b64,
            client_data_json_b64=client_data_b64,
            signature_b64=sig_b64,
            expected_challenge_b64=expected_challenge
        )
        if not is_valid:
            conn.close()
            return jsonify({"success": False, "message": "지문 전자서명 검증에 실패했습니다."}), 401
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": f"서명 검증 오류: {str(e)}"}), 400

    session_row = conn.execute("SELECT * FROM qr_login_sessions WHERE token = ?", (token,)).fetchone()
    if not session_row:
        conn.close()
        return jsonify({"success": False, "message": "유효하지 않은 QR 세션입니다."}), 404

    now_str = get_kst_now().strftime("%Y-%m-%d %H:%M:%S")
    if session_row["expires_at"] < now_str or session_row["status"] != "PENDING":
        conn.close()
        return jsonify({"success": False, "message": "만료되었거나 이미 사용된 QR 세션입니다."}), 400

    # 승인 완료 처리
    conn.execute("""
        UPDATE qr_login_sessions
        SET status = 'APPROVED', user_id = ?
        WHERE token = ?
    """, (passkey_row["uid"], token))
    conn.commit()
    conn.close()

    # 챌린지 정리
    session.pop(f"qr_challenge_{token}", None)

    return jsonify({
        "success": True,
        "message": f"🎉 {username}님의 지문 서명이 검증되었습니다! 컴퓨터 화면을 확인해 주세요."
    })


@app.route("/")
@login_required
def index():
    return render_template("index.html", current_user={"id": session["user_id"], "username": session["username"]})


# ==============================================================================
# 계획(Plan) 관련 엔드포인트 (사용자별 격리)
# ==============================================================================

@app.route("/api/plans", methods=["GET"])
@login_required
def get_plans():
    user_id = session["user_id"]
    query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    tag_filter = request.args.get("tag", "").strip()
    sort_by = request.args.get("sort", "priority-asc").strip()

    conn = get_db()

    # [격리] p.user_id = ? 필수 적용
    sql = """
        SELECT p.*,
               (SELECT COUNT(*) FROM plan_history h WHERE h.plan_id = p.id) AS history_count,
               (SELECT COUNT(*) FROM execution_records e WHERE e.plan_id = p.id) AS execution_count,
               (SELECT COALESCE(SUM(actual_minutes), 0) FROM execution_records e WHERE e.plan_id = p.id) AS actual_minutes_sum,
               (SELECT completed_at FROM completion_records c WHERE c.plan_id = p.id) AS completed_at,
               (SELECT COUNT(*) FROM plan_tasks t WHERE t.plan_id = p.id) AS task_count,
               (SELECT COUNT(*) FROM plan_tasks t WHERE t.plan_id = p.id AND t.is_completed = 1) AS completed_task_count
        FROM plans p
        WHERE p.user_id = ?
    """
    params = [user_id]

    if query:
        sql += " AND (p.title LIKE ? OR p.tags LIKE ? OR p.current_success_criteria LIKE ?)"
        q_wild = f"%{query}%"
        params.extend([q_wild, q_wild, q_wild])

    if status_filter and status_filter != "all":
        if status_filter == "지연":
            today_str = datetime.now().strftime("%Y-%m-%d")
            sql += """ AND (
                (p.status != '완료' AND p.current_end_date < ?)
                OR
                (p.status = '완료' AND (SELECT completed_at FROM completion_records c WHERE c.plan_id = p.id) IS NOT NULL AND SUBSTR((SELECT completed_at FROM completion_records c WHERE c.plan_id = p.id), 1, 10) > p.current_end_date)
            )"""
            params.append(today_str)
        elif status_filter == "막힘":
            sql += " AND (SELECT COUNT(*) FROM execution_records e WHERE e.plan_id = p.id AND e.blocker_reason IS NOT NULL AND TRIM(e.blocker_reason) != '') > 0"
        else:
            sql += " AND p.status = ?"
            params.append(status_filter)

    if priority_filter and priority_filter != "all":
        sql += " AND p.current_priority = ?"
        params.append(priority_filter)

    if tag_filter and tag_filter != "all":
        sql += " AND p.tags LIKE ?"
        params.append(f"%{tag_filter}%")

    if sort_by == "date-desc":
        sql += " ORDER BY p.id DESC"
    elif sort_by == "due-asc":
        sql += " ORDER BY p.current_end_date ASC, p.id DESC"
    elif sort_by == "time-asc":
        sql += " ORDER BY p.current_expected_minutes ASC, p.id DESC"
    else:  # priority-asc (기본)
        sql += """
            ORDER BY
                CASE
                    WHEN p.current_priority LIKE '%순위' THEN CAST(REPLACE(p.current_priority, '순위', '') AS INTEGER)
                    ELSE 999999
                END ASC,
                p.id DESC
        """

    cursor = conn.execute(sql, params)
    raw_rows = cursor.fetchall()
    today_str = get_kst_today_str()
    plans = []
    for row in raw_rows:
        d = dict(row)
        is_comp = (d.get("status") == "완료")
        p_end = d.get("current_end_date")
        d["is_delayed"] = bool(not is_comp and p_end and p_end < today_str)
        plans.append(d)

    conn.close()

    return jsonify({
        "plans": plans,
        "count": len(plans)
    })


@app.route("/api/plan", methods=["GET"])
@login_required
def get_plan():
    user_id = session["user_id"]
    plan_id = request.args.get("id")
    conn = get_db()

    if plan_id:
        try:
            plan = conn.execute("SELECT * FROM plans WHERE id = ? AND user_id = ?", (int(plan_id), user_id)).fetchone()
        except (ValueError, TypeError):
            plan = None
    else:
        plan = conn.execute("""
            SELECT *
            FROM plans
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,)).fetchone()

    if plan is None:
        conn.close()
        return jsonify({
            "exists": False
        })

    plan_data = dict(plan)
    conn.close()

    return jsonify({
        "exists": True,
        "plan": plan_data
    })


@app.route("/api/plan", methods=["POST"])
@login_required
def create_plan():
    user_id = session["user_id"]
    data = request.get_json()

    title = data.get("title", "").strip()
    priority = data.get("priority", "").strip()
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    success_criteria = data.get("success_criteria", "").strip()

    try:
        expected_minutes = int(data.get("expected_minutes", 0))
    except (ValueError, TypeError):
        expected_minutes = 0

    if not title:
        return jsonify({"success": False, "message": "계획명을 입력해 주세요."}), 400
    if not start_date or not end_date:
        return jsonify({"success": False, "message": "기간을 입력해 주세요."}), 400
    if start_date > end_date:
        return jsonify({"success": False, "message": "시작일이 종료일보다 늦을 수 없습니다."}), 400
    if not success_criteria:
        return jsonify({"success": False, "message": "성공 기준을 입력해 주세요."}), 400
    if expected_minutes <= 0:
        return jsonify({"success": False, "message": "예상 시간은 1분 이상 입력해 주세요."}), 400

    now_kst = get_kst_now()
    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()

    # 사용자의 기존 계획들 우선순위 정렬 및 밀어내기
    cur_p_rows = conn.execute("""
        SELECT id, current_priority
        FROM plans
        WHERE user_id = ?
        ORDER BY
            CASE
                WHEN current_priority LIKE '%순위' THEN CAST(REPLACE(current_priority, '순위', '') AS INTEGER)
                ELSE 999999
            END ASC,
            id ASC
    """, (user_id,)).fetchall()

    target_num = None
    if priority and priority.endswith("순위"):
        try:
            target_num = int(priority.replace("순위", ""))
        except ValueError:
            target_num = None

    if target_num is not None:
        final_priority = f"{target_num}순위"
        for p_row in cur_p_rows:
            p_curr = p_row["current_priority"]
            if p_curr and p_curr.endswith("순위"):
                try:
                    c_num = int(p_curr.replace("순위", ""))
                    if c_num >= target_num:
                        new_p_str = f"{c_num + 1}순위"
                        conn.execute("UPDATE plans SET current_priority = ? WHERE id = ? AND user_id = ?", (new_p_str, p_row["id"], user_id))
                except ValueError:
                    pass
    else:
        max_num = 0
        for p_row in cur_p_rows:
            p_curr = p_row["current_priority"]
            if p_curr and p_curr.endswith("순위"):
                try:
                    c_num = int(p_curr.replace("순위", ""))
                    if c_num > max_num:
                        max_num = c_num
                except ValueError:
                    pass
        final_priority = f"{max_num + 1}순위"

    cursor = conn.execute("""
        INSERT INTO plans (
            user_id,
            title, original_title,
            original_priority, original_start_date, original_end_date, original_success_criteria, original_expected_minutes,
            current_priority, current_start_date, current_end_date, current_success_criteria, current_expected_minutes,
            status, tags, created_at, updated_at
        ) VALUES (
            ?,
            ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            '진행중', '', ?, ?
        )
    """, (
        user_id,
        title, title,
        final_priority, start_date, end_date, success_criteria, expected_minutes,
        final_priority, start_date, end_date, success_criteria, expected_minutes,
        now_str, now_str
    ))

    new_id = cursor.lastrowid
    conn.commit()

    saved_plan = conn.execute("SELECT * FROM plans WHERE id = ? AND user_id = ?", (new_id, user_id)).fetchone()
    conn.close()

    return jsonify({
        "success": True,
        "message": "새 계획이 안전하게 등록되었습니다.",
        "plan": dict(saved_plan)
    }), 201


@app.route("/api/plan", methods=["PUT"])
@login_required
def update_plan():
    user_id = session["user_id"]
    data = request.get_json()

    try:
        plan_id = int(data.get("id"))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "잘못된 계획 ID입니다."}), 400

    title = data.get("title", "").strip()
    priority = data.get("priority", "").strip()
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    success_criteria = data.get("success_criteria", "").strip()

    try:
        expected_minutes = int(data.get("expected_minutes", 0))
    except (ValueError, TypeError):
        expected_minutes = 0

    if not title:
        return jsonify({"success": False, "message": "계획명을 입력해 주세요."}), 400
    if not start_date or not end_date:
        return jsonify({"success": False, "message": "기간을 입력해 주세요."}), 400
    if start_date > end_date:
        return jsonify({"success": False, "message": "시작일이 종료일보다 늦을 수 없습니다."}), 400
    if not success_criteria:
        return jsonify({"success": False, "message": "성공 기준을 입력해 주세요."}), 400
    if expected_minutes <= 0:
        return jsonify({"success": False, "message": "예상 시간은 1분 이상 입력해 주세요."}), 400

    conn = get_db()
    current_plan = check_plan_ownership(conn, plan_id, user_id)
    if current_plan is None:
        conn.close()
        return jsonify({"success": False, "message": "해당 계획을 수정할 권한이 없습니다."}), 403

    now_kst = get_kst_now()
    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")

    # 버전 산출 및 이전 스냅샷 history 테이블에 보존 (T06-C08)
    last_hist = conn.execute("""
        SELECT version FROM plan_history
        WHERE plan_id = ?
        ORDER BY version DESC LIMIT 1
    """, (plan_id,)).fetchone()
    next_ver = (last_hist["version"] + 1) if last_hist else 1

    conn.execute("""
        INSERT INTO plan_history (
            plan_id, version, title, priority,
            start_date, end_date, success_criteria,
            expected_minutes, status, tags, modified_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        plan_id,
        next_ver,
        current_plan["title"],
        current_plan["current_priority"],
        current_plan["current_start_date"],
        current_plan["current_end_date"],
        current_plan["current_success_criteria"],
        current_plan["current_expected_minutes"],
        current_plan["status"],
        current_plan["tags"],
        current_plan["updated_at"]
    ))

    # 우선순위 재배치
    cur_p_rows = conn.execute("""
        SELECT id, current_priority
        FROM plans
        WHERE user_id = ? AND id != ?
        ORDER BY
            CASE
                WHEN current_priority LIKE '%순위' THEN CAST(REPLACE(current_priority, '순위', '') AS INTEGER)
                ELSE 999999
            END ASC,
            id ASC
    """, (user_id, plan_id)).fetchall()

    target_num = None
    if priority and priority.endswith("순위"):
        try:
            target_num = int(priority.replace("순위", ""))
        except ValueError:
            target_num = None

    if target_num is not None:
        final_priority = f"{target_num}순위"
        for p_row in cur_p_rows:
            p_curr = p_row["current_priority"]
            if p_curr and p_curr.endswith("순위"):
                try:
                    c_num = int(p_curr.replace("순위", ""))
                    if c_num >= target_num:
                        new_p_str = f"{c_num + 1}순위"
                        conn.execute("UPDATE plans SET current_priority = ? WHERE id = ? AND user_id = ?", (new_p_str, p_row["id"], user_id))
                except ValueError:
                    pass
    else:
        final_priority = current_plan["current_priority"]

    conn.execute("""
        UPDATE plans
        SET title = ?,
            current_priority = ?,
            current_start_date = ?,
            current_end_date = ?,
            current_success_criteria = ?,
            current_expected_minutes = ?,
            updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (
        title,
        final_priority,
        start_date,
        end_date,
        success_criteria,
        expected_minutes,
        now_str,
        plan_id,
        user_id
    ))

    conn.commit()
    updated_plan = conn.execute("SELECT * FROM plans WHERE id = ? AND user_id = ?", (plan_id, user_id)).fetchone()
    conn.close()

    return jsonify({
        "success": True,
        "message": "계획이 안전하게 수정되었습니다. (이전 내용은 변경 이력에 보존됨)",
        "plan": dict(updated_plan)
    })


@app.route("/api/plan/<int:plan_id>/history", methods=["GET"])
@login_required
def get_plan_history(plan_id):
    user_id = session["user_id"]
    conn = get_db()
    if not check_plan_ownership(conn, plan_id, user_id):
        conn.close()
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    history_cursor = conn.execute("""
        SELECT *
        FROM plan_history
        WHERE plan_id = ?
        ORDER BY version DESC, id DESC
    """, (plan_id,))

    history = [dict(row) for row in history_cursor.fetchall()]
    conn.close()

    return jsonify({
        "history": history,
        "count": len(history)
    })


@app.route("/api/plan/<int:plan_id>/history/<int:history_id>/restore", methods=["POST"])
@login_required
def restore_plan_history(plan_id, history_id):
    user_id = session["user_id"]
    conn = get_db()
    current_plan = check_plan_ownership(conn, plan_id, user_id)
    if current_plan is None:
        conn.close()
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    hist_item = conn.execute("""
        SELECT * FROM plan_history
        WHERE id = ? AND plan_id = ?
    """, (history_id, plan_id)).fetchone()

    if hist_item is None:
        conn.close()
        return jsonify({"success": False, "message": "해당 이력 정보를 찾을 수 없습니다."}), 404

    now_kst = get_kst_now()
    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")

    last_ver_row = conn.execute("""
        SELECT version FROM plan_history
        WHERE plan_id = ?
        ORDER BY version DESC LIMIT 1
    """, (plan_id,)).fetchone()
    next_ver = (last_ver_row["version"] + 1) if last_ver_row else 1

    conn.execute("""
        INSERT INTO plan_history (
            plan_id, version, title, priority,
            start_date, end_date, success_criteria,
            expected_minutes, status, tags, modified_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        plan_id,
        next_ver,
        current_plan["title"],
        current_plan["current_priority"],
        current_plan["current_start_date"],
        current_plan["current_end_date"],
        current_plan["current_success_criteria"],
        current_plan["current_expected_minutes"],
        current_plan["status"],
        current_plan["tags"],
        current_plan["updated_at"]
    ))

    conn.execute("""
        UPDATE plans
        SET title = ?,
            current_priority = ?,
            current_start_date = ?,
            current_end_date = ?,
            current_success_criteria = ?,
            current_expected_minutes = ?,
            status = ?,
            tags = ?,
            updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (
        hist_item["title"],
        hist_item["priority"],
        hist_item["start_date"],
        hist_item["end_date"],
        hist_item["success_criteria"],
        hist_item["expected_minutes"],
        hist_item["status"],
        hist_item["tags"],
        now_str,
        plan_id,
        user_id
    ))

    conn.commit()
    restored_plan = conn.execute("SELECT * FROM plans WHERE id = ? AND user_id = ?", (plan_id, user_id)).fetchone()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"버전 {hist_item['version']} 상태로 계획이 안전하게 복원되었습니다.",
        "plan": dict(restored_plan)
    })


@app.route("/api/plans/reorder", methods=["PUT"])
@login_required
def reorder_plans():
    user_id = session["user_id"]
    data = request.get_json()
    orders = data.get("orders", [])

    if not orders:
        return jsonify({"success": False, "message": "정렬 정보가 없습니다."}), 400

    conn = get_db()
    for item in orders:
        plan_id = item.get("id")
        new_priority = item.get("priority")
        if plan_id and new_priority:
            conn.execute("""
                UPDATE plans
                SET current_priority = ?
                WHERE id = ? AND user_id = ?
            """, (new_priority, plan_id, user_id))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "우선순위 순서가 정상적으로 재정렬되었습니다."
    })


@app.route("/api/plan/<int:plan_id>/status", methods=["PUT", "POST"])
@login_required
def update_plan_status(plan_id):
    user_id = session["user_id"]
    conn = get_db()
    plan = check_plan_ownership(conn, plan_id, user_id)
    if not plan:
        conn.close()
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    data = request.get_json() or {}
    new_status = data.get("status")

    if not new_status:
        current_status = plan["status"]
        new_status = "진행중" if current_status == "완료" else "완료"

    now_kst = get_kst_now()
    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("""
        UPDATE plans
        SET status = ?,
            updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (new_status, now_str, plan_id, user_id))

    if new_status == "완료":
        conn.execute("""
            INSERT OR IGNORE INTO completion_records (plan_id, completed_at)
            VALUES (?, ?)
        """, (plan_id, now_str))
    else:
        conn.execute("DELETE FROM completion_records WHERE plan_id = ?", (plan_id,))

    conn.commit()
    updated_plan = conn.execute("SELECT * FROM plans WHERE id = ? AND user_id = ?", (plan_id, user_id)).fetchone()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"계획 상태가 '{new_status}'(으)로 변경되었습니다.",
        "plan": dict(updated_plan)
    })


@app.route("/api/plan/<int:plan_id>/tasks", methods=["GET"])
@login_required
def get_plan_tasks(plan_id):
    user_id = session["user_id"]
    conn = get_db()
    if not check_plan_ownership(conn, plan_id, user_id):
        conn.close()
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    tasks_cursor = conn.execute("""
        SELECT *
        FROM plan_tasks
        WHERE plan_id = ?
        ORDER BY order_num ASC, id ASC
    """, (plan_id,))

    tasks = [dict(r) for r in tasks_cursor.fetchall()]
    conn.close()

    return jsonify({
        "tasks": tasks,
        "count": len(tasks)
    })


@app.route("/api/plan/<int:plan_id>/tasks", methods=["POST"])
@login_required
def add_plan_task(plan_id):
    user_id = session["user_id"]
    conn = get_db()
    if not check_plan_ownership(conn, plan_id, user_id):
        conn.close()
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    data = request.get_json() or {}
    title = data.get("title", "").strip()
    due_date = data.get("due_date", "").strip()

    if not title:
        conn.close()
        return jsonify({"success": False, "message": "할 일 제목을 입력해 주세요."}), 400

    now_kst = get_kst_now()
    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")

    max_order_row = conn.execute("SELECT COALESCE(MAX(order_num), 0) AS mo FROM plan_tasks WHERE plan_id = ?", (plan_id,)).fetchone()
    next_order = max_order_row["mo"] + 1

    cursor = conn.execute("""
        INSERT INTO plan_tasks (plan_id, title, is_completed, due_date, order_num, created_at, updated_at)
        VALUES (?, ?, 0, ?, ?, ?, ?)
    """, (plan_id, title, due_date, next_order, now_str, now_str))

    new_id = cursor.lastrowid
    conn.commit()

    new_task = conn.execute("SELECT * FROM plan_tasks WHERE id = ?", (new_id,)).fetchone()
    conn.close()

    return jsonify({
        "success": True,
        "message": "할 일이 추가되었습니다.",
        "task": dict(new_task)
    }), 201


@app.route("/api/plan/<int:plan_id>/task/<int:task_id>", methods=["PUT"])
@login_required
def update_plan_task(plan_id, task_id):
    user_id = session["user_id"]
    conn = get_db()
    if not check_plan_ownership(conn, plan_id, user_id):
        conn.close()
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    task = conn.execute("SELECT * FROM plan_tasks WHERE id = ? AND plan_id = ?", (task_id, plan_id)).fetchone()
    if not task:
        conn.close()
        return jsonify({"success": False, "message": "할 일을 찾을 수 없습니다."}), 404

    data = request.get_json() or {}
    now_kst = get_kst_now()
    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")

    updates = []
    params = []

    if "title" in data:
        t = data["title"].strip()
        if not t:
            conn.close()
            return jsonify({"success": False, "message": "제목을 입력해 주세요."}), 400
        updates.append("title = ?")
        params.append(t)

    if "is_completed" in data:
        updates.append("is_completed = ?")
        params.append(1 if data["is_completed"] else 0)

    if "due_date" in data:
        updates.append("due_date = ?")
        params.append(data["due_date"].strip())

    if not updates:
        conn.close()
        return jsonify({"success": False, "message": "변경할 항목이 없습니다."}), 400

    updates.append("updated_at = ?")
    params.append(now_str)
    params.extend([task_id, plan_id])

    conn.execute(f"UPDATE plan_tasks SET {', '.join(updates)} WHERE id = ? AND plan_id = ?", params)
    conn.commit()

    updated_task = conn.execute("SELECT * FROM plan_tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()

    return jsonify({
        "success": True,
        "message": "할 일이 변경되었습니다.",
        "task": dict(updated_task)
    })


@app.route("/api/plan/<int:plan_id>/task/<int:task_id>", methods=["DELETE"])
@login_required
def delete_plan_task(plan_id, task_id):
    user_id = session["user_id"]
    conn = get_db()
    if not check_plan_ownership(conn, plan_id, user_id):
        conn.close()
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    conn.execute("DELETE FROM plan_tasks WHERE id = ? AND plan_id = ?", (task_id, plan_id))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "할 일이 삭제되었습니다."
    })


# ==============================================================================
# 실행 기록(Do) 엔드포인트 (사용자별 격리)
# ==============================================================================

@app.route("/api/plan/<int:plan_id>/executions", methods=["GET"])
@login_required
def get_plan_executions(plan_id):
    user_id = session["user_id"]
    conn = get_db()
    if not check_plan_ownership(conn, plan_id, user_id):
        conn.close()
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    cursor = conn.execute("""
        SELECT *
        FROM execution_records
        WHERE plan_id = ?
        ORDER BY start_time ASC, id ASC
    """, (plan_id,))

    records = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "executions": records,
        "count": len(records)
    })


@app.route("/api/plan/<int:plan_id>/execution", methods=["POST"])
@login_required
def add_execution_record(plan_id):
    user_id = session["user_id"]
    conn = get_db()
    plan = check_plan_ownership(conn, plan_id, user_id)
    if not plan:
        conn.close()
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    data = request.get_json() or {}
    start_time = data.get("start_time", "").strip()
    end_time = data.get("end_time", "").strip()
    blocker_reason = data.get("blocker_reason", "").strip()
    memo = data.get("memo", "").strip()

    if not start_time or not end_time:
        conn.close()
        return jsonify({"success": False, "message": "시작 시각과 종료 시각을 모두 입력해 주세요."}), 400

    try:
        t_fmt = "%Y-%m-%d %H:%M" if len(start_time) == 16 else "%Y-%m-%d %H:%M:%S"
        t_start = datetime.strptime(start_time, t_fmt)
        t_end_fmt = "%Y-%m-%d %H:%M" if len(end_time) == 16 else "%Y-%m-%d %H:%M:%S"
        t_end = datetime.strptime(end_time, t_end_fmt)
    except ValueError:
        conn.close()
        return jsonify({"success": False, "message": "날짜 및 시간 형식이 올바르지 않습니다. (YYYY-MM-DD HH:MM)"}), 400

    if t_start >= t_end:
        conn.close()
        return jsonify({"success": False, "message": "종료 시각은 시작 시각보다 뒤여야 합니다."}), 400

    diff_seconds = (t_end - t_start).total_seconds()
    actual_minutes = int(diff_seconds // 60)

    # 멱등성 검증 (동일 구간 중복 방지)
    existing = conn.execute("""
        SELECT id FROM execution_records
        WHERE plan_id = ? AND start_time = ? AND end_time = ?
    """, (plan_id, start_time, end_time)).fetchone()

    if existing:
        conn.close()
        return jsonify({
            "success": False,
            "message": "이미 동일한 시작 및 종료 시각으로 등록된 실행 기록이 존재합니다. (중복 방지)"
        }), 409

    now_kst = get_kst_now()
    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.execute("""
        INSERT INTO execution_records (
            plan_id, start_time, end_time, actual_minutes, blocker_reason, memo, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        plan_id, start_time, end_time, actual_minutes, blocker_reason, memo, now_str
    ))

    new_id = cursor.lastrowid

    # 계획 최종 업데이트 일시 갱신
    conn.execute("UPDATE plans SET updated_at = ? WHERE id = ? AND user_id = ?", (now_str, plan_id, user_id))
    conn.commit()

    saved_record = conn.execute("SELECT * FROM execution_records WHERE id = ?", (new_id,)).fetchone()
    conn.close()

    return jsonify({
        "success": True,
        "message": "실행 기록이 누적 보존되었습니다.",
        "execution": dict(saved_record)
    }), 201


@app.route("/api/execution/<int:execution_id>", methods=["DELETE"])
@login_required
def delete_execution_record(execution_id):
    user_id = session["user_id"]
    conn = get_db()
    # 소유권 확인
    exec_row = conn.execute("""
        SELECT e.id, p.user_id
        FROM execution_records e
        JOIN plans p ON e.plan_id = p.id
        WHERE e.id = ?
    """, (execution_id,)).fetchone()

    if not exec_row or exec_row["user_id"] != user_id:
        conn.close()
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    conn.execute("DELETE FROM execution_records WHERE id = ?", (execution_id,))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "실행 기록이 삭제되었습니다."
    })


# ==============================================================================
# 돌아보기(See) 엔드포인트 (사용자별 격리)
# ==============================================================================

@app.route("/api/see", methods=["GET"])
@login_required
def get_see_data():
    user_id = session["user_id"]
    conn = get_db()

    # 현재 로그인된 사용자의 계획만 조회
    plans_cursor = conn.execute("SELECT * FROM plans WHERE user_id = ? ORDER BY id ASC", (user_id,))
    plans = [dict(row) for row in plans_cursor.fetchall()]

    # 현재 사용자의 계획에 종속된 실행 기록만 조회
    records_cursor = conn.execute("""
        SELECT e.*, p.title AS plan_title
        FROM execution_records e
        JOIN plans p ON e.plan_id = p.id
        WHERE p.user_id = ?
        ORDER BY e.start_time ASC, e.id ASC
    """, (user_id,))
    execution_records = [dict(row) for row in records_cursor.fetchall()]

    # 현재 사용자의 next_actions만 조회
    next_actions_cursor = conn.execute("""
        SELECT * FROM next_actions
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))
    next_actions = [dict(row) for row in next_actions_cursor.fetchall()]

    today_str = get_kst_today_str()

    total_plans = len(plans)
    completed_plans = 0
    delayed_plans = 0
    blocked_plans = 0

    total_expected_minutes = 0
    total_actual_minutes = 0

    blocked_plan_ids = set()
    for rec in execution_records:
        total_actual_minutes += rec.get("actual_minutes", 0)
        reason = rec.get("blocker_reason", "").strip()
        if reason:
            blocked_plan_ids.add(rec["plan_id"])

    blocked_plans = len(blocked_plan_ids)

    plan_stats = []
    for p in plans:
        pid = p["id"]
        exp_min = p["current_expected_minutes"]
        total_expected_minutes += exp_min

        p_execs = [r for r in execution_records if r["plan_id"] == pid]
        act_min = sum(r["actual_minutes"] for r in p_execs)

        is_completed = (p["status"] == "완료")
        if is_completed:
            completed_plans += 1

        end_date = p["current_end_date"]
        is_delayed = bool(not is_completed and end_date and end_date < today_str)
        if is_delayed:
            delayed_plans += 1

        diff_min = act_min - exp_min
        plan_stats.append({
            "plan_id": pid,
            "title": p["title"],
            "priority": p["current_priority"],
            "status": p["status"],
            "is_delayed": is_delayed,
            "expected_minutes": exp_min,
            "actual_minutes": act_min,
            "diff_minutes": diff_min,
            "execution_count": len(p_execs)
        })

    time_diff_minutes = total_actual_minutes - total_expected_minutes
    completion_rate = round((completed_plans / total_plans * 100), 1) if total_plans > 0 else 0.0

    conn.close()

    return jsonify({
        "summary": {
            "total_plans": total_plans,
            "completed_plans": completed_plans,
            "delayed_plans": delayed_plans,
            "blocked_plans": blocked_plans,
            "completion_rate": completion_rate,
            "total_expected_minutes": total_expected_minutes,
            "total_actual_minutes": total_actual_minutes,
            "time_diff_minutes": time_diff_minutes
        },
        "plan_stats": plan_stats,
        "next_actions": next_actions
    })


@app.route("/api/see/next-action", methods=["POST"])
@login_required
def save_next_action():
    user_id = session["user_id"]
    data = request.get_json() or {}
    action_text = data.get("action_text", "").strip()
    source_type = data.get("source_type", "custom").strip()
    source_plan_id = data.get("source_plan_id")

    if not action_text:
        return jsonify({"success": False, "message": "고칠 점(Action Item) 내용을 입력해 주세요."}), 400

    now_kst = get_kst_now()
    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cursor = conn.execute("""
        INSERT INTO next_actions (user_id, action_text, source_type, source_plan_id, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, action_text, source_type, source_plan_id, now_str))

    new_id = cursor.lastrowid
    conn.commit()

    saved_row = conn.execute("SELECT * FROM next_actions WHERE id = ? AND user_id = ?", (new_id, user_id)).fetchone()
    conn.close()

    return jsonify({
        "success": True,
        "message": "고칠 점이 안전하게 저장되었습니다.",
        "next_action": dict(saved_row)
    }), 201


@app.route("/api/see/next-actions", methods=["GET"])
@login_required
def get_next_actions():
    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.execute("""
        SELECT * FROM next_actions
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))
    actions = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "next_actions": actions,
        "count": len(actions)
    })


@app.route("/api/plan/<int:plan_id>", methods=["DELETE"])
@login_required
def delete_plan(plan_id):
    user_id = session["user_id"]
    conn = get_db()
    if not check_plan_ownership(conn, plan_id, user_id):
        conn.close()
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    conn.execute("DELETE FROM plans WHERE id = ? AND user_id = ?", (plan_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "계획이 삭제되었습니다."
    })


# ==============================================================================
# 백업 및 내보내기 엔드포인트 (사용자별 격리)
# ==============================================================================

@app.route("/api/export", methods=["GET"])
@login_required
def export_all_data():
    user_id = session["user_id"]
    username = session["username"]
    conn = get_db()

    plans_cursor = conn.execute("SELECT * FROM plans WHERE user_id = ? ORDER BY id ASC", (user_id,))
    plans = [dict(r) for r in plans_cursor.fetchall()]

    plan_ids = [p["id"] for p in plans]
    if plan_ids:
        placeholders = ",".join("?" * len(plan_ids))
        history_cursor = conn.execute(f"SELECT * FROM plan_history WHERE plan_id IN ({placeholders}) ORDER BY id ASC", plan_ids)
        history = [dict(r) for r in history_cursor.fetchall()]

        exec_cursor = conn.execute(f"SELECT * FROM execution_records WHERE plan_id IN ({placeholders}) ORDER BY id ASC", plan_ids)
        executions = [dict(r) for r in exec_cursor.fetchall()]

        comp_cursor = conn.execute(f"SELECT * FROM completion_records WHERE plan_id IN ({placeholders}) ORDER BY id ASC", plan_ids)
        completions = [dict(r) for r in comp_cursor.fetchall()]

        tasks_cursor = conn.execute(f"SELECT * FROM plan_tasks WHERE plan_id IN ({placeholders}) ORDER BY id ASC", plan_ids)
        tasks = [dict(r) for r in tasks_cursor.fetchall()]
    else:
        history = []
        executions = []
        completions = []
        tasks = []

    next_actions_cursor = conn.execute("SELECT * FROM next_actions WHERE user_id = ? ORDER BY id ASC", (user_id,))
    next_actions = [dict(r) for r in next_actions_cursor.fetchall()]

    conn.close()

    now_kst = get_kst_now()
    timestamp_str = now_kst.strftime("%Y%m%d_%H%M%S")

    export_payload = {
        "metadata": {
            "system": "Plan-Do-See (PDS) Personal Task System",
            "version": "2.0.0 (Assignment 7 - Auth & Isolation)",
            "user": username,
            "exported_at": now_kst.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": "Asia/Seoul (KST, UTC+9)",
            "total_plans": len(plans),
            "total_tasks": len(tasks),
            "total_history": len(history),
            "total_executions": len(executions),
            "total_completions": len(completions),
            "total_next_actions": len(next_actions)
        },
        "plans": plans,
        "plan_tasks": tasks,
        "plan_history": history,
        "execution_records": executions,
        "completion_records": completions,
        "next_actions": next_actions
    }

    json_str = json.dumps(export_payload, ensure_ascii=False, indent=2)
    filename = f"pds_backup_{username}_{timestamp_str}.json"

    response = Response(json_str, mimetype="application/json; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


if __name__ == "__main__":
    init_db()

    print("=" * 60)
    print("플랜두씨 다이어리 2 (Plan-Do-See) - 인증 & 격리 서버 시작")
    print("기본 관리자 계정 (과제 6 샘플 데이터 연동): admin / admin1234!")
    print("접속 주소: http://127.0.0.1:5000")
    print("=" * 60)

    app.run(debug=True, port=5000)
