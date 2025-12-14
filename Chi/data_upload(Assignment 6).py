import pyodbc
import csv
import json
import os
from datetime import datetime

server = 'tcp:lds.di.unipi.it'
database = 'Group_ID_22_DB'
username = 'Group_ID_22'
password = 'BJ4X9GI6'

connectionString = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};DATABASE={database};"
    f"UID={username};PWD={password}"
)

def connect_to_database():
    return pyodbc.connect(connectionString)

def sanitize_row(row):
    sanitized = []
    for value in row:
        if value == '' or value is None:
            sanitized.append(None)
        else:
            try:
                if '.' in value:
                    sanitized.append(float(value))
                else:
                    sanitized.append(int(value))
            except ValueError:
                sanitized.append(value)
    return sanitized

def upload_csv_to_table(
    connection,
    cursor,
    csv_path,
    table_name,
    checkpoint_file="checkpoint.json",
    commit_every=1000
):
    print(f"\nUploading {csv_path} → {table_name}")

    # load checkpoint if exists
    last_row = -1
    last_table = None
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            checkpoint = json.load(f)
            last_row = checkpoint.get("last_processed_row", -1)
            last_table = checkpoint.get("last_processed_table")

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        header = reader[0]
        rows = reader[1:]

    if last_table == table_name and last_row >= len(rows) - 1:
        print(f"Table {table_name} already completed, skipping.")
        return

    placeholders = ", ".join(["?"] * len(header))
    columns = ", ".join(header)
    insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    for i, row in enumerate(rows[last_row + 1:], start=last_row + 1):
        try:
            cursor.execute(insert_sql, sanitize_row(row))

            if i % commit_every == 0:
                connection.commit()
                with open(checkpoint_file, "w") as f:
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "last_processed_row": i,
                        "last_processed_table": table_name,
                        "total_rows": len(rows),
                        "progress_percent": round(i / len(rows) * 100, 2)
                    }, f, indent=4)

                print(f"  ⏳ {table_name}: {i}/{len(rows)} rows")

        except Exception as e:
            connection.rollback()
            print(f"Error at row {i} in table {table_name}: {e}")
            raise

    connection.commit()
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

    print(f"Completed upload for {table_name}")

def retrieve_columns_metadata(cursor, table_name):
    print(f"\nColumns in {table_name}:")
    for col in cursor.columns(table=table_name):
        print(f"  - {col.column_name} ({col.type_name})")

def main():
    cnxn = connect_to_database()
    cursor = cnxn.cursor()

    csv_to_table = [
        # Dimensions
        ("/Users/huynhphuongchi/Desktop/DW/geo_dim.csv", "geo_dim"),
        ("/Users/huynhphuongchi/Desktop/DW/artist_dim.csv", "artist_dim"),
        ("/Users/huynhphuongchi/Desktop/DW/time_dim.csv", "time_dim"),
        ("/Users/huynhphuongchi/Desktop/DW/track_dim.csv", "track_dim"),

        # Bridge
        ("/Users/huynhphuongchi/Desktop/DW/track_artist_bridge.csv", "track_artist_bridge"),

        # Fact
        ("/Users/huynhphuongchi/Desktop/DW/fact_streams.csv", "fact_table"),
    ]

    for csv_file, table_name in csv_to_table:
        upload_csv_to_table(cnxn, cursor, csv_file, table_name)

    for _, table_name in csv_to_table:
        retrieve_columns_metadata(cursor, table_name)

    cursor.close()
    cnxn.close()
    print("\nDATABASE POPULATION COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    main()
