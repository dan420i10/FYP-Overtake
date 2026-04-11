import duckdb
import pandas as pd
from typing import Optional


class F1DB:
    def __init__(self, db_path: str = "f1.duckdb"):
        self.con = duckdb.connect(db_path)

    def q(self, sql: str) -> pd.DataFrame:
        return self.con.execute(sql).df()

    def execute(self, sql: str):
        return self.con.execute(sql)

    def close(self):
        self.con.close()

    def create_table(self, name: str, df: pd.DataFrame, replace: bool = True):
        if replace:
            self.con.execute(f"DROP TABLE IF EXISTS {name}")
        self.con.register("tmp_df", df)
        self.con.execute(f"CREATE TABLE {name} AS SELECT * FROM tmp_df")
        self.con.unregister("tmp_df")

    def create_view(self, name: str, sql: str):
        self.con.execute(f"CREATE OR REPLACE VIEW {name} AS {sql}")

    def drop_table(self, name: str):
        self.con.execute(f"DROP TABLE IF EXISTS {name}")

    def drop_view(self, name: str):
        self.con.execute(f"DROP VIEW IF EXISTS {name}")

    def delete(self, table: str, condition: str):
        self.con.execute(f"DELETE FROM {table} WHERE {condition}")


_default_db: Optional[F1DB] = None


def get_db() -> F1DB:
    global _default_db
    if _default_db is None:
        _default_db = F1DB()
    return _default_db


def connect(db_path: str = "f1.duckdb") -> F1DB:
    return F1DB(db_path)


def query(sql: str, db: Optional[F1DB] = None) -> pd.DataFrame:
    db = db or get_db()
    return db.q(sql)


def execute(sql: str, db: Optional[F1DB] = None):
    db = db or get_db()
    return db.execute(sql)


def create_table(name: str, df: pd.DataFrame, replace: bool = True, db: Optional[F1DB] = None):
    db = db or get_db()
    return db.create_table(name, df, replace)


def create_view(name: str, sql: str, db: Optional[F1DB] = None):
    db = db or get_db()
    return db.create_view(name, sql)


def drop_table(name: str, db: Optional[F1DB] = None):
    db = db or get_db()
    return db.drop_table(name)


def drop_view(name: str, db: Optional[F1DB] = None):
    db = db or get_db()
    return db.drop_view(name)


def delete(table: str, condition: str, db: Optional[F1DB] = None):
    db = db or get_db()
    return db.delete(table, condition)


def run_sql_file(path: str, db: Optional[F1DB] = None):
    db = db or get_db()
    with open(path, "r") as f:
        return db.execute(f.read())


def interactive(db: Optional[F1DB] = None):
    db = db or get_db()

    print("\nDuckDB Interactive Shell")
    print("Type SQL to query")
    print("Commands:")
    print("  :exit       → quit")
    print("  :tables     → show tables")
    print("  :views      → show views")
    print("  :help       → help\n")

    while True:
        sql = input("duckdb> ").strip()

        if not sql:
            continue

        if sql == ":exit":
            break

        if sql == ":help":
            print("SQL mode + commands (:tables, :views, :exit)")
            continue

        if sql == ":tables":
            print(db.q("SHOW TABLES"))
            continue

        if sql == ":views":
            print(db.q("SHOW VIEWS"))
            continue

        try:
            result = db.q(sql)
            print(result.to_string(index=False))
        except Exception as e:
            print(f"\nERROR: {type(e).__name__}")
            print(e)