import csv
from datetime import datetime

# GEO DIMENSION
def extract_geo_dim(input_csv, output_csv):
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        data = list(reader)

    birthplace_idx = header.index('birthplace')
    region_idx = header.index('region')
    country_idx = header.index('country')

    geo_records = {}
    geo_id = 1

    for row in data:
        key = (
            row[birthplace_idx].strip(),
            row[region_idx].strip(),
            row[country_idx].strip()
        )
        if key not in geo_records:
            geo_records[key] = geo_id
            geo_id += 1

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['geo_ID', 'birthplace', 'region', 'country'])
        for (birthplace, region, country), gid in geo_records.items():
            writer.writerow([gid, birthplace, region, country])

# ARTIST DIMENSION
def extract_artist_dim(input_csv, geo_dim_csv, output_csv):
    geo_map = {}
    with open(geo_dim_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            geo_map[(row[1], row[2], row[3])] = row[0]

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        data = list(reader)

    artist_idx = header.index('id_author')
    gender_idx = header.index('gender')
    birthplace_idx = header.index('birthplace')
    region_idx = header.index('region')
    country_idx = header.index('country')

    artist_records = {}
    artist_id = 1

    for row in data:
        geo_fk = geo_map.get(
            (row[birthplace_idx], row[region_idx], row[country_idx])
        )
        key = (row[artist_idx], row[gender_idx], geo_fk)

        if key not in artist_records:
            artist_records[key] = artist_id
            artist_id += 1

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID_artist', 'ID_artist_original', 'gender', 'geo_ID_FK'])
        for (orig_id, gender, geo_fk), aid in artist_records.items():
            writer.writerow([aid, orig_id, gender, geo_fk])

# TIME DIMENSION
def extract_time_dim(input_csv, output_csv):
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        data = list(reader)

    year_idx = header.index('year')
    month_idx = header.index('month')
    day_idx = header.index('day')

    time_records = {}
    time_id = 1

    for row in data:
        try:
            y = int(float(row[year_idx]))
            m = int(float(row[month_idx]))
            d = int(float(row[day_idx]))

            dt = datetime(y, m, d)
            day_of_week = dt.strftime('%A')
            season = (m % 12 + 3) // 3

            key = (d, day_of_week, y, m, season)
            if key not in time_records:
                time_records[key] = time_id
                time_id += 1
        except:
            continue

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID_time', 'day', 'day_of_week', 'year', 'month', 'season'])
        for (d, dow, y, m, s), tid in time_records.items():
            writer.writerow([tid, d, dow, y, m, s])

# TRACK DIMENSION
def extract_track_dim(input_csv, time_dim_csv, output_csv):
    time_map = {}
    with open(time_dim_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            time_map[(row[3], row[4])] = row[0]  # year, month

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        data = list(reader)

    id_idx = header.index('id')
    title_idx = header.index('title')
    song_cat_idx = header.index('song_category')
    year_idx = header.index('year')
    month_idx = header.index('month')

    track_records = {}
    track_id = 1

    for row in data:
        time_fk = time_map.get((row[year_idx], row[month_idx]))
        key = (row[id_idx], row[title_idx], row[song_cat_idx], time_fk)

        if key not in track_records:
            track_records[key] = track_id
            track_id += 1

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID_track',
            'ID_track_original',
            'title',
            'song_category',
            'ID_time_FK'
        ])
        for (orig, title, cat, tfk), tid in track_records.items():
            writer.writerow([tid, orig, title, cat, tfk])

# TRACK-ARTIST BRIDGE
def extract_track_artist_bridge(input_csv, track_dim_csv, artist_dim_csv, output_csv):
    track_map = {}
    with open(track_dim_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            track_map[row[1]] = row[0]

    artist_map = {}
    with open(artist_dim_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            artist_map[row[1]] = row[0]

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        data = list(reader)

    track_idx = header.index('id')
    artist_idx = header.index('id_artist')
    feat_idx = header.index('featured_artists')

    records = []

    for row in data:
        track_fk = track_map.get(row[track_idx])
        artist_fk = artist_map.get(row[artist_idx])

        if track_fk and artist_fk:
            records.append((track_fk, artist_fk, 'main', 0.8))

            if row[feat_idx]:
                for feat in row[feat_idx].split(','):
                    feat_fk = artist_map.get(feat.strip())
                    if feat_fk:
                        records.append((track_fk, feat_fk, 'feature', 0.2))

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID_track_FK', 'ID_artist_FK', 'role', 'weight'])
        writer.writerows(records)

# FACT TABLE
def extract_fact_table(input_csv, track_dim_csv, output_csv):
    track_map = {}
    with open(track_dim_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            track_map[row[1]] = row[0]

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        data = list(reader)

    track_idx = header.index('id')
    streams_idx = header.index('streams@1month')

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID_track_FK', 'Streams_1month'])

        for row in data:
            track_fk = track_map.get(row[track_idx])
            if track_fk:
                writer.writerow([track_fk, row[streams_idx]])

# EXECUTION
artist_file = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/LDS Data 2025-2026/artists.csv"
track_file  = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/LDS Data 2025-2026/tracks.csv"

output_geo_dim = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/output/geo_dim.csv"
output_artist_dim = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/output/artist_dim.csv"
output_time_dim = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/output/time_dim.csv"
output_track_dim = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/output/track_dim.csv"
output_track_artist_bridge = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/output/track_artist_bridge.csv"
output_fact_table = r"/Users/huynhphuongchi/Desktop/Unipi/DSS/Module 2/output/fact_streams.csv"

extract_geo_dim(artist_file, output_geo_dim)
extract_artist_dim(artist_file, output_geo_dim, output_artist_dim)
extract_time_dim(track_file, output_time_dim)
extract_track_dim(track_file, output_time_dim, output_track_dim)
extract_track_artist_bridge(track_file, output_track_dim, output_artist_dim, output_track_artist_bridge)
extract_fact_table(track_file, output_track_dim, output_fact_table)