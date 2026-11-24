"""Build the dashboard page: charts for one run, plus the saved alerts table."""

import html                              # Escapes text so it displays safely in a web page
import time                              # Converts timestamps to clock times

import plotly.graph_objects as go        # Plotly's chart tools

import db                                # Database connection


def latest_run_id(conn):
    # Returns the name of the run with the newest reading, or None if the table is empty
    row = conn.execute("SELECT run_id FROM samples ORDER BY ts DESC LIMIT 1").fetchone()
    return row[0] if row else None


def clock_labels(rows):
    # Turns each timestamp in the rows into a clock time for the chart's x-axis
    return [time.strftime("%H:%M:%S", time.localtime(r[0])) for r in rows]


def readings_chart(conn, run_id):
    # Line chart of CPU % and RAM % over time for one run
    rows = conn.execute(
        "SELECT ts, cpu_percent, ram_percent FROM samples WHERE run_id = ? ORDER BY ts",
        (run_id,),
    ).fetchall()                          # Each row is (timestamp, cpu, ram)

    times = clock_labels(rows)
    fig = go.Figure()                     # An empty chart we add lines to
    fig.add_trace(go.Scatter(x=times, y=[r[1] for r in rows], name="CPU %"))   # CPU line
    fig.add_trace(go.Scatter(x=times, y=[r[2] for r in rows], name="RAM %"))   # RAM line
    fig.update_layout(title=f"CPU and RAM for {run_id}", xaxis_title="Time",
                      yaxis_title="Percent", height=420)
    return fig


def disk_chart(conn, run_id):
    # Line chart of disk write speed in KB/s over time for one run
    rows = conn.execute(
        "SELECT ts, disk_write_bps FROM samples WHERE run_id = ? ORDER BY ts",
        (run_id,),
    ).fetchall()

    times = clock_labels(rows)
    fig = go.Figure()
    # Divide by 1024 to convert bytes per second into KB per second
    fig.add_trace(go.Scatter(x=times, y=[r[1] / 1024 for r in rows], name="Disk write KB/s"))
    fig.update_layout(title=f"Disk writes for {run_id}", xaxis_title="Time",
                      yaxis_title="KB/s", height=340)
    return fig


def alerts_html(conn):
    # Builds an HTML table of the 20 most recent alerts
    rows = conn.execute(
        "SELECT run_id, ts, value, message FROM alerts ORDER BY ts DESC LIMIT 20"
    ).fetchall()
    if not rows:
        return "<p>No alerts saved yet.</p>"

    # One table row per alert. html.escape stops message text from being read as HTML.
    items = "".join(
        f"<tr><td>{html.escape(run)}</td>"
        f"<td>{time.strftime('%H:%M:%S', time.localtime(ts))}</td>"
        f"<td>{value:.1f}%</td>"
        f"<td>{html.escape(message)}</td></tr>"
        for run, ts, value, message in rows
    )
    return ("<table><tr><th>Run</th><th>Time</th><th>CPU</th><th>Message</th></tr>"
            f"{items}</table>")


def build_page(conn, run_id=None):
    # Builds the full HTML page. If no run is given, the newest run is shown.
    run_id = run_id or latest_run_id(conn)
    if run_id is None:
        return "<h1>No data yet. Run collector.py or fault_inject.py first.</h1>"

    # The first chart embeds the Plotly library, so the page works offline.
    # The second chart reuses it, so the library is included only once.
    cpu_part = readings_chart(conn, run_id).to_html(full_html=False, include_plotlyjs=True)
    disk_part = disk_chart(conn, run_id).to_html(full_html=False, include_plotlyjs=False)

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Performance Diagnostics</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; max-width: 1000px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 6px; text-align: left; }}
  </style>
</head>
<body>
  <h1>Performance Diagnostics</h1>
  <p>Showing run: <b>{html.escape(run_id)}</b>. Add ?run_id=NAME to the address to pick another run.</p>
  {cpu_part}
  {disk_part}
  <h2>Saved alerts</h2>
  {alerts_html(conn)}
</body>
</html>"""