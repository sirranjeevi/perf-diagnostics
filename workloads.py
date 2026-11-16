"""Workloads that create known patterns for labeled data: idle, cpu, memory, disk."""

import multiprocessing  # Starts one busy process per CPU core
import os               # File paths and file removal
import sys              # Reads the command-line arguments
import tempfile         # Gives us the system temp folder
import time             # Clock and sleep


def _busy(seconds):
    # Runs a tight loop until the time is up. Used by run_cpu.
    end = time.time() + seconds
    while time.time() < end:
        pass


def run_idle(seconds):
    # Does nothing for the whole time
    time.sleep(seconds)


def run_cpu(seconds):
    # Starts one busy process per core, so the overall CPU percentage rises clearly
    procs = [multiprocessing.Process(target=_busy, args=(seconds,))
             for _ in range(os.cpu_count() or 1)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()  # Wait until each busy process finishes


def run_memory(seconds, megabytes=500):
    # Reserves a block of RAM and writes to each memory page, so Windows really uses it
    block = bytearray(megabytes * 1024 * 1024)
    for i in range(0, len(block), 4096):
        block[i] = 1
    time.sleep(seconds)  # Hold the memory for the whole run
    del block            # Release it at the end


def run_disk(seconds, chunk_mb=20):
    # Rewrites one temporary file over and over, forcing each write to disk
    path = os.path.join(tempfile.gettempdir(), "perf_diag_disk_test.bin")
    data = os.urandom(chunk_mb * 1024 * 1024)
    end = time.time() + seconds
    with open(path, "wb") as f:
        while time.time() < end:
            f.seek(0)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())  # Wait until the operating system confirms the write
    os.remove(path)


WORKLOADS = {"idle": run_idle, "cpu": run_cpu, "memory": run_memory, "disk": run_disk}

if __name__ == "__main__":
    # Usage: python workloads.py <kind> <seconds>, for example: python workloads.py cpu 20
    kind = sys.argv[1]
    seconds = float(sys.argv[2])
    WORKLOADS[kind](seconds)