"""Print live metrics once per second, save readings, and raise CPU alerts."""

import sys
import time

import psutil

import db
from alerts import SustainedAlert, top_processes, format_top

CPU_LIMIT = 80   # Alert when CPU is above this percent...
CPU_SECONDS = 10 # ...for this many readings in a row


def main():
    # Label comes from the command line, for example: python collector.py cpu
    label = sys.argv[1] if len(sys.argv) > 1 else "idle"

    # Each run gets its own name, based on the start time
    run_id = f"run-{int(time.time())}"

    conn = db.connect()                     # Opens metrics.db and makes sure both tables exist
    cpu_alert = SustainedAlert(CPU_LIMIT, CPU_SECONDS)  # The CPU rule

    psutil.cpu_percent(interval=None)       # Start the CPU measurement
    prev_disk = psutil.disk_io_counters()   # Save starting disk totals
    prev_net = psutil.net_io_counters()     # Save starting network totals
    prev_time = time.time()

    print(f"Recording {run_id} with label '{label}' (press Ctrl+C to stop)\n")

    try:
        while True:
            time.sleep(1)  # One reading per second

            now = time.time()
            elapsed = now - prev_time

            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent

            disk = psutil.disk_io_counters()
            net = psutil.net_io_counters()

            # Convert change in totals to bytes per second
            disk_read = (disk.read_bytes - prev_disk.read_bytes) / elapsed
            disk_write = (disk.write_bytes - prev_disk.write_bytes) / elapsed
            net_recv = (net.bytes_recv - prev_net.bytes_recv) / elapsed
            net_sent = (net.bytes_sent - prev_net.bytes_sent) / elapsed

            # Save this second's readings
            db.insert_sample(
                conn, run_id, label, now,
                cpu, ram, disk_read, disk_write, net_recv, net_sent,
            )

            # Check the CPU rule with this reading
            if cpu_alert.update(cpu):
                # The rule fired: look up the busy processes and save the alert.
                # top_processes() waits about 1 second, so this loop pauses briefly.
                top = format_top(top_processes())
                message = (
                    f"CPU above {CPU_LIMIT}% for {CPU_SECONDS} seconds. "
                    f"Top processes at this time: {top}. Check these first."
                )
                db.insert_alert(
                    conn, run_id, now, "cpu_percent", cpu,
                    CPU_LIMIT, CPU_SECONDS, message, top,
                )
                print(f"  ALERT: {message}")

            stamp = time.strftime("%H:%M:%S")
            print(
                f"{stamp}  CPU {cpu:5.1f}%  RAM {ram:5.1f}%  "
                f"Disk R {disk_read / 1024:8.1f} KB/s W {disk_write / 1024:8.1f} KB/s  "
                f"Net Rx {net_recv / 1024:8.1f} KB/s Tx {net_sent / 1024:8.1f} KB/s"
            )

            prev_disk, prev_net, prev_time = disk, net, now

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        conn.close()  # Always close the database file


if __name__ == "__main__":
    main()