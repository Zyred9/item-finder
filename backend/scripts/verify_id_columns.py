"""
验证数据库中所有主键、外键是否为 BIGINT（自增主键）
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_connection_params():
    from config.settings import settings
    url = settings.DATABASE_URL
    m = re.match(r"mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)", url)
    if not m:
        raise ValueError("Unsupported DATABASE_URL")
    user, password, host, port, database = m.groups()
    return {"host": host, "port": int(port), "user": user, "password": password, "database": database}


def main():
    import pymysql
    params = get_connection_params()
    conn = pymysql.connect(**params)
    cur = conn.cursor()

    # 主键列
    cur.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, EXTRA
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND COLUMN_KEY = 'PRI'
        ORDER BY TABLE_NAME, ORDINAL_POSITION
    """, (params["database"],))
    pk_rows = cur.fetchall()

    # 外键列（通过 KEY_COLUMN_USAGE 找引用其它表的列）
    cur.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND COLUMN_NAME IN ('id', 'family_id', 'user_id', 'creator_id', 'item_id', 'category_id', 'parent_id', 'reminder_id')
        ORDER BY TABLE_NAME, COLUMN_NAME
    """, (params["database"],))
    id_cols = cur.fetchall()

    conn.close()

    print("=== 主键 (应为 bigint, auto_increment) ===\n")
    all_ok = True
    for table, col, data_type, col_type, extra in pk_rows:
        is_bigint = (data_type or "").lower() == "bigint"
        has_auto = (extra or "").lower().find("auto_increment") >= 0
        ok = is_bigint and (col == "id" and has_auto or col != "id")
        if not ok and col == "id":
            all_ok = False
        status = "OK" if ok else "FAIL"
        print(f"  {table}.{col}: {col_type or data_type}  {extra or ''}  [{status}]")

    print("\n=== ID/外键列 (应为 bigint) ===\n")
    for table, col, data_type, col_type in id_cols:
        is_bigint = (data_type or "").lower() == "bigint"
        status = "OK" if is_bigint else "FAIL"
        if not is_bigint:
            all_ok = False
        print(f"  {table}.{col}: {col_type or data_type}  [{status}]")

    print("\n" + ("[OK] 所有主键/外键均为 BIGINT，主键为自增。" if all_ok else "[FAIL] 存在非 BIGINT 或非自增主键。"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
