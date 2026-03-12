"""
将全部 VARCHAR UUID 主键/外键迁移为 BIGINT 自增主键（方案 B：不保留 uuid 列）
历史数据保留，执行前请备份数据库。
"""
import os
import re
import sys

# 保证能导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_connection_params():
    from config.settings import settings
    url = settings.DATABASE_URL
    # mysql+pymysql://user:pass@host:port/dbname?charset=utf8mb4
    m = re.match(r"mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)", url)
    if not m:
        raise ValueError("Unsupported DATABASE_URL format")
    user, password, host, port, database = m.groups()
    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "database": database,
    }


def run_migration():
    import pymysql
    params = get_connection_params()
    conn = pymysql.connect(**params)
    conn.cursor().execute("SET NAMES utf8mb4")
    conn.commit()

    def exec_many(cursor, statements):
        for s in statements:
            s = (s or "").strip()
            if not s or s.startswith("--"):
                continue
            try:
                cursor.execute(s)
            except Exception as e:
                print(f"[SQL] {s[:120]}...")
                raise RuntimeError(f"Migration failed: {e}") from e

    cursor = conn.cursor()

    # 1) 关闭外键检查
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    conn.commit()

    # 2) 为每张表添加 id_new 并赋行号
    tables_with_fk = [
        ("families", []),
        ("users", [("family_id", "families", "id")]),
        ("categories", [("parent_id", "categories", "id")]),  # 自引用稍后处理
        ("locations", [("family_id", "families", "id"), ("parent_id", "locations", "id")]),
        ("items", [("family_id", "families", "id"), ("creator_id", "users", "id"), ("category_id", "categories", "id")]),
        ("item_extensions", [("item_id", "items", "id")]),
        ("reminders", [("family_id", "families", "id"), ("item_id", "items", "id")]),
        ("chat_messages", [("family_id", "families", "id"), ("user_id", "users", "id")]),
    ]

    # 为 categories 保留旧 id 到 code（用于 seed 与关联）
    cursor.execute("""
        SELECT COLUMN_NAME FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'categories' AND COLUMN_NAME = 'code'
    """, (params["database"],))
    has_code = cursor.fetchone() is not None
    if not has_code:
        cursor.execute("ALTER TABLE categories ADD COLUMN code VARCHAR(50) NULL UNIQUE AFTER id")
        conn.commit()
        cursor.execute("UPDATE categories SET code = id")
        conn.commit()

    for table, _ in tables_with_fk:
        cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN id_new BIGINT NULL")
        conn.commit()
        cursor.execute("SET @r := 0")
        cursor.execute(f"UPDATE `{table}` SET id_new = (@r := @r + 1) ORDER BY id")
        conn.commit()
        if table == "categories":
            cursor.execute("UPDATE categories SET code = id WHERE code IS NULL")
            conn.commit()

    # 3) 为 categories 填 parent_id_new（自引用）
    cursor.execute("ALTER TABLE categories ADD COLUMN parent_id_new BIGINT NULL")
    conn.commit()
    cursor.execute("""
        UPDATE categories c
        JOIN categories p ON c.parent_id = p.id
        SET c.parent_id_new = p.id_new
    """)
    conn.commit()

    # 4) 为各表添加 fk_new 并填充
    # users
    cursor.execute("ALTER TABLE users ADD COLUMN family_id_new BIGINT NULL")
    conn.commit()
    cursor.execute("UPDATE users u JOIN families f ON u.family_id = f.id SET u.family_id_new = f.id_new")
    conn.commit()

    # locations
    cursor.execute("ALTER TABLE locations ADD COLUMN family_id_new BIGINT NULL")
    cursor.execute("ALTER TABLE locations ADD COLUMN parent_id_new BIGINT NULL")
    conn.commit()
    cursor.execute("UPDATE locations loc JOIN families f ON loc.family_id = f.id SET loc.family_id_new = f.id_new")
    cursor.execute("UPDATE locations loc JOIN locations p ON loc.parent_id = p.id SET loc.parent_id_new = p.id_new")
    conn.commit()

    # items
    cursor.execute("ALTER TABLE items ADD COLUMN family_id_new BIGINT NULL")
    cursor.execute("ALTER TABLE items ADD COLUMN creator_id_new BIGINT NULL")
    cursor.execute("ALTER TABLE items ADD COLUMN category_id_new BIGINT NULL")
    conn.commit()
    cursor.execute("UPDATE items i JOIN families f ON i.family_id = f.id SET i.family_id_new = f.id_new")
    cursor.execute("UPDATE items i JOIN users u ON i.creator_id = u.id SET i.creator_id_new = u.id_new")
    cursor.execute("UPDATE items i JOIN categories c ON i.category_id = c.id SET i.category_id_new = c.id_new")
    conn.commit()

    # item_extensions
    cursor.execute("ALTER TABLE item_extensions ADD COLUMN item_id_new BIGINT NULL")
    conn.commit()
    cursor.execute("UPDATE item_extensions e JOIN items i ON e.item_id = i.id SET e.item_id_new = i.id_new")
    conn.commit()

    # reminders
    cursor.execute("ALTER TABLE reminders ADD COLUMN family_id_new BIGINT NULL")
    cursor.execute("ALTER TABLE reminders ADD COLUMN item_id_new BIGINT NULL")
    conn.commit()
    cursor.execute("UPDATE reminders r JOIN families f ON r.family_id = f.id SET r.family_id_new = f.id_new")
    cursor.execute("UPDATE reminders r JOIN items i ON r.item_id = i.id SET r.item_id_new = i.id_new")
    conn.commit()

    # chat_messages
    cursor.execute("ALTER TABLE chat_messages ADD COLUMN family_id_new BIGINT NULL")
    cursor.execute("ALTER TABLE chat_messages ADD COLUMN user_id_new BIGINT NULL")
    conn.commit()
    cursor.execute("UPDATE chat_messages m JOIN families f ON m.family_id = f.id SET m.family_id_new = f.id_new")
    cursor.execute("UPDATE chat_messages m JOIN users u ON m.user_id = u.id SET m.user_id_new = u.id_new")
    conn.commit()

    # 5) 查出现有外键约束名并删除
    cursor.execute("""
        SELECT TABLE_NAME, CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = %s AND CONSTRAINT_TYPE = 'FOREIGN KEY'
    """, (params["database"],))
    for table_name, constraint_name in cursor.fetchall():
        try:
            cursor.execute(f"ALTER TABLE `{table_name}` DROP FOREIGN KEY `{constraint_name}`")
            conn.commit()
        except Exception as e:
            print(f"Drop FK {table_name}.{constraint_name}: {e}")

    # 6) 各表：删主键、删 id、重命名 id_new 为 id、加主键与自增
    for table, _ in tables_with_fk:
        try:
            cursor.execute(f"ALTER TABLE `{table}` DROP PRIMARY KEY")
        except Exception:
            pass
        conn.commit()
        cursor.execute(f"ALTER TABLE `{table}` DROP COLUMN id")
        cursor.execute(f"ALTER TABLE `{table}` CHANGE COLUMN id_new id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY")
        conn.commit()

    # 7) 外键列：删旧列、重命名新列
    cursor.execute("ALTER TABLE users DROP COLUMN family_id")
    cursor.execute("ALTER TABLE users CHANGE COLUMN family_id_new family_id BIGINT NULL")
    conn.commit()

    cursor.execute("ALTER TABLE categories DROP COLUMN parent_id")
    cursor.execute("ALTER TABLE categories CHANGE COLUMN parent_id_new parent_id BIGINT NULL")
    conn.commit()

    cursor.execute("ALTER TABLE locations DROP COLUMN family_id")
    cursor.execute("ALTER TABLE locations CHANGE COLUMN family_id_new family_id BIGINT NOT NULL")
    cursor.execute("ALTER TABLE locations DROP COLUMN parent_id")
    cursor.execute("ALTER TABLE locations CHANGE COLUMN parent_id_new parent_id BIGINT NULL")
    conn.commit()

    cursor.execute("ALTER TABLE items DROP COLUMN family_id")
    cursor.execute("ALTER TABLE items CHANGE COLUMN family_id_new family_id BIGINT NOT NULL")
    cursor.execute("ALTER TABLE items DROP COLUMN creator_id")
    cursor.execute("ALTER TABLE items CHANGE COLUMN creator_id_new creator_id BIGINT NOT NULL")
    cursor.execute("ALTER TABLE items DROP COLUMN category_id")
    cursor.execute("ALTER TABLE items CHANGE COLUMN category_id_new category_id BIGINT NULL")
    conn.commit()

    cursor.execute("ALTER TABLE item_extensions DROP COLUMN item_id")
    cursor.execute("ALTER TABLE item_extensions CHANGE COLUMN item_id_new item_id BIGINT NOT NULL")
    conn.commit()

    cursor.execute("ALTER TABLE reminders DROP COLUMN family_id")
    cursor.execute("ALTER TABLE reminders CHANGE COLUMN family_id_new family_id BIGINT NOT NULL")
    cursor.execute("ALTER TABLE reminders DROP COLUMN item_id")
    cursor.execute("ALTER TABLE reminders CHANGE COLUMN item_id_new item_id BIGINT NOT NULL")
    conn.commit()

    cursor.execute("ALTER TABLE chat_messages DROP COLUMN family_id")
    cursor.execute("ALTER TABLE chat_messages CHANGE COLUMN family_id_new family_id BIGINT NOT NULL")
    cursor.execute("ALTER TABLE chat_messages DROP COLUMN user_id")
    cursor.execute("ALTER TABLE chat_messages CHANGE COLUMN user_id_new user_id BIGINT NOT NULL")
    conn.commit()

    # 8) 重新加外键（可选，便于引用完整）
    exec_many(cursor, [
        "ALTER TABLE users ADD CONSTRAINT fk_users_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE SET NULL",
        "ALTER TABLE categories ADD CONSTRAINT fk_categories_parent FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL",
        "ALTER TABLE locations ADD CONSTRAINT fk_locations_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE",
        "ALTER TABLE locations ADD CONSTRAINT fk_locations_parent FOREIGN KEY (parent_id) REFERENCES locations(id) ON DELETE SET NULL",
        "ALTER TABLE items ADD CONSTRAINT fk_items_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE",
        "ALTER TABLE items ADD CONSTRAINT fk_items_creator FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE",
        "ALTER TABLE items ADD CONSTRAINT fk_items_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL",
        "ALTER TABLE item_extensions ADD CONSTRAINT fk_item_ext_item FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE",
        "ALTER TABLE reminders ADD CONSTRAINT fk_reminders_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE",
        "ALTER TABLE reminders ADD CONSTRAINT fk_reminders_item FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE",
        "ALTER TABLE chat_messages ADD CONSTRAINT fk_chat_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE",
        "ALTER TABLE chat_messages ADD CONSTRAINT fk_chat_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
    ])
    conn.commit()

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()
    conn.close()
    print("[OK] Migration completed: all ids are now BIGINT auto-increment.")


if __name__ == "__main__":
    run_migration()
