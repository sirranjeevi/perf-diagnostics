"""Sustained-threshold alert logic and a top-process snapshot."""

import time

import psutil


class SustainedAlert:
    """Fires once when a value stays above a threshold for N readings in a row."""

    def __init__(self, threshold, seconds):
        self.threshold = threshold  # The limit, for example 80 (%)
        self.seconds = seconds      # How many readings in a row are needed, for example 10
        self.streak = 0             # How many readings in a row have been above the limit
        self.active = False         # True after an alert fired, until the value drops back down

    def update(self, value):
        """Feed one reading. Returns True only on the reading where the alert fires."""
        if value <= self.threshold:
            # Value is below the limit: the streak is broken, so reset everything
            self.streak = 0
            self.active = False
            return False

        # Value is above the limit: extend the streak
        self.streak += 1

        # Fire only when the streak is long enough and we haven't already fired for this episode
        if self.streak >= self.seconds and not self.active:
            self.active = True
            return True
        return False


def top_processes(count=5, sample_seconds=1.0):
    """Return the busiest processes as (name, share_of_total_cpu_percent) tuples."""
    cores = psutil.cpu_count() or 1  # Number of CPU cores, used to convert per-core % to whole-CPU %

    # Step 1: start measuring every process
    procs = []
    for p in psutil.process_iter():
        try:
            if p.pid == 0:
                continue  # Skip the "System Idle Process": it's unused CPU time, not work
            p.cpu_percent(interval=None)  # First call starts the measurement
            procs.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue  # Skip processes that closed or that we can't read

    # Step 2: wait so each process has real usage to measure
    time.sleep(sample_seconds)

    # Step 3: read each process's usage and convert it to a share of the whole CPU
    readings = []
    for p in procs:
        try:
            per_core = p.cpu_percent(interval=None)  # Can exceed 100 on multi-core machines
            share = per_core / cores                 # Now 0-100 across the whole CPU
            readings.append((p.name(), share))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Step 4: sort busiest first and keep the top few
    readings.sort(key=lambda item: item[1], reverse=True)
    return readings[:count]


def format_top(readings):
    """Turn [('chrome.exe', 45.0), ...] into 'chrome.exe (45%); ...' for storing and printing."""
    return "; ".join(f"{name} ({cpu:.0f}%)" for name, cpu in readings)