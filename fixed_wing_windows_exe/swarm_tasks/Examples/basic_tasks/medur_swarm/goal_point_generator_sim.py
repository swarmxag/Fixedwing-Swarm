"""Standalone visual check for the "Automate Goals" layout (no SITL, no GCS).

Run:  python -m medur_swarm.goal_point_generator_sim

Plots the per-UAV loiter centers and circles produced by
goal_point_generator.generate_loiter_goal_points from ONE operator point,
then regenerates at a larger radius to show the circles re-space so they
never overlap.

This does NOT run the real dispatch loop. In the live system the flow is:
  SwarmPanel "Automate Goals" -> app.py autogoal_socket -> swarm.py UDP
  -> medur_swarm/tasks/goal.run_autogoal_command -> assign_autogoal_tasks,
and an on-board loiter-radius change (Swarm UAVs tab -> Save) additionally
fires autogoal_radius_socket -> goal.regenerate_autogoal.
"""

from math import cos, radians, sin

import matplotlib.pyplot as plt

from medur_swarm.goal_point_generator import (
    generate_loiter_goal_points,
    loiter_center_spacing,
)

GOAL_LAT, GOAL_LON = 26.96256333, 70.95419682
NUM_UAVS = 5
BEARING_DEG = 90.0
SAFETY_MARGIN_M = 50.0
RADII_M = [400.0, 700.0]  # first = initial, rest = mid-flight radius changes


def _to_local_m(lat, lon):
    m_per_deg_lat = 111320.0
    m_per_deg_lon = 111320.0 * cos(radians(GOAL_LAT))
    return (lon - GOAL_LON) * m_per_deg_lon, (lat - GOAL_LAT) * m_per_deg_lat


def main():
    fig, ax = plt.subplots(figsize=(11, 5))
    ring_theta = [radians(t) for t in range(0, 361, 3)]
    colors = plt.cm.viridis([i / max(NUM_UAVS - 1, 1) for i in range(NUM_UAVS)])

    for step, radius in enumerate(RADII_M):
        pts = generate_loiter_goal_points(
            GOAL_LAT, GOAL_LON, NUM_UAVS, radius, BEARING_DEG, SAFETY_MARGIN_M
        )
        style = "-" if step == 0 else "--"
        label_r = f"r={radius:.0f} m (spacing {loiter_center_spacing(radius, SAFETY_MARGIN_M):.0f} m)"
        for i, p in enumerate(pts):
            cx, cy = _to_local_m(p["goal_lat"], p["goal_lon"])
            ax.plot(
                [cx + radius * sin(t) for t in ring_theta],
                [cy + radius * cos(t) for t in ring_theta],
                style,
                color=colors[i],
                linewidth=1.2,
                label=label_r if i == 0 else None,
            )
            ax.plot(cx, cy, "o", color=colors[i], markersize=5)
            if step == 0:
                ax.annotate(
                    f"UAV{i + 1}",
                    (cx, cy),
                    textcoords="offset points",
                    xytext=(0, 8),
                    ha="center",
                    fontsize=8,
                )
        print(
            f"r={radius:.0f}: "
            + ", ".join(
                f"UAV{p['uav_id']}@{p['distance_from_center_m']:.0f}m" for p in pts
            )
        )

    ax.plot(0, 0, "k+", markersize=14)
    ax.set_aspect("equal")
    ax.set_title(
        f"Automate Goals -- {NUM_UAVS} UAVs, bearing {BEARING_DEG:.0f} deg\n"
        "solid = initial radius, dashed = after on-board radius change"
    )
    ax.set_xlabel("east (m)")
    ax.set_ylabel("north (m)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
