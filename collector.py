"""Print live CPU, memory, disk and network readings once per second."""

import time

import psutil


def main():
    # The first cpu_percent call only starts measuring, so call it once before the loop.
    psutil.cpu_percent(interval=None)

    # Cumulative counters since boot. We store them now and subtract later to get rates.
    prev_disk = psutil.disk_io_counters()
    prev_net = psutil.net_io_counters()
    prev_time = time.time()

    print("Live metrics (press Ctrl+C to stop)\n")

    try:
        while True:
            time.sleep(1)

            now = time.time()
            elapsed = now - prev_time

            cpu = psutil.cpu_percent(interval=None)  # % busy since the last call
            ram = psutil.virtual_memory().percent     # % of RAM in use

            disk = psutil.disk_io_counters()
            net = psutil.net_io_counters()

            # Bytes per second = (new total - old total) / seconds elapsed
            disk_read = (disk.read_bytes - prev_disk.read_bytes) / elapsed
            disk_write = (disk.write_bytes - prev_disk.write_bytes) / elapsed
            net_recv = (net.bytes_recv - prev_net.bytes_recv) / elapsed
            net_sent = (net.bytes_sent - prev_net.bytes_sent) / elapsed

            stamp = time.strftime("%H:%M:%S")
            print(
                f"{stamp}  CPU {cpu:5.1f}%  RAM {ram:5.1f}%  "
                f"Disk R {disk_read / 1024:8.1f} KB/s W {disk_write / 1024:8.1f} KB/s  "
                f"Net Rx {net_recv / 1024:8.1f} KB/s Tx {net_sent / 1024:8.1f} KB/s"
            )

            prev_disk, prev_net, prev_time = disk, net, now

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()