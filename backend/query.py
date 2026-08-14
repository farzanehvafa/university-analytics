import sqlite3

conn = sqlite3.connect("downloads.db")
cur = conn.cursor()

rows = cur.execute("""
    SELECT university_code, SUM(downloads) AS total
    FROM downloads_by_university
    GROUP BY university_code
    ORDER BY total DESC
    LIMIT 10
""").fetchall()


for row in rows:
    print(row)