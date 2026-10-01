#!/usr/bin/env python3
"""Aggregate exp/results/n10_*.json into a stock-vs-slim table (mean and min–max per metric)."""
import glob, json, statistics

METRICS = [
    ("launches", "Cold launches completed (5 min)"),
    ("launch_fail", "Launches timed out"),
    ("launch_ms_p50", "Launch p50 (ms)"),
    ("launch_ms_p90", "Launch p90 (ms)"),
    ("boot_s_median", "Boot median (s)"),
    ("boot_s_max", "Boot slowest (s)"),
    ("swapouts_during", "Host swapouts (pages)"),
    ("swap_growth_mb", "Host swap growth (MB)"),
    ("fleet_footprint_mb", "Fleet phys_footprint (MB)"),
    ("fleet_rss_mb", "Fleet resident (MB)"),
    ("fleet_cpu_pct", "Fleet CPU (% of one core)"),
]

import sys
sizes = sys.argv[1:] or ["10"]

def cell(xs):
    xs = [x for x in xs if x is not None]
    if not xs: return "n/a"
    return f"{statistics.mean(xs):,.0f} ({min(xs):,.0f}–{max(xs):,.0f})"

VARIANTS = ["stock", "slim", "atd", "atdslim"]
PREFIX = "app_" if "--app" in sys.argv else "focus_" if "--focus" in sys.argv else ""
sizes = [x for x in sizes if not x.startswith("--")]

def table(n):
  runs = {v: [] for v in VARIANTS}
  for f in sorted(glob.glob(f"exp/results/{PREFIX}n{n}_*.json")):
    s = json.load(open(f))["summary"]
    runs[s["label"].split("_")[-2]].append(s)
  vs = [v for v in VARIANTS if runs[v]]
  if len(vs) < 2: return
  print(f"\n### {n} emulators")
  print("runs:", {v: len(runs[v]) for v in vs})
  print("| Metric | " + " | ".join(vs) + " |\n|---|" + "---|" * len(vs))
  for key, name in METRICS:
    print(f"| {name} | " + " | ".join(cell([r[key] for r in runs[v]]) for v in vs) + " |")
  loads = [r.get("host_before", {}).get("load1") for v in vs for r in runs[v]]
  print("host load1 before each run:", [round(x) for x in loads if x is not None] or "not recorded")

for n in sizes: table(n)
