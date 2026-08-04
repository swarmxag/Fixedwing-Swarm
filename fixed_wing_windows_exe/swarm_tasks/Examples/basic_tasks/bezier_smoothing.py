import numpy as np


def get_heading_to_target(current_pos, target_pos):
    """Compute the heading angle required to face the target waypoint."""
    dx, dy = target_pos[0] - current_pos[0], target_pos[1] - current_pos[1]
    return np.arctan2(dy, dx)


def normalize_angle(angle):
    """Ensure angles stay within -pi to pi range."""
    return (angle + np.pi) % (2 * np.pi) - np.pi


def predict_path_with_waypoints(
    initial_pos, initial_heading, speed, turn_rate, waypoints, dt=0.1, max_iter=5000
):
    """Predicts the aircraft's turn-rate-limited movement through waypoints.

    Parameters:
    - initial_pos: (x, y) tuple for the start position
    - initial_heading: Initial heading in radians
    - speed: Constant velocity (m/s)
    - turn_rate: Max turn rate (rad/s)
    - waypoints: List of (x, y) waypoints
    - dt: Time step (s)
    - max_iter: Prevent infinite loops by limiting iterations

    Returns:
    - A list of (x, y) positions representing the predicted path.
    """
    x, y = initial_pos
    theta = initial_heading
    path = [(x, y)]

    for target in waypoints:
        iteration = 0
        while np.hypot(target[0] - x, target[1] - y) > speed * dt:
            if iteration > max_iter:
                print(
                    f"Warning: Exceeded max iterations while moving to waypoint {target}, skipping!"
                )
                break  # Prevent infinite loop

            desired_theta = get_heading_to_target((x, y), target)

            heading_diff = normalize_angle(
                desired_theta - theta
            )  # Normalize angle difference

            # Adjust heading smoothly within the turn rate limit
            theta += np.clip(heading_diff, -turn_rate * dt, turn_rate * dt)

            # Move the aircraft forward
            x += speed * np.cos(theta) * dt
            y += speed * np.sin(theta) * dt

            path.append((x, y))
            iteration += 2
    return np.array(path)


def generate_bezier_path(
    waypoints, speed, turn_rate, initial_heading=0.0, samples=10, max_iter=500000
):
    """Smooths one drone's raw grid waypoints (row-boundary points plus a
    turn-around overshoot point every 3rd entry -- see GridFormation /
    CreateGridsForSpecifiedAreaAndSpecifiedDrones) into a flyable path.

    This is the single canonical bezier-smoothing implementation search,
    split, and specific-split all call, so their turn-around curves stay
    identical by construction instead of drifting out of sync (as the old
    per-class copies of this loop did).

    Returns (result, is_bezier): result is the smoothed point list, is_bezier
    a same-length list of bools flagging which points came from the bezier
    turn (True) vs are original grid waypoints (False).
    """
    result = [waypoints[0]]
    is_bezier = [False]
    alternative = False

    for i in range(1, len(waypoints) - 1, 3):
        if i + 2 < len(waypoints) - 1:  # Ensure we don't include the last line
            if alternative:
                heading = np.radians(180)
                alternative = False
            else:
                heading = initial_heading
                alternative = True
            data = []
            path1 = predict_path_with_waypoints(
                waypoints[i],
                heading,
                speed,
                turn_rate,
                [waypoints[i], waypoints[i + 1], waypoints[i + 2]],
                max_iter=max_iter,
            )
            sampled_indices = np.linspace(0, len(path1) - 1, samples, dtype=int)
            sampled_points = path1[sampled_indices]
            for sample_point in sampled_points:
                data.append(sample_point.tolist())
            # sampled_points[0] is path1[0], i.e. waypoints[i] itself (the
            # bezier segment's start), and the trailing waypoints[i + 2] is
            # its end -- both are original waypoints, not generated points.
            data_flags = [False] + [True] * (len(sampled_points) - 1) + [False]
            data.append(waypoints[i + 2])
            result.extend(data)
            is_bezier.extend(data_flags)
        else:
            j = i
            while j <= len(waypoints) - 1:
                result.append(waypoints[j])
                is_bezier.append(False)
                j += 1
    return result, is_bezier
