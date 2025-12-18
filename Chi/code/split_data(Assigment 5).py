import csv
from datetime import datetime
import os

OUTPUT_DIR = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/table"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# GEO DIMENSION
def extract_geo_dim(input_csv, output_csv):
    geo_map = {}
    geo_id = 1

    with open(input_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = (
                r["birth_place"].strip(),
                r["region"].strip(),
                r["country"].strip()
            )
            if key not in geo_map:
                geo_map[key] = geo_id
                geo_id += 1

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["geo_ID", "birthplace", "region", "country"])
        for (b, r, c), gid in geo_map.items():
            writer.writerow([gid, b, r, c])

# ARTIST DIMENSION
def extract_artist_dim(input_csv, geo_dim_csv, output_csv):
    geo_lookup = {}
    with open(geo_dim_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            geo_lookup[(r["birthplace"], r["region"], r["country"])] = r["geo_ID"]

    artist_map = {}
    artist_id = 1

    with open(input_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            geo_fk = geo_lookup.get(
                (r["birth_place"], r["region"], r["country"])
            )
            key = (r["id_author"], r["gender"], geo_fk)
            if key not in artist_map:
                artist_map[key] = artist_id
                artist_id += 1

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID_artist", "ID_artist_original", "gender", "geo_ID_FK"])
        for (orig, gender, geo_fk), aid in artist_map.items():
            writer.writerow([aid, orig, gender, geo_fk])

# TIME DIMENSION
def extract_time_dim(input_csv, output_csv):
    time_map = {}
    time_id = 1

    with open(input_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                dt = datetime(
                    int(r["year"]),
                    int(r["month"]),
                    int(r["day"])
                )

                season = (
                    "winter" if dt.month in [12,1,2] else
                    "spring" if dt.month in [3,4,5] else
                    "summer" if dt.month in [6,7,8] else
                    "autumn"
                )

                key = (
                    dt.strftime("%A"),
                    dt.year,
                    dt.month,
                    season
                )

                if key not in time_map:
                    time_map[key] = time_id
                    time_id += 1
            except:
                continue

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID_time", "day_of_week", "year", "month", "season"])
        for (dow, y, m, s), tid in time_map.items():
            writer.writerow([tid, dow, y, m, s])

# TRACK DIMENSION
def extract_track_dim(input_csv, output_csv):
    track_map = {}
    track_id = 1

    with open(input_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = (
                r["id"],
                r["song_category"]
            )
            if key not in track_map:
                track_map[key] = track_id
                track_id += 1

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID_track",
            "ID_track_original",
            "song_category"
        ])
        for (orig, cat), tid in track_map.items():
            writer.writerow([tid, orig, cat])

# TRACK-ARTIST BRIDGE
def extract_track_artist_bridge(input_csv, track_dim_csv, artist_dim_csv, output_csv):
    track_lookup = {}
    with open(track_dim_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            track_lookup[r["ID_track_original"]] = r["ID_track"]

    artist_lookup = {}
    with open(artist_dim_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            artist_lookup[r["ID_artist_original"]] = r["ID_artist"]

    rows = []

    with open(input_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            track_fk = track_lookup.get(r["id"])
            main_fk = artist_lookup.get(r["id_artist"])

            if track_fk and main_fk:
                rows.append([track_fk, main_fk, "main"])

                if r["featured_artists"]:
                    for feat in r["featured_artists"].split(","):
                        feat_fk = artist_lookup.get(feat.strip())
                        if feat_fk:
                            rows.append([track_fk, feat_fk, "feature"])

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID_track_FK",
            "ID_artist_FK",
            "role"
        ])
        writer.writerows(rows)

# FACT TABLE
def extract_fact_table(input_csv, track_dim_csv, time_dim_csv, output_csv):
    track_lookup = {}
    with open(track_dim_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            track_lookup[r["ID_track_original"]] = r["ID_track"]

    time_lookup = {}
    with open(time_dim_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            time_lookup[(r["year"], r["month"])] = r["ID_time"]

    with open(input_csv, encoding="utf-8") as f, \
         open(output_csv, "w", newline="", encoding="utf-8") as out:

        reader = csv.DictReader(f)
        writer = csv.writer(out)
        writer.writerow([
            "ID_track_FK",
            "ID_time_FK",
            "Streams_1month"
        ])

        for r in reader:
            track_fk = track_lookup.get(r["id"])
            time_fk = time_lookup.get((r["year"], r["month"]))

            if track_fk and time_fk:
                writer.writerow([
                    track_fk,
                    time_fk,
                    r["streams@1month"]
                ])

# EXECUTION
artist_file = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/LDS Data 2025-2026/artists_cleaned.csv"
track_file  = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/LDS Data 2025-2026/tracks_cleaned_with_song_category.csv"

output_geo_dim = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/table/geo_dim.csv"
output_artist_dim = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/table/artist_dim.csv"
output_time_dim = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/table/time_dim.csv"
output_track_dim = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/table/track_dim.csv"
output_track_artist_bridge = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/table/track_artist_bridge.csv"
output_fact_table = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/table/fact_streams.csv"

extract_geo_dim(artist_file, output_geo_dim)

extract_artist_dim(
    artist_file,
    output_geo_dim,
    output_artist_dim
)

extract_time_dim(
    track_file,
    output_time_dim
)

extract_track_dim(
    track_file,
    output_track_dim
)

extract_track_artist_bridge(
    track_file,
    output_track_dim,
    output_artist_dim,
    output_track_artist_bridge
)

extract_fact_table(
    track_file,
    output_track_dim,
    output_time_dim,
    output_fact_table
)
