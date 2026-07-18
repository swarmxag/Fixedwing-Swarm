"""
Standalone script to visualize the generated search grid + Bezier paths.
Run AFTER a search command has been issued so that the mission's
drone_*_grid.csv and drone_*_path.csv files exist.

Usage:
    python plot_search_grid.py
    python plot_search_grid.py --num_drones 3
    python plot_search_grid.py --run 20260717_143012
"""
import sys, os, csv, argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

SEARCH_MISSIONS_DIR = os.path.join(
    os.path.expanduser("~"), "Documents", "swarm_env", "missions", "search"
)

parser = argparse.ArgumentParser()
parser.add_argument("--num_drones", type=int, default=None)
parser.add_argument(
    "--run", type=str, default=None,
    help="Specific run_id folder under missions/search/ to plot; defaults to the most recent.",
)
args = parser.parse_args()

if not os.path.isdir(SEARCH_MISSIONS_DIR):
    print(f"ERROR: {SEARCH_MISSIONS_DIR} not found. Run a search command first.")
    sys.exit(1)

if args.run:
    RUN_DIR = os.path.join(SEARCH_MISSIONS_DIR, args.run)
else:
    runs = sorted(
        d for d in os.listdir(SEARCH_MISSIONS_DIR)
        if os.path.isdir(os.path.join(SEARCH_MISSIONS_DIR, d))
    )
    if not runs:
        print(f"ERROR: No search runs found under {SEARCH_MISSIONS_DIR}.")
        sys.exit(1)
    RUN_DIR = os.path.join(SEARCH_MISSIONS_DIR, runs[-1])

print(f"Plotting run: {RUN_DIR}")

# Auto-detect number of drones from drone_*_grid.csv files
if args.num_drones:
    num_drones = args.num_drones
else:
    num_drones = 0
    for i in range(1, 20):
        if os.path.exists(os.path.join(RUN_DIR, f"drone_{i}_grid.csv")):
            num_drones += 1
        else:
            break
    if num_drones == 0:
        print(f"ERROR: No drone_*_grid.csv files found in {RUN_DIR}.")
        sys.exit(1)

print(f"Plotting grid for {num_drones} drone(s) ...")

COLORS = cm.get_cmap("tab10", num_drones)

fig, ax = plt.subplots(figsize=(12, 10))
ax.set_title("Search Grid - Generated Trajectory vs Grid Waypoints", fontsize=14, fontweight="bold")
ax.set_xlabel("X (sim units,  1 unit = 2 m real-world)")
ax.set_ylabel("Y (sim units,  1 unit = 2 m real-world)")
ax.grid(True, linestyle="--", alpha=0.5)
ax.set_aspect("equal")

for drone_idx in range(num_drones):
    color = COLORS(drone_idx)
    label = f"Drone {drone_idx + 1}"

    # --- Grid waypoints (drone_N_grid.csv) ---
    grid_csv = os.path.join(RUN_DIR, f"drone_{drone_idx + 1}_grid.csv")
    grid_pts = []
    if os.path.exists(grid_csv):
        with open(grid_csv, "r") as f:
            for row in csv.reader(f):
                if row and row[0].strip():
                    grid_pts.append((float(row[0]), float(row[1])))
        if grid_pts:
            gx, gy = zip(*grid_pts)
            ax.scatter(gx, gy, color=color, s=80, marker="X", zorder=5,
                       label=f"{label} - grid waypoints")
            ax.plot(gx, gy, color=color, linestyle=":", linewidth=1.2, alpha=0.5)
            for n, (px, py) in enumerate(grid_pts):
                ax.annotate(str(n), (px, py), fontsize=6, color=color,
                            xytext=(4, 4), textcoords="offset points")
    else:
        print(f"  WARNING: {grid_csv} not found")

    # --- Bezier path (drone_N_path.csv) ---
    bezier_csv = os.path.join(RUN_DIR, f"drone_{drone_idx + 1}_path.csv")
    bezier_pts = []
    if os.path.exists(bezier_csv):
        with open(bezier_csv, "r") as f:
            for row in csv.reader(f):
                if row and row[0].strip():
                    bezier_pts.append((float(row[0]), float(row[1])))
        if bezier_pts:
            bx, by = zip(*bezier_pts)
            ax.plot(bx, by, color=color, linestyle="-", linewidth=2, zorder=4,
                    label=f"{label} - bezier path")
            ax.scatter(bx[0], by[0], color=color, marker="o", s=140,
                       edgecolors="black", linewidths=1.5, zorder=6)
            ax.scatter(bx[-1], by[-1], color=color, marker="s", s=140,
                       edgecolors="black", linewidths=1.5, zorder=6)
            ax.annotate(f"D{drone_idx+1} start", xy=(bx[0], by[0]),
                        fontsize=8, color=color, fontweight="bold",
                        xytext=(8, 6), textcoords="offset points")
    else:
        print(f"  WARNING: {bezier_csv} not found")

handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, loc="best", fontsize=8, framealpha=0.9)
ax.text(0.01, 0.01,
        "Circle=start | Square=end | X=grid waypoints | line=bezier path | numbers=waypoint index",
        transform=ax.transAxes, fontsize=7, color="gray", verticalalignment="bottom")

plt.tight_layout()
out_path = os.path.join(RUN_DIR, "search_grid_plot.png")
plt.savefig(out_path, dpi=150)
print(f"Saved: {out_path}")
plt.show(block=True)
