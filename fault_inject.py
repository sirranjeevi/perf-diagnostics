"""Create labeled runs: start each workload, record one reading per second, save with its label."""

import subprocess  # Starts workloads.py as a separate process
import sys         # Reads command-line arguments
import time        # Clock and sleep

import psutil      # Reads system stats

import db          # Saves rows to metrics.db

CLASSES = ["idle", "cpu", "memory", "disk"]  # The four labels we train on


def record_run(conn, run_id, label, seconds):
    # Start the counters so the first rate is measured from now
    psutil.cpu_percent(interval=None)
    prev_disk = psutil.disk_io_counters()
    prev_net = psutil.net_io_counters()
    prev_time = time.time()

    for _ in range(seconds):
        time.sleep(1)  # One reading per second

        now = time.time()
        elapsed = now - prev_time

        cpu = psutil.cpu_percent(interval=None)   # % CPU busy since last call
        ram = psutil.virtual_memory().percent     # % RAM in use
        disk = psutil.disk_io_counters()          # Running disk totals
        net = psutil.net_io_counters()            # Running network totals

        # Convert the change in totals into bytes per second
        disk_read = (disk.read_bytes - prev_disk.read_bytes) / elapsed
        disk_write = (disk.write_bytes - prev_disk.write_bytes) / elapsed
        net_recv = (net.bytes_recv - prev_net.bytes_recv) / elapsed
        net_sent = (net.bytes_sent - prev_net.bytes_sent) / elapsed

        db.insert_sample(conn, run_id, label, now,
                         cpu, ram, disk_read, disk_write, net_recv, net_sent)

        prev_disk, prev_net, prev_time = disk, net, now


def main():
    # Usage: python fault_inject.py [runs_per_class] [seconds_per_run]
    # Defaults: 10 runs per class, 20 seconds each
    runs_per_class = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    conn = db.connect()
    stamp = int(time.time())  # Makes run names unique for this batch

    for label in CLASSES:
        for i in range(1, runs_per_class + 1):
            run_id = f"{label}-{i:02d}-{stamp}"
            print(f"Starting {run_id} ...")

            # Start the workload in its own process, for the same number of seconds
            child = subprocess.Popen([sys.executable, "workloads.py", label, str(seconds)])
            record_run(conn, run_id, label, seconds)  # Record readings while it runs
            child.wait()                              # Make sure the workload has finished

            print("  done")

    conn.close()
    print("All runs finished.")


if __name__ == "__main__":
    main()