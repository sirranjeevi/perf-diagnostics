"""Print live metrics once per second and save each reading to SQLite."""

import sys
import time

import psutil

import db  # Imports db.py from this same folder


def main():
    # Read the label from the command line, for example: python collector.py cpu
    # If no label is given, the label is "idle".
    label = sys.argv[1] if len(sys.argv) > 1 else "idle"

    # Make a name for this recording session, based on the start time.
    run_id = f"run-{int(time.time())}"

    # Open metrics.db. This also creates the table if it doesn't exist yet.
    conn = db.connect()

    # Call cpu_percent once so later calls return real values.
    psutil.cpu_percent(interval=None)

    # Save the starting totals so we can subtract them later.
    prev_disk = psutil.disk_io_counters()
    prev_net = psutil.net_io_counters()
    prev_time = time.time()

    print(f"Recording {run_id} with label '{label}' (press Ctrl+C to stop)\n")

    try:
        while True:
            time.sleep(1)  # Wait one second between readings

            now = time.time()
            elapsed = now - prev_time  # Seconds since the last reading

            cpu = psutil.cpu_percent(interval=None)  # % CPU busy since last call
            ram = psutil.virtual_memory().percent    # % RAM in use

            disk = psutil.disk_io_counters()
            net = psutil.net_io_counters()

            # Convert the change in totals into bytes per second
            disk_read = (disk.read_bytes - prev_disk.read_bytes) / elapsed
            disk_write = (disk.write_bytes - prev_disk.write_bytes) / elapsed
            net_recv = (net.bytes_recv - prev_net.bytes_recv) / elapsed
            net_sent = (net.bytes_sent - prev_net.bytes_sent) / elapsed

            # Save this second's readings to the database
            db.insert_sample(
                conn, run_id, label, now,
                cpu, ram, disk_read, disk_write, net_recv, net_sent,
            )

            # Show the same readings on screen, in KB/s
            stamp = time.strftime("%H:%M:%S")
            print(
                f"{stamp}  CPU {cpu:5.1f}%  RAM {ram:5.1f}%  "
                f"Disk R {disk_read / 1024:8.1f} KB/s W {disk_write / 1024:8.1f} KB/s  "
                f"Net Rx {net_recv / 1024:8.1f} KB/s Tx {net_sent / 1024:8.1f} KB/s"
            )

            # Remember the current totals for the next second
            prev_disk, prev_net, prev_time = disk, net, now

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        conn.close()  # Always close the database file, even if the script stops early


if __name__ == "__main__":
    main()