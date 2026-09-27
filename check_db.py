# -*- coding: utf-8 -*-
"""
SQLite DB 간편 조회 스크립트
"""
import sys
import os
import sqlite3

# Windows 콘솔 인코딩 대응
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

curr_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(curr_dir, "database.db")):
    DB_PATH = os.path.join(curr_dir, "database.db")
elif os.path.exists(os.path.join(curr_dir, "plan_diary-main", "database.db")):
    DB_PATH = os.path.join(curr_dir, "plan_diary-main", "database.db")
else:
    DB_PATH = os.path.join(curr_dir, "database.db")

def print_table(headers, rows):
    if not rows:
        print("  (데이터 없음)")
        return
    s_rows = [[str(col) if col is not None else "NULL" for col in row] for row in rows]
    col_widths = [len(h) for h in headers]
    for row in s_rows:
        for idx, col in enumerate(row):
            # 한글/영문 길이 단순 보정
            col_widths[idx] = max(col_widths[idx], len(col))
    
    header_str = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    sep_str = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    print(header_str)
    print(sep_str)
    for row in s_rows:
        print(" | ".join(row[i].ljust(col_widths[i]) for i in range(len(headers))))

def main():
    if not os.path.exists(DB_PATH):
        print(f"[오류] DB 파일을 찾을 수 없습니다: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if len(sys.argv) == 1:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        print("=" * 50)
        print(" [database.db 테이블 목록 및 레코드 수]")
        print("=" * 50)
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cursor.fetchone()[0]
            print(f"  - {t:<22} : {cnt:>4}개 행")
        print("=" * 50)
        print("\n[사용 방법]")
        print("  1. 특정 테이블 조회: python check_db.py <테이블명>")
        print("     예시) python check_db.py users")
        print("     예시) python check_db.py plans")
        print('  2. SQL 직접 실행   : python check_db.py "SELECT * FROM users"\n')
        return

    arg = sys.argv[1].strip()
    if arg.upper().startswith("SELECT") or arg.upper().startswith("PRAGMA"):
        query = " ".join(sys.argv[1:])
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            if rows:
                headers = rows[0].keys()
                print_table(headers, rows)
            else:
                print("  (결과가 없습니다.)")
        except Exception as e:
            print(f"[쿼리 오류]: {e}")
    else:
        table_name = arg
        try:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 20;")
            rows = cursor.fetchall()
            print(f"\n[{table_name}] 테이블 데이터 (최대 20개):")
            if rows:
                headers = rows[0].keys()
                print_table(headers, rows)
            else:
                print("  (데이터 없음)")
        except Exception as e:
            print(f"[조회 오류]: {e}")

if __name__ == "__main__":
    main()
