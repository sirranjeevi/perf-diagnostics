import time  # Why: gives us a current timestamp for the fake row

from db import connect, insert_sample  # Why: reuses the functions we wrote in db.py

conn = connect()  # Why: opens metrics.db and creates the table if it's missing

# Why: saves one fake row. The numbers are dummy values, only used to test storage.
insert_sample(conn, "test-run", "idle", time.time(), 10.0, 50.0, 0.0, 0.0, 0.0, 0.0)

# Why: reads back the columns we care about, to confirm the row was really saved
rows = conn.execute("SELECT run_id, label, cpu_percent FROM samples").fetchall()
print("Rows:", rows)  # Why: prints the result so you can check it

conn.close()  # Why: releases the database file when we're done