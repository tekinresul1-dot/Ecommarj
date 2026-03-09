import psycopg2
import sys

def check_db(dbname, user, password, host, port):
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.close()
        return True
    except Exception as e:
        return False

configs = [
    # (dbname, user, password)
    ("ecompro", "postgres", "postgres"),
    ("ecompro", "postgres", ""),
    ("ecompro", "candemir", ""),
    ("ecommarj", "postgres", "postgres"),
    ("ecommarj", "postgres", ""),
    ("ecompro", "postgres", "postgres_password_change_me"),
    ("postgres", "postgres", ""),
    ("postgres", "postgres", "postgres"),
    ("postgres", "candemir", ""),
]

for db, u, p in configs:
    if check_db(db, u, p, "localhost", "5432"):
        print(f"SUCCESS: db={db}, user={u}, pass={p}")
        sys.exit(0)

print("FAILED ALL")
sys.exit(1)
