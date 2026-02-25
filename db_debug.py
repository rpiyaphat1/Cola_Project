import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "instance", "cola.db")


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    print("DB:", DB)
    print("Tables:", [t[0] for t in tables])

    if not any(t[0] == 'users' for t in tables):
        print("ERROR: table 'users' not found in this DB")
        return

    rows = cur.execute("SELECT username, password, displayname, permission FROM users ORDER BY username").fetchall()
    print("User count:", len(rows))

    for u, p, d, perm in rows:
        p_preview = (p[:50] + "...") if p else None
        print(f"- {u} | {p_preview} | {d} | {perm}")

    con.close()


if __name__ == '__main__':
    main()
