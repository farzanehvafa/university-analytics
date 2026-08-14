import sqlite3

dest = sqlite3.connect("downloads.db")
cur = dest.cursor()

cur.execute("ATTACH DATABASE '/Users/farzaneh/dbt-practice/practice.db' AS src")

cur.execute("DROP TABLE IF EXISTS screen_views_by_university")
cur.execute("""
    CREATE TABLE screen_views_by_university AS
    SELECT * FROM src.mart_screen_views_by_university
""")

dest.commit()

print("Copied. Preview:")
for row in cur.execute("SELECT * FROM screen_views_by_university LIMIT 5"):
    print(row)

cur.execute("DETACH DATABASE src")
dest.close()