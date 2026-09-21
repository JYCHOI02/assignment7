from flask import Flask, render_template, request, jsonify, Response
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

DATABASE = "database.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

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

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
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
            modified_at TEXT NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE
        )
    """)

    # 실행 기록(Do) 보존을 위한 별도 테이블 생성
    # 시작/끝 시각, 실제 걸린 시간, 막혔던 이유를 저장하며 이전 기록이 사라지지 않고 누적 보존됨
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
    # 완료 버튼을 여러 번 눌러도 완료 기록은 1회만 보존됨
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
            action_text TEXT NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'custom',
            source_plan_id INTEGER,
            created_at TEXT NOT NULL,
            applied_at TEXT
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

    # 기존 데이터베이스 테이블 호환성 유지 (컬럼이 없을 경우 추가)
    cursor = conn.execute("PRAGMA table_info(plans)")
    columns = [row["name"] for row in cursor.fetchall()]

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

    # plan_history 테이블 컬럼 호환성 유지
    cursor_hist = conn.execute("PRAGMA table_info(plan_history)")
    hist_cols = [row["name"] for row in cursor_hist.fetchall()]
    if "tags" not in hist_cols:
        conn.execute("ALTER TABLE plan_history ADD COLUMN tags TEXT NOT NULL DEFAULT ''")

    # 기존 '높음', '보통', '낮음' 우선순위를 '1순위', '2순위'... 형식으로 마이그레이션
    cursor = conn.execute("SELECT id, original_priority, current_priority FROM plans ORDER BY id ASC")
    rows = cursor.fetchall()
    for idx, row in enumerate(rows, start=1):
        orig_p = row["original_priority"]
        curr_p = row["current_priority"]
        updates = []
        params = []
        if orig_p in ["높음", "보통", "낮음"]:
            updates.append("original_priority = ?")
            params.append(f"{idx}순위")
        if curr_p in ["높음", "보통", "낮음"]:
            updates.append("current_priority = ?")
            params.append(f"{idx}순위")
        if updates:
            params.append(row["id"])
            conn.execute(f"UPDATE plans SET {', '.join(updates)} WHERE id = ?", params)

    # 기존 데이터 중 수정된 이력이 있으나 plan_history가 비어있는 경우 마이그레이션
    hist_cnt_row = conn.execute("SELECT COUNT(*) AS cnt FROM plan_history").fetchone()
    if hist_cnt_row and hist_cnt_row["cnt"] == 0:
        for row in rows:
            plan_row = conn.execute("SELECT * FROM plans WHERE id = ?", (row["id"],)).fetchone()
            if plan_row and (plan_row["updated_at"] != plan_row["created_at"] or (plan_row["original_title"] and plan_row["original_title"] != plan_row["title"])):
                conn.execute("""
                    INSERT INTO plan_history (
                        plan_id, version, title, priority,
                        start_date, end_date, success_criteria,
                        expected_minutes, status, modified_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    plan_row["id"],
                    1,
                    plan_row["original_title"] or plan_row["title"],
                    plan_row["original_priority"] or plan_row["current_priority"],
                    plan_row["original_start_date"] or plan_row["current_start_date"],
                    plan_row["original_end_date"] or plan_row["current_end_date"],
                    plan_row["original_success_criteria"] or plan_row["current_success_criteria"],
                    plan_row["original_expected_minutes"] or plan_row["current_expected_minutes"],
                    plan_row["status"],
                    plan_row["updated_at"]
                ))

    # 최초 실행 시 첫 번째 계획에 5개 이상의 딸린 할 일이 들어있도록 시드 데이터 구성
    # ("그 계획에 딸린 할 일이 다섯 개 이상 들어 있다" 검증 요구사항 충족)
    task_cnt_row = conn.execute("SELECT COUNT(*) AS cnt FROM plan_tasks").fetchone()
    if task_cnt_row and task_cnt_row["cnt"] == 0:
        first_plan = conn.execute("SELECT id, title, current_end_date FROM plans ORDER BY id ASC LIMIT 1").fetchone()
        if first_plan:
            now_str = get_kst_now().strftime("%Y-%m-%d %H:%M:%S")
            due_str = first_plan["current_end_date"] or get_kst_today_str()
            sample_subtasks = [
                ("준비 운동 및 전신 스트레칭 (10분)", 1),
                ("기초 체력 루틴 세트 수행", 1),
                ("집중 트레이닝 및 코어 단련", 0),
                ("유산소 인터벌 25분 달리기", 0),
                ("마무리 쿨다운 및 수분 보충", 0)
            ]
            for o_idx, (t_title, t_done) in enumerate(sample_subtasks, start=1):
                conn.execute("""
                    INSERT INTO plan_tasks (plan_id, title, is_completed, due_date, order_num, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (first_plan["id"], t_title, t_done, due_str, o_idx, now_str, now_str))

    conn.commit()
    conn.close()


@app.route("/")
def index():
    return render_template("index.html")


# 모든 저장된 계획 목록 가져오기 (검색, 필터링, 정렬 지원)
@app.route("/api/plans", methods=["GET"])
def get_plans():
    query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    tag_filter = request.args.get("tag", "").strip()
    sort_by = request.args.get("sort", "priority-asc").strip()

    conn = get_db()

    sql = """
        SELECT p.*,
               (SELECT COUNT(*) FROM plan_history h WHERE h.plan_id = p.id) AS history_count,
               (SELECT COUNT(*) FROM execution_records e WHERE e.plan_id = p.id) AS execution_count,
               (SELECT COALESCE(SUM(actual_minutes), 0) FROM execution_records e WHERE e.plan_id = p.id) AS actual_minutes_sum,
               (SELECT completed_at FROM completion_records c WHERE c.plan_id = p.id) AS completed_at,
               (SELECT COUNT(*) FROM plan_tasks t WHERE t.plan_id = p.id) AS task_count,
               (SELECT COUNT(*) FROM plan_tasks t WHERE t.plan_id = p.id AND t.is_completed = 1) AS completed_task_count
        FROM plans p
        WHERE 1=1
    """
    params = []

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
        # [T06-C30] 완료되지 않았고 마감일이 서울 시간 기준 오늘보다 앞선 할 일만 지연으로 판정
        d["is_delayed"] = bool(not is_comp and p_end and p_end < today_str)
        plans.append(d)

    conn.close()

    return jsonify({
        "plans": plans,
        "count": len(plans)
    })


# 특정 계획 또는 최신 계획 가져오기
@app.route("/api/plan", methods=["GET"])
def get_plan():
    plan_id = request.args.get("id")
    conn = get_db()

    if plan_id:
        try:
            plan = conn.execute("SELECT * FROM plans WHERE id = ?", (int(plan_id),)).fetchone()
        except (ValueError, TypeError):
            plan = None
    else:
        plan = conn.execute("""
            SELECT *
            FROM plans
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()

    if plan is None:
        conn.close()
        return jsonify({
            "exists": False
        })

    plan_dict = dict(plan)

    # 수정 이력(plan_history)도 함께 반환
    hist_cursor = conn.execute("""
        SELECT *
        FROM plan_history
        WHERE plan_id = ?
        ORDER BY version DESC, id DESC
    """, (plan_dict["id"],))
    history = [dict(row) for row in hist_cursor.fetchall()]

    # 실행 기록(execution_records)도 함께 반환
    exec_cursor = conn.execute("""
        SELECT *
        FROM execution_records
        WHERE plan_id = ?
        ORDER BY id DESC
    """, (plan_dict["id"],))
    executions = [dict(row) for row in exec_cursor.fetchall()]

    # 단일 완료 기록 조회
    comp_row = conn.execute("SELECT completed_at FROM completion_records WHERE plan_id = ?", (plan_dict["id"],)).fetchone()
    completed_at = comp_row["completed_at"] if comp_row else None

    conn.close()

    return jsonify({
        "exists": True,
        "plan": plan_dict,
        "history": history,
        "executions": executions,
        "execution_count": len(executions),
        "total_actual_minutes": sum(e["actual_minutes"] for e in executions),
        "completed_at": completed_at
    })


# 최초 계획 저장
@app.route("/api/plan", methods=["POST"])
def create_plan():
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

    # 입력 검증
    if not title:
        return jsonify({
            "success": False,
            "message": "계획을 입력해주세요."
        }), 400

    if not start_date or not end_date:
        return jsonify({
            "success": False,
            "message": "기간을 입력해주세요."
        }), 400

    if start_date > end_date:
        return jsonify({
            "success": False,
            "message": "시작일은 종료일보다 늦을 수 없습니다."
        }), 400

    if not success_criteria:
        return jsonify({
            "success": False,
            "message": "성공 기준을 입력해주세요."
        }), 400

    if expected_minutes <= 0:
        return jsonify({
            "success": False,
            "message": "예상 시간은 1분 이상 입력해주세요."
        }), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tags = data.get("tags", "").strip()

    conn = get_db()

    # 우선순위가 비어있거나 '보통'/'높음'/'낮음'인 경우 다음 순위로 자동 배정
    if not priority or priority in ["높음", "보통", "낮음"]:
        cnt_row = conn.execute("SELECT COUNT(*) AS cnt FROM plans").fetchone()
        count = cnt_row["cnt"] if cnt_row else 0
        priority = f"{count + 1}순위"

    # 최초 계획과 현재 계획을 같은 값으로 저장
    cursor = conn.execute("""
        INSERT INTO plans (
            title, 
            tags,
            original_title,

            original_priority,
            original_start_date,
            original_end_date,
            original_success_criteria,
            original_expected_minutes,

            current_priority,
            current_start_date,
            current_end_date,
            current_success_criteria,
            current_expected_minutes,

            status,

            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        tags,
        title,

        priority,
        start_date,
        end_date,
        success_criteria,
        expected_minutes,

        priority,
        start_date,
        end_date,
        success_criteria,
        expected_minutes,

        "진행중",

        now,
        now
    ))

    conn.commit()

    plan_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "success": True,
        "message": "계획이 저장되었습니다.",
        "plan_id": plan_id
    })


# 현재 계획 수정
@app.route("/api/plan", methods=["PUT"])
def update_plan():
    data = request.get_json()

    try:
        plan_id = int(data.get("id"))
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "잘못된 계획입니다."
        }), 400

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
        return jsonify({
            "success": False,
            "message": "계획을 입력해주세요."
        }), 400

    if not start_date or not end_date:
        return jsonify({
            "success": False,
            "message": "기간을 입력해주세요."
        }), 400

    if start_date > end_date:
        return jsonify({
            "success": False,
            "message": "시작일은 종료일보다 늦을 수 없습니다."
        }), 400

    if not success_criteria:
        return jsonify({
            "success": False,
            "message": "성공 기준을 입력하세요."
        }), 400

    if expected_minutes <= 0:
        return jsonify({
            "success": False,
            "message": "예상 시간은 1분 이상 입력해주세요."
        }), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tags = data.get("tags", "").strip()

    conn = get_db()

    # 기존 계획 조회 (수정 전 상태)
    existing = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({
            "success": False,
            "message": "계획을 찾을 수 없습니다."
        }), 404

    # 우선순위가 비어있거나 구버전 값인 경우 기존 우선순위 유지
    if not priority or priority in ["높음", "보통", "낮음"]:
        if existing["current_priority"]:
            priority = existing["current_priority"]
        else:
            priority = "1순위"

    # [T06-C08] 계획을 고쳐도 고치기 전 계획이 그대로 남아 있다.
    # 수정 전 계획 상태를 별도 표(plan_history)에 분리 저장하고, 계획 ID는 유지
    ver_cursor = conn.execute("SELECT COUNT(*) AS cnt FROM plan_history WHERE plan_id = ?", (plan_id,))
    ver_count = ver_cursor.fetchone()["cnt"]
    next_ver = ver_count + 1

    existing_tags = existing["tags"] if "tags" in existing.keys() else ""

    conn.execute("""
        INSERT INTO plan_history (
            plan_id,
            version,
            title,
            tags,
            priority,
            start_date,
            end_date,
            success_criteria,
            expected_minutes,
            status,
            modified_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        plan_id,
        next_ver,
        existing["title"],
        existing_tags,
        existing["current_priority"],
        existing["current_start_date"],
        existing["current_end_date"],
        existing["current_success_criteria"],
        existing["current_expected_minutes"],
        existing["status"],
        now
    ))

    result = conn.execute("""
        UPDATE plans
        SET
            title = ?,
            tags = ?,
            current_priority = ?,
            current_start_date = ?,
            current_end_date = ?,
            current_success_criteria = ?,
            current_expected_minutes = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        title,
        tags,
        priority,
        start_date,
        end_date,
        success_criteria,
        expected_minutes,
        now,
        plan_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "계획이 수정되었습니다. 수정 전 계획은 이력 표에 보존됩니다."
    })


# 특정 계획의 수정 이력 목록 가져오기 (T06-C08)
@app.route("/api/plan/<int:plan_id>/history", methods=["GET"])
def get_plan_history(plan_id):
    conn = get_db()
    cursor = conn.execute("""
        SELECT *
        FROM plan_history
        WHERE plan_id = ?
        ORDER BY version DESC, id DESC
    """, (plan_id,))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "success": True,
        "plan_id": plan_id,
        "history": history,
        "count": len(history)
    })


# 특정 수정 이력으로 계획 복원하기
@app.route("/api/plan/<int:plan_id>/history/<int:history_id>/restore", methods=["POST"])
def restore_plan_history(plan_id, history_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()

    target_history = conn.execute(
        "SELECT * FROM plan_history WHERE id = ? AND plan_id = ?",
        (history_id, plan_id)
    ).fetchone()

    if not target_history:
        conn.close()
        return jsonify({"success": False, "message": "해당 수정 이력을 찾을 수 없습니다."}), 404

    current = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if not current:
        conn.close()
        return jsonify({"success": False, "message": "계획을 찾을 수 없습니다."}), 404

    # 복원 전 현재 상태도 이력에 추가 보존
    ver_cursor = conn.execute("SELECT COUNT(*) AS cnt FROM plan_history WHERE plan_id = ?", (plan_id,))
    ver_count = ver_cursor.fetchone()["cnt"]
    next_ver = ver_count + 1

    current_tags = current["tags"] if "tags" in current.keys() else ""
    target_tags = target_history["tags"] if "tags" in target_history.keys() else ""

    conn.execute("""
        INSERT INTO plan_history (
            plan_id, version, title, tags, priority,
            start_date, end_date, success_criteria,
            expected_minutes, status, modified_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        plan_id, next_ver,
        current["title"], current_tags, current["current_priority"],
        current["current_start_date"], current["current_end_date"],
        current["current_success_criteria"], current["current_expected_minutes"],
        current["status"], now
    ))

    # 대상 이력 데이터로 plans 테이블 복원
    conn.execute("""
        UPDATE plans
        SET
            title = ?,
            tags = ?,
            current_priority = ?,
            current_start_date = ?,
            current_end_date = ?,
            current_success_criteria = ?,
            current_expected_minutes = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        target_history["title"],
        target_tags,
        target_history["priority"],
        target_history["start_date"],
        target_history["end_date"],
        target_history["success_criteria"],
        target_history["expected_minutes"],
        now,
        plan_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"'{target_history['title']}'(v{target_history['version']}) 버전으로 계획이 복원되었습니다."
    })


# 계획 우선순위 일괄 변경 (드래그 앤 드롭 슬라이드 재정렬)
@app.route("/api/plans/reorder", methods=["PUT"])
def reorder_plans():
    data = request.get_json()
    order = data.get("order", [])

    if not isinstance(order, list) or len(order) == 0:
        return jsonify({
            "success": False,
            "message": "순서 데이터가 올바르지 않습니다."
        }), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()

    # original_priority는 건드리지 않고 current_priority만 1순위, 2순위...로 변경하여 T06-C08 준수
    for rank, plan_id in enumerate(order, start=1):
        priority_str = f"{rank}순위"
        conn.execute("""
            UPDATE plans
            SET current_priority = ?, updated_at = ?
            WHERE id = ?
        """, (priority_str, now, int(plan_id)))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "우선순위가 성공적으로 변경되었습니다."
    })


# 계획 상태 변경 (진행중 <-> 완료)
# 완료로 변경 시 우선순위 맨 아래로 이동
# [요구사항 4 & 5] 완료 버튼을 2번 눌러도 완료 기록은 1번만 남고 돌아보기 완료 수도 1만 증가하도록 단일성 및 멱등성 보장
@app.route("/api/plan/<int:plan_id>/status", methods=["PUT", "POST"])
def update_plan_status(plan_id):
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")

    conn = get_db()
    current = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if not current:
        conn.close()
        return jsonify({"success": False, "message": "계획을 찾을 수 없습니다."}), 404

    # 상태 지정이 없으면 토글
    if not new_status:
        new_status = "완료" if current["status"] != "완료" else "진행중"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # [요구사항 4 & 5] 이미 완료된 상태에서 다시 '완료' 요청이 들어온 경우 (중복 클릭 방어)
    if current["status"] == "완료" and new_status == "완료":
        # completion_records에 이미 1건만 존재함을 보장하고 그대로 반환
        conn.execute("""
            INSERT OR IGNORE INTO completion_records (plan_id, completed_at)
            VALUES (?, ?)
        """, (plan_id, now))
        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "message": "이미 완료 처리된 계획입니다. 완료 기록은 1건으로 유지됩니다.",
            "status": "완료",
            "already_completed": True
        })

    if new_status == "완료":
        # 완료 기록 단일 삽입 (UNIQUE 제약으로 1건만 보존)
        conn.execute("""
            INSERT OR IGNORE INTO completion_records (plan_id, completed_at)
            VALUES (?, ?)
        """, (plan_id, now))
    else:
        # 진행중으로 복귀 시 completion_records에서 삭제하여 정합성 유지
        conn.execute("DELETE FROM completion_records WHERE plan_id = ?", (plan_id,))

    # 전체 계획 ID를 현재 우선순위 순서대로 조회
    cursor = conn.execute("""
        SELECT id, status
        FROM plans
        ORDER BY
            CASE
                WHEN current_priority LIKE '%순위' THEN CAST(REPLACE(current_priority, '순위', '') AS INTEGER)
                ELSE 999999
            END ASC,
            id DESC
    """)
    all_rows = [dict(r) for r in cursor.fetchall()]

    plan_ids = [r["id"] for r in all_rows]
    if plan_id in plan_ids:
        plan_ids.remove(plan_id)

    if new_status == "완료":
        # 완료 상태로 변경되면 맨 아래로 이동
        plan_ids.append(plan_id)
    else:
        # 다시 진행중으로 바뀌면, 완료된 계획들 바로 앞으로 복귀
        completed_ids = [r["id"] for r in all_rows if r["id"] != plan_id and r["status"] == "완료"]
        if completed_ids:
            first_completed_idx = next((i for i, pid in enumerate(plan_ids) if pid in completed_ids), len(plan_ids))
            plan_ids.insert(first_completed_idx, plan_id)
        else:
            plan_ids.append(plan_id)

    # 모든 계획의 current_priority를 재할당 (1순위, 2순위, ...)
    for rank, pid in enumerate(plan_ids, start=1):
        if pid == plan_id:
            conn.execute("""
                UPDATE plans
                SET current_priority = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (f"{rank}순위", new_status, now, pid))
        else:
            conn.execute("""
                UPDATE plans
                SET current_priority = ?, updated_at = ?
                WHERE id = ?
            """, (f"{rank}순위", now, pid))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"계획이 '{new_status}' 상태로 변경되었습니다.",
        "status": new_status
    })


# ==========================================================
# 📌 계획에 딸린 세부 할 일 (Subtasks / Plan Tasks) CRUD API
# ==========================================================

# 1. 특정 계획의 딸린 할 일 목록 조회
@app.route("/api/plan/<int:plan_id>/tasks", methods=["GET"])
def get_plan_tasks(plan_id):
    conn = get_db()
    cursor = conn.execute("""
        SELECT *
        FROM plan_tasks
        WHERE plan_id = ?
        ORDER BY order_num ASC, id ASC
    """, (plan_id,))
    tasks = [dict(row) for row in cursor.fetchall()]
    total_count = len(tasks)
    completed_count = sum(1 for t in tasks if t.get("is_completed") == 1)
    conn.close()

    return jsonify({
        "success": True,
        "tasks": tasks,
        "total_count": total_count,
        "completed_count": completed_count
    })


# 2. 특정 계획에 새로운 딸린 할 일 추가
@app.route("/api/plan/<int:plan_id>/tasks", methods=["POST"])
def add_plan_task(plan_id):
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    due_date = (data.get("due_date") or "").strip()

    if not title:
        return jsonify({"success": False, "message": "할 일 내용을 입력해주세요."}), 400

    conn = get_db()
    plan = conn.execute("SELECT id FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if not plan:
        conn.close()
        return jsonify({"success": False, "message": "계획을 찾을 수 없습니다."}), 404

    now_str = get_kst_now().strftime("%Y-%m-%d %H:%M:%S")
    max_order_row = conn.execute("SELECT MAX(order_num) AS max_o FROM plan_tasks WHERE plan_id = ?", (plan_id,)).fetchone()
    next_order = (max_order_row["max_o"] or 0) + 1

    cursor = conn.execute("""
        INSERT INTO plan_tasks (plan_id, title, is_completed, due_date, order_num, created_at, updated_at)
        VALUES (?, ?, 0, ?, ?, ?, ?)
    """, (plan_id, title, due_date, next_order, now_str, now_str))
    task_id = cursor.lastrowid

    # 부모 계획 updated_at 갱신
    conn.execute("UPDATE plans SET updated_at = ? WHERE id = ?", (now_str, plan_id))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "세부 할 일이 추가되었습니다.",
        "task_id": task_id
    })


# 3. 특정 딸린 할 일 수정 (내용, 완료 여부, 마감일 등)
@app.route("/api/plan/<int:plan_id>/task/<int:task_id>", methods=["PUT"])
def update_plan_task(plan_id, task_id):
    data = request.get_json(silent=True) or {}
    conn = get_db()
    task = conn.execute("SELECT * FROM plan_tasks WHERE id = ? AND plan_id = ?", (task_id, plan_id)).fetchone()
    if not task:
        conn.close()
        return jsonify({"success": False, "message": "할 일을 찾을 수 없습니다."}), 404

    title = data.get("title")
    if title is not None:
        title = str(title).strip()
        if not title:
            conn.close()
            return jsonify({"success": False, "message": "할 일 내용을 비워둘 수 없습니다."}), 400
    else:
        title = task["title"]

    is_completed = data.get("is_completed")
    if is_completed is not None:
        is_completed = 1 if is_completed in [1, True, "1", "true"] else 0
    else:
        is_completed = task["is_completed"]

    due_date = data.get("due_date")
    if due_date is not None:
        due_date = str(due_date).strip()
    else:
        due_date = task["due_date"]

    now_str = get_kst_now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        UPDATE plan_tasks
        SET title = ?, is_completed = ?, due_date = ?, updated_at = ?
        WHERE id = ? AND plan_id = ?
    """, (title, is_completed, due_date, now_str, task_id, plan_id))

    conn.execute("UPDATE plans SET updated_at = ? WHERE id = ?", (now_str, plan_id))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "할 일이 수정되었습니다."
    })


# 4. 특정 딸린 할 일 삭제
@app.route("/api/plan/<int:plan_id>/task/<int:task_id>", methods=["DELETE"])
def delete_plan_task(plan_id, task_id):
    conn = get_db()
    result = conn.execute("DELETE FROM plan_tasks WHERE id = ? AND plan_id = ?", (task_id, plan_id))
    deleted = result.rowcount > 0
    if deleted:
        now_str = get_kst_now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("UPDATE plans SET updated_at = ? WHERE id = ?", (now_str, plan_id))
    conn.commit()
    conn.close()

    if not deleted:
        return jsonify({"success": False, "message": "삭제할 할 일을 찾을 수 없습니다."}), 404

    return jsonify({
        "success": True,
        "message": "할 일이 삭제되었습니다."
    })


# 특정 계획의 모든 실행 기록 가져오기
@app.route("/api/plan/<int:plan_id>/executions", methods=["GET"])
def get_plan_executions(plan_id):
    conn = get_db()
    cursor = conn.execute("""
        SELECT *
        FROM execution_records
        WHERE plan_id = ?
        ORDER BY id DESC
    """, (plan_id,))
    executions = [dict(row) for row in cursor.fetchall()]
    total_actual = sum(e["actual_minutes"] for e in executions)
    conn.close()

    return jsonify({
        "success": True,
        "plan_id": plan_id,
        "executions": executions,
        "count": len(executions),
        "total_actual_minutes": total_actual
    })


# 실행 기록(Do) 저장
# [요구사항 1, 2, 3] 시작/끝 시각, 실제 걸린 시간, 막혔던 이유 저장 및 이전 기록 누적 보존
@app.route("/api/plan/<int:plan_id>/execution", methods=["POST"])
def add_execution_record(plan_id):
    data = request.get_json() or {}

    start_time = data.get("start_time", "").strip()
    end_time = data.get("end_time", "").strip()
    blocker_reason = data.get("blocker_reason", "").strip()
    memo = data.get("memo", "").strip()
    mark_completed = bool(data.get("mark_completed", False))
    confirm_overlap = bool(data.get("confirm_overlap", False))

    try:
        actual_minutes = int(data.get("actual_minutes", 0))
    except (ValueError, TypeError):
        actual_minutes = 0

    if not start_time or not end_time:
        return jsonify({
            "success": False,
            "message": "실행 시작 시각과 끝 시각을 모두 입력해주세요."
        }), 400

    if start_time > end_time:
        return jsonify({
            "success": False,
            "message": "시작 시각은 끝 시각보다 늦을 수 없습니다."
        }), 400

    if actual_minutes <= 0:
        return jsonify({
            "success": False,
            "message": "실제로 걸린 시간을 1분 이상 입력해주세요."
        }), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    plan = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if not plan:
        conn.close()
        return jsonify({
            "success": False,
            "message": "계획을 찾을 수 없습니다."
        }), 404

    # 1. 완전 중복 저장 방지: 동일한 계획(plan_id)에 같은 시작 시각과 끝 시각을 가진 실행 기록이 이미 존재하는지 검사
    existing_exec = conn.execute("""
        SELECT id FROM execution_records
        WHERE plan_id = ? AND start_time = ? AND end_time = ?
    """, (plan_id, start_time, end_time)).fetchone()

    if existing_exec:
        conn.close()
        return jsonify({
            "success": False,
            "duplicate": True,
            "message": "동일한 시작 시각과 끝 시각을 가진 실행 기록이 이미 등록되어 있습니다. 중복으로 저장할 수 없습니다."
        }), 409

    # 2. [옵션 B] 시간대 겹침 검사 (confirm_overlap이 False일 때 겹치는 내역 반환하여 확인 창 유도)
    if not confirm_overlap:
        overlap_rows = conn.execute("""
            SELECT e.id, e.plan_id, e.start_time, e.end_time, e.actual_minutes, p.title AS plan_title
            FROM execution_records e
            JOIN plans p ON e.plan_id = p.id
            WHERE e.start_time < ? AND e.end_time > ?
            ORDER BY e.start_time ASC
        """, (end_time, start_time)).fetchall()

        if overlap_rows:
            overlaps = [dict(r) for r in overlap_rows]
            conn.close()
            return jsonify({
                "success": False,
                "overlap": True,
                "overlaps": overlaps,
                "message": "입력하신 시간이 기존 실행 기록과 일부 겹칩니다."
            }), 409

    try:
        # [요구사항 3] 실행 기록을 저장해도 이전의 기록이 사라지지 않게 항상 신규 INSERT로 누적 보존
        cursor = conn.execute("""
            INSERT INTO execution_records (
                plan_id, start_time, end_time, actual_minutes, blocker_reason, memo, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (plan_id, start_time, end_time, actual_minutes, blocker_reason, memo, now))
        execution_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({
            "success": False,
            "duplicate": True,
            "message": "동일한 시작 시각과 끝 시각을 가진 실행 기록이 이미 등록되어 있습니다. 중복으로 저장할 수 없습니다."
        }), 409

    # [요구사항 4 & 5] 실행과 함께 완료 처리 요청된 경우 단일성 보장
    if mark_completed:
        conn.execute("""
            INSERT OR IGNORE INTO completion_records (plan_id, completed_at)
            VALUES (?, ?)
        """, (plan_id, now))

        if plan["status"] != "완료":
            # 완료 시 맨 아래 순위로 이동
            cursor_p = conn.execute("""
                SELECT id FROM plans WHERE id != ?
                ORDER BY
                    CASE
                        WHEN current_priority LIKE '%순위' THEN CAST(REPLACE(current_priority, '순위', '') AS INTEGER)
                        ELSE 999999
                    END ASC
            """, (plan_id,))
            other_ids = [r["id"] for r in cursor_p.fetchall()]
            other_ids.append(plan_id)

            for rank, pid in enumerate(other_ids, start=1):
                if pid == plan_id:
                    conn.execute("""
                        UPDATE plans
                        SET current_priority = ?, status = '완료', updated_at = ?
                        WHERE id = ?
                    """, (f"{rank}순위", now, pid))
                else:
                    conn.execute("""
                        UPDATE plans
                        SET current_priority = ?, updated_at = ?
                        WHERE id = ?
                    """, (f"{rank}순위", now, pid))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "실행 기록이 안전하게 저장되었습니다. 이전 실행 기록도 모두 보존됩니다.",
        "execution_id": execution_id
    })


# 실행 기록 개별 삭제
@app.route("/api/execution/<int:execution_id>", methods=["DELETE"])
def delete_execution_record(execution_id):
    conn = get_db()
    conn.execute("DELETE FROM execution_records WHERE id = ?", (execution_id,))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "해당 실행 기록이 삭제되었습니다."
    })


# 돌아보기 (See) 대시보드 통계 및 분석 데이터
# [기간별 집계, 지표 확장(계획·완료·지연·막힘, 예상·실제 시간), 근거 추적 지원]
@app.route("/api/see", methods=["GET"])
def get_see_data():
    period = request.args.get("period", "all").strip().lower()
    now = get_kst_now()
    today_str = get_kst_today_str()

    start_date = None
    end_date = None
    range_label = "전체 기간"

    if period == "today":
        start_date = today_str
        end_date = today_str
        range_label = f"오늘 ({today_str})"
    elif period == "week":
        monday = now.date() - timedelta(days=now.weekday())
        sunday = monday + timedelta(days=6)
        start_date = monday.strftime("%Y-%m-%d")
        end_date = sunday.strftime("%Y-%m-%d")
        range_label = f"이번 주 ({start_date} ~ {end_date})"
    elif period == "month":
        _, last_day = calendar.monthrange(now.year, now.month)
        start_date = f"{now.year:04d}-{now.month:02d}-01"
        end_date = f"{now.year:04d}-{now.month:02d}-{last_day:02d}"
        range_label = f"이번 달 ({now.year}년 {now.month}월)"
    else:
        period = "all"
        range_label = "전체 기간"

    conn = get_db()

    # 모든 계획 및 연관 요약 정보 가져오기
    summary_cursor = conn.execute("""
        SELECT
            p.id, p.title, p.current_priority, p.status,
            p.current_start_date, p.current_end_date,
            p.created_at, p.updated_at,
            p.original_expected_minutes, p.current_expected_minutes,
            c.completed_at,
            (SELECT COUNT(*) FROM execution_records e WHERE e.plan_id = p.id) AS execution_count,
            (SELECT COALESCE(SUM(actual_minutes), 0) FROM execution_records e WHERE e.plan_id = p.id) AS actual_total_minutes,
            (SELECT COUNT(*) FROM execution_records e WHERE e.plan_id = p.id AND e.blocker_reason IS NOT NULL AND TRIM(e.blocker_reason) != '') AS blocker_count
        FROM plans p
        LEFT JOIN completion_records c ON p.id = c.plan_id
        ORDER BY
            CASE WHEN p.status = '완료' THEN 1 ELSE 0 END ASC,
            CASE
                WHEN p.current_priority LIKE '%순위' THEN CAST(REPLACE(p.current_priority, '순위', '') AS INTEGER)
                ELSE 999999
            END ASC,
            p.id DESC
    """)
    all_plans = [dict(r) for r in summary_cursor.fetchall()]

    # 기간 필터링 적용
    filtered_plans = []
    for p in all_plans:
        if period == "all":
            filtered_plans.append(p)
        else:
            p_start = p["current_start_date"]
            p_end = p["current_end_date"]
            p_created = (p["created_at"] or "")[:10]
            p_comp = (p["completed_at"] or "")[:10]

            is_in_period = False
            if p_start and p_end and (p_start <= end_date and p_end >= start_date):
                is_in_period = True
            elif p_created and (start_date <= p_created <= end_date):
                is_in_period = True
            elif p_comp and (start_date <= p_comp <= end_date):
                is_in_period = True

            if is_in_period:
                filtered_plans.append(p)

    # 지표 산출
    total_plans = len(filtered_plans)
    completed_plans = 0
    delayed_plans = 0
    blocked_plans = 0
    ongoing_plans = 0

    total_expected_minutes = 0
    total_actual_minutes = 0

    delayed_plan_ids = []
    completed_plan_ids = []
    ongoing_plan_ids = []
    blocked_plan_ids = []

    for p in filtered_plans:
        p_id = p["id"]
        is_comp = (p["status"] == "완료")
        p_end = p["current_end_date"]
        p_comp = (p["completed_at"] or "")[:10]
        has_blocker = (p["blocker_count"] > 0)

        # [T06-C30] 지연 판정: 완료되지 않았고 마감일이 서울 시간 기준 오늘보다 앞선 할 일 (완료한 할 일은 지연으로 두 번 세지 않음)
        is_delayed = bool(not is_comp and p_end and p_end < today_str)

        p["is_delayed"] = is_delayed
        p["has_blocker"] = has_blocker

        if is_comp:
            completed_plans += 1
            completed_plan_ids.append(p_id)
        else:
            ongoing_plans += 1
            ongoing_plan_ids.append(p_id)

        if is_delayed:
            delayed_plans += 1
            delayed_plan_ids.append(p_id)

        if has_blocker:
            blocked_plans += 1
            blocked_plan_ids.append(p_id)

        total_expected_minutes += int(p["current_expected_minutes"] or 0)
        total_actual_minutes += int(p["actual_total_minutes"] or 0)

    completion_rate = round((completed_plans / total_plans * 100), 1) if total_plans > 0 else 0

    # 막혔던 이유 모아보기
    plan_id_set = {p["id"] for p in filtered_plans}
    blockers_cursor = conn.execute("""
        SELECT e.id, e.plan_id, e.blocker_reason, e.actual_minutes, e.created_at, p.title AS plan_title
        FROM execution_records e
        JOIN plans p ON e.plan_id = p.id
        WHERE e.blocker_reason IS NOT NULL AND TRIM(e.blocker_reason) != ''
        ORDER BY e.id DESC
    """)
    all_blockers = [dict(r) for r in blockers_cursor.fetchall()]
    if period == "all":
        blockers = all_blockers
    else:
        blockers = [b for b in all_blockers if b["plan_id"] in plan_id_set or (start_date <= (b["created_at"] or "")[:10] <= end_date)]

    # 최근 다음 계획으로 넘긴 한 줄 목록
    recent_actions = []
    try:
        actions_cursor = conn.execute("""
            SELECT * FROM next_actions
            ORDER BY id DESC
            LIMIT 5
        """)
        recent_actions = [dict(r) for r in actions_cursor.fetchall()]
    except Exception:
        pass

    conn.close()

    return jsonify({
        "success": True,
        "period": period,
        "range_label": range_label,
        "start_date": start_date,
        "end_date": end_date,
        "total_plans": total_plans,
        "completed_count": completed_plans,
        "delayed_count": delayed_plans,
        "blocked_count": blocked_plans,
        "ongoing_count": ongoing_plans,
        "completion_rate": completion_rate,
        "total_expected_minutes": total_expected_minutes,
        "total_actual_minutes": total_actual_minutes,
        "time_difference": total_actual_minutes - total_expected_minutes,
        "total_executions": sum(p["execution_count"] for p in filtered_plans),
        "delayed_plan_ids": delayed_plan_ids,
        "completed_plan_ids": completed_plan_ids,
        "ongoing_plan_ids": ongoing_plan_ids,
        "blocked_plan_ids": blocked_plan_ids,
        "blockers": blockers,
        "plan_do_summaries": filtered_plans,
        "recent_actions": recent_actions
    })


# 돌아보기에서 다음 계획으로 넘길 한 줄 저장
@app.route("/api/see/next-action", methods=["POST"])
def save_next_action():
    data = request.get_json() or {}
    action_text = data.get("action_text", "").strip()
    source_type = data.get("source_type", "custom").strip()
    source_plan_id = data.get("source_plan_id")

    if not action_text:
        return jsonify({"success": False, "message": "고칠 점(개선할 내용)을 입력해주세요."}), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    cursor = conn.execute("""
        INSERT INTO next_actions (action_text, source_type, source_plan_id, created_at, applied_at)
        VALUES (?, ?, ?, ?, ?)
    """, (action_text, source_type, source_plan_id, now, now))
    action_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "고칠 점이 다음 계획으로 성공적으로 전달되었습니다.",
        "action_id": action_id,
        "action_text": action_text
    })


# 돌아보기 다음 계획 액션 아이템 목록 조회
@app.route("/api/see/next-actions", methods=["GET"])
def get_next_actions():
    conn = get_db()
    cursor = conn.execute("SELECT * FROM next_actions ORDER BY id DESC LIMIT 10")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "actions": rows})


# 계획 삭제 (해당 계획의 수정 이력, 실행 기록, 완료 기록, 세부 할 일도 함께 삭제)
@app.route("/api/plan/<int:plan_id>", methods=["DELETE"])
def delete_plan(plan_id):
    conn = get_db()
    conn.execute("DELETE FROM plan_history WHERE plan_id = ?", (plan_id,))
    conn.execute("DELETE FROM execution_records WHERE plan_id = ?", (plan_id,))
    conn.execute("DELETE FROM completion_records WHERE plan_id = ?", (plan_id,))
    conn.execute("DELETE FROM plan_tasks WHERE plan_id = ?", (plan_id,))
    result = conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
    conn.commit()
    deleted = result.rowcount > 0
    conn.close()

    if not deleted:
        return jsonify({
            "success": False,
            "message": "계획을 찾을 수 없습니다."
        }), 404

    return jsonify({
        "success": True,
        "message": "계획과 세부 할 일, 수정 이력, 실행 및 완료 기록이 모두 삭제되었습니다."
    })


# 전체 데이터 파일 하나로 내보내기 (JSON Export / 백업)
@app.route("/api/export", methods=["GET"])
def export_all_data():
    conn = get_db()
    
    plans_cursor = conn.execute("SELECT * FROM plans ORDER BY id ASC")
    plans = [dict(r) for r in plans_cursor.fetchall()]

    hist_cursor = conn.execute("SELECT * FROM plan_history ORDER BY id ASC")
    history = [dict(r) for r in hist_cursor.fetchall()]

    exec_cursor = conn.execute("SELECT * FROM execution_records ORDER BY id ASC")
    executions = [dict(r) for r in exec_cursor.fetchall()]

    comp_cursor = conn.execute("SELECT * FROM completion_records ORDER BY id ASC")
    completions = [dict(r) for r in comp_cursor.fetchall()]

    next_cursor = conn.execute("SELECT * FROM next_actions ORDER BY id ASC")
    next_actions = [dict(r) for r in next_cursor.fetchall()]

    tasks_cursor = conn.execute("SELECT * FROM plan_tasks ORDER BY id ASC")
    tasks = [dict(r) for r in tasks_cursor.fetchall()]

    conn.close()

    now_kst = get_kst_now()
    timestamp_str = now_kst.strftime("%Y%m%d_%H%M%S")

    export_payload = {
        "metadata": {
            "system": "Plan-Do-See (PDS) Personal Task System",
            "version": "2.0.0",
            "schema_contract": "contracts/pds-schema-v2.json",
            "exported_at": now_kst.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": "Asia/Seoul (KST, UTC+9)",
            "total_plans": len(plans),
            "total_tasks": len(tasks),
            "total_history": len(history),
            "total_executions": len(executions),
            "total_completions": len(completions),
            "total_next_actions": len(next_actions),
            "notice": "지금은 로그인이 없어 링크를 아는 사람은 누구나 볼 수 있습니다. 남이 봐도 괜찮은 내용만 넣으세요."
        },
        "plans": plans,
        "plan_tasks": tasks,
        "plan_history": history,
        "execution_records": executions,
        "completion_records": completions,
        "next_actions": next_actions
    }

    json_str = json.dumps(export_payload, ensure_ascii=False, indent=2)
    filename = f"pds_backup_{timestamp_str}.json"

    response = Response(json_str, mimetype="application/json; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


if __name__ == "__main__":
    init_db()

    print("=" * 50)
    print("Plan → Do → See 시작")
    print("http://127.0.0.1:5000")
    print("=" * 50)

    app.run(debug=True)