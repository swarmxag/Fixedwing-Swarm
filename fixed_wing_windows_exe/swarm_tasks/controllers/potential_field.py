# import swarm_tasks.utils as utils
# import swarm_tasks.controllers.command as cmd
# #import swarm_tasks.simulation as sim

# import numpy as np
# from shapely.geometry import Point, Polygon
# from shapely.ops import nearest_points


# field_weights = {'bots':150, 'obstacles':1, 'borders':1, 'goal':-3, 'items':0}

# def get_field(i,point, goal,sim, \
# 	order=2, \
# 	weights=field_weights, \
# 	max_dist=2, \
# 	goal_set = True, \
# 	goal_order = 0,\
# 	item_types = []):
# 	"""
# 	Args:
# 		poiint: (x,y) tuple
# 		sim: Simulation object
# 		order: r^(-pow)
# 		weights: weight given to field from bots, obstacles, goal, etc.
# 		max_dist: Max distance of objects (except goal) exerting a field
# 		goal_set: Bool; whether a goal point has been given
# 		goal: (x,y) tuple
# 		goal_order:
# 		item_types: List containing types of items that generate field
# 	Returns:
# 		velocity vector as Cmd object
# 	"""
# 	vec = np.array([0.0,0.0])

# 	p = Point(point[0],point[1])
# 	#Obstacle field
# 	for o in sim.env.obstacles:
# 		p1,p2 = nearest_points(p,o)

# 		r = p2.distance(p1)

# 		if r>max_dist:
# 			continue

# 		dir_vec = -np.array([p2.x-p1.x, p2.y-p1.y])
# 		dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))

# 		field = weights['obstacles']/np.abs(np.power(r+0.001, order))

# 		vec+=field*dir_vec

# 	#Robots field
# 	for b in sim.swarm:
# 		pos = Point(b.get_position())
# 		if pos.x == point[0] and pos.y == point[1]:
# 			continue
# 		r = pos.distance(p)

# 		if r>max_dist:
# 			continue

# 		dir_vec = -np.array([pos.x-p.x, pos.y-p.y])
# 		dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))

# 		field = weights['bots']/np.abs(np.power(r+0.001, order))

# 		vec+=field*dir_vec

# 	#Boundaries
# 	#X
# 	if point[0] < max_dist:
# 		r = point[0]
# 		vec[0]+=weights['borders']/np.abs(np.power(r+0.001, order))
# 	elif point[0] > sim.size[0]-max_dist:
# 		r = sim.size[0]-point[0]
# 		vec[0]-=weights['borders']/np.abs(np.power(r+0.001, order))
# 	#Y
# 	if point[1] < max_dist:
# 		r = point[1]
# 		vec[1]+=weights['borders']/np.abs(np.power(r+0.001, order))
# 	elif point[1] > sim.size[1]-max_dist:
# 		r = sim.size[1]-point[1]
# 		vec[1]-=weights['borders']/np.abs(np.power(r+0.001, order))

# 	#Goal
# 	if goal_set:
# 		r = p.distance(Point(goal[0],goal[1]))
# 		if r>0.4:
# 			dir_vec = -np.array([goal[0]-p.x, goal[1]-p.y])
# 			dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))
# 			field = weights['goal']/np.abs(np.power(r+0.001, goal_order))
# 			vec+=field*dir_vec


# 	#Items
# 	for o in sim.contents.items:
# 		if not ((o.type in item_types) or ('all' in item_types)):
# 			continue
# 		p1,p2 = nearest_points(p,o.polygon)

# 		r = p2.distance(p1)

# 		if r>max_dist:
# 			continue

# 		dir_vec = -np.array([p2.x-p1.x, p2.y-p1.y])
# 		dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec+0.001))

# 		field = weights['items']/np.abs(np.power(r+0.001, order))

# 		vec+=field*dir_vec


# 	return cmd.Cmd(vec.tolist())


# def exp_field(point,sim, \
# 	order=2, \
# 	weights=field_weights, \
# 	max_dist=2, \
# 	goal_set = False,goal=None, \
# 	goal_order = 0,\
# 	item_types = []):
# 	"""
# 	Args:
# 		poiint: (x,y) tuple
# 		sim: Simulation object
# 		order: r^(-pow)
# 		weights: weight given to field from bots, obstacles, goal, etc.
# 		max_dist: Max distance of objects (except goal) exerting a field
# 		goal_set: Bool; whether a goal point has been given
# 		goal: (x,y) tuple
# 		goal_order:
# 		item_types: List containing types of items that generate field
# 	Returns:
# 		velocity vector as Cmd object
# 	"""
# 	vec = np.array([0.0,0.0])

# 	p = Point(point[0],point[1])
# 	#Obstacle field
# 	for o in sim.env.obstacles:
# 		p1,p2 = nearest_points(p,o)

# 		r = p2.distance(p1)

# 		if r>max_dist:
# 			continue

# 		dir_vec = -np.array([p2.x-p1.x, p2.y-p1.y])
# 		dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))

# 		field = weights['obstacles']/np.abs(np.power(r+0.001, order))

# 		vec+=field*dir_vec

# 	#Robots field
# 	for b in sim.swarm:
# 		pos = Point(b.get_position())
# 		if pos.x == point[0] and pos.y == point[1]:
# 			continue
# 		r = pos.distance(p)

# 		if r>max_dist:
# 			continue

# 		dir_vec = -np.array([pos.x-p.x, pos.y-p.y])
# 		dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))

# 		field = weights['bots']/np.abs(np.power(r+0.001, order))

# 		vec+=field*dir_vec

# 	#Boundaries
# 	#X
# 	if point[0] < max_dist:
# 		r = point[0]
# 		vec[0]+=weights['borders']/np.abs(np.power(r+0.001, order))
# 	elif point[0] > sim.size[0]-max_dist:
# 		r = sim.size[0]-point[0]
# 		vec[0]-=weights['borders']/np.abs(np.power(r+0.001, order))
# 	#Y
# 	if point[1] < max_dist:
# 		r = point[1]
# 		vec[1]+=weights['borders']/np.abs(np.power(r+0.001, order))
# 	elif point[1] > sim.size[1]-max_dist:
# 		r = sim.size[1]-point[1]
# 		vec[1]-=weights['borders']/np.abs(np.power(r+0.001, order))

# 	#Goal
# 	if goal_set:
# 		r = p.distance(Point(goal[0],goal[1]))
# 		if r>0.1:
# 			dir_vec = -np.array([goal[0]-p.x, goal[1]-p.y])
# 			dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))
# 			field = weights['goal']/np.abs(np.power(r+0.001, goal_order))
# 			vec+=field*dir_vec


# 	#Items
# 	for o in sim.contents.items:
# 		if not ((o.type in item_types) or ('all' in item_types)):
# 			continue
# 		p1,p2 = nearest_points(p,o.polygon)

# 		r = p2.distance(p1)

# 		if r>max_dist:
# 			continue

# 		dir_vec = -np.array([p2.x-p1.x, p2.y-p1.y])
# 		dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec+0.001))

# 		field = weights['items']/np.abs(np.power(r+0.001, order))

# 		vec+=field*dir_vec


# 	return cmd.Cmd(vec.tolist())


# def velocity(point, sim, \
# 	order=2, \
# 	weights=field_weights, \
# 	max_dist=2, \
# 	goal_set = False, goal=None, \
# 	goal_order = 0,\
# 	item_types = []):
# 	"""
# 	Args:
# 		poiint: (x,y) tuple
# 		sim: Simulation object
# 		order: r^(-pow)
# 		weights: weight given to field from bots, obstacles, goal, etc.
# 		max_dist: Max distance of objects (except goal) exerting a field
# 		goal_set: Bool; whether a goal point has been given
# 		goal: (x,y) tuple
# 		goal_order:
# 		item_types: List containing types of items that generate field
# 	Returns:
# 		velocity vector as Cmd object
# 	"""
# 	vec = np.array([0.0,0.0])

# 	p = Point(point[0],point[1])


# 	#print("!!!!!!!!!!")
# 	# If the robot is close to the goal, set its velocity to zero and mark the goal as reached
# 	vec = np.array([0.0, 0.0])
# 	return cmd.Cmd(vec.tolist())


import swarm_tasks.utils as utils
import swarm_tasks.controllers.command as cmd

# import swarm_tasks.simulation as sim

import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points

field_weights = {"bots": 150, "obstacles": 1, "borders": 1, "goal": -3, "items": 0}

# Two GPS fixes can quantise to the same simulated point.  A zero-length
# position difference has no geometric "away" direction, but treating every
# bot at that point as self makes both aircraft receive the same goal command
# and remain coupled.  This is deliberately tiny: it is used only to choose a
# direction for an exact-overlap recovery, not as a replacement for the normal
# distance-based repulsion.
OVERLAP_EPSILON = 1e-6


def get_field(
    i,
    point,
    goal,
    sim,
    order=2,
    weights=field_weights,
    max_dist=2,
    goal_set=True,
    goal_order=0,
    item_types=[],
):
    """
    Args:
            poiint: (x,y) tuple
            sim: Simulation object
            order: r^(-pow)
            weights: weight given to field from bots, obstacles, goal, etc.
            max_dist: Max distance of objects (except goal) exerting a field
            goal_set: Bool; whether a goal point has been given
            goal: (x,y) tuple
            goal_order:
            item_types: List containing types of items that generate field
    Returns:
            velocity vector as Cmd object
    """
    vec = np.array([0.0, 0.0])

    p = Point(point[0], point[1])
    # Obstacle field
    for o in sim.env.obstacles:
        p1, p2 = nearest_points(p, o)

        r = p2.distance(p1)

        if r > max_dist:
            continue

        dir_vec = -np.array([p2.x - p1.x, p2.y - p1.y])
        dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))

        field = weights["obstacles"] / np.abs(np.power(r + 0.001, order))

        vec += field * dir_vec

    # Robots field
    for j, b in enumerate(sim.swarm):
        if j == i:
            continue
        pos = Point(b.get_position())
        r = pos.distance(p)

        if r > max_dist:
            continue

        if r <= OVERLAP_EPSILON:
            # Give the pair opposite, repeatable escape headings.  Using the
            # pair (rather than random headings) prevents command-to-command
            # jitter and lets a fixed-wing aircraft fly forward while it
            # separates instead of repeatedly changing heading in place.
            lo, hi = sorted((i, j))
            pair_angle = (lo * 2.399963229728653 + hi * 0.9272952180016122) % (
                2 * np.pi
            )
            if i > j:
                pair_angle += np.pi
            dir_vec = np.array([np.cos(pair_angle), np.sin(pair_angle)])
            r = OVERLAP_EPSILON
        else:
            dir_vec = -np.array([pos.x - p.x, pos.y - p.y])
            dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))

        field = weights["bots"] / np.abs(np.power(r + 0.001, order))

        vec += field * dir_vec

    # Boundaries
    # X
    if point[0] < max_dist:
        r = point[0]
        vec[0] += weights["borders"] / np.abs(np.power(r + 0.001, order))
    elif point[0] > sim.size[0] - max_dist:
        r = sim.size[0] - point[0]
        vec[0] -= weights["borders"] / np.abs(np.power(r + 0.001, order))
    # Y
    if point[1] < max_dist:
        r = point[1]
        vec[1] += weights["borders"] / np.abs(np.power(r + 0.001, order))
    elif point[1] > sim.size[1] - max_dist:
        r = sim.size[1] - point[1]
        vec[1] -= weights["borders"] / np.abs(np.power(r + 0.001, order))

    # Goal
    if goal_set:
        r = p.distance(Point(goal[0], goal[1]))
        if r > 0.4:
            dir_vec = -np.array([goal[0] - p.x, goal[1] - p.y])
            dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))
            field = weights["goal"] / np.abs(np.power(r + 0.001, goal_order))
            vec += field * dir_vec

    # Items
    for o in sim.contents.items:
        if not ((o.type in item_types) or ("all" in item_types)):
            continue
        p1, p2 = nearest_points(p, o.polygon)

        r = p2.distance(p1)

        if r > max_dist:
            continue

        dir_vec = -np.array([p2.x - p1.x, p2.y - p1.y])
        dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec + 0.001))

        field = weights["items"] / np.abs(np.power(r + 0.001, order))

        vec += field * dir_vec

    return cmd.Cmd(vec.tolist())


def exp_field(
    point,
    sim,
    order=2,
    weights=field_weights,
    max_dist=2,
    goal_set=False,
    goal=None,
    goal_order=0,
    item_types=[],
):
    """
    Args:
            poiint: (x,y) tuple
            sim: Simulation object
            order: r^(-pow)
            weights: weight given to field from bots, obstacles, goal, etc.
            max_dist: Max distance of objects (except goal) exerting a field
            goal_set: Bool; whether a goal point has been given
            goal: (x,y) tuple
            goal_order:
            item_types: List containing types of items that generate field
    Returns:
            velocity vector as Cmd object
    """
    vec = np.array([0.0, 0.0])

    p = Point(point[0], point[1])
    # Obstacle field
    for o in sim.env.obstacles:
        p1, p2 = nearest_points(p, o)

        r = p2.distance(p1)

        if r > max_dist:
            continue

        dir_vec = -np.array([p2.x - p1.x, p2.y - p1.y])
        dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))

        field = weights["obstacles"] / np.abs(np.power(r + 0.001, order))

        vec += field * dir_vec

    # Robots field
    for b in sim.swarm:
        pos = Point(b.get_position())
        if pos.x == point[0] and pos.y == point[1]:
            continue
        r = pos.distance(p)

        if r > max_dist:
            continue

        dir_vec = -np.array([pos.x - p.x, pos.y - p.y])
        dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))

        field = weights["bots"] / np.abs(np.power(r + 0.001, order))

        vec += field * dir_vec

    # Boundaries
    # X
    if point[0] < max_dist:
        r = point[0]
        vec[0] += weights["borders"] / np.abs(np.power(r + 0.001, order))
    elif point[0] > sim.size[0] - max_dist:
        r = sim.size[0] - point[0]
        vec[0] -= weights["borders"] / np.abs(np.power(r + 0.001, order))
    # Y
    if point[1] < max_dist:
        r = point[1]
        vec[1] += weights["borders"] / np.abs(np.power(r + 0.001, order))
    elif point[1] > sim.size[1] - max_dist:
        r = sim.size[1] - point[1]
        vec[1] -= weights["borders"] / np.abs(np.power(r + 0.001, order))

    # Goal
    if goal_set:
        r = p.distance(Point(goal[0], goal[1]))
        if r > 0.1:
            dir_vec = -np.array([goal[0] - p.x, goal[1] - p.y])
            dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec))
            field = weights["goal"] / np.abs(np.power(r + 0.001, goal_order))
            vec += field * dir_vec

    # Items
    for o in sim.contents.items:
        if not ((o.type in item_types) or ("all" in item_types)):
            continue
        p1, p2 = nearest_points(p, o.polygon)

        r = p2.distance(p1)

        if r > max_dist:
            continue

        dir_vec = -np.array([p2.x - p1.x, p2.y - p1.y])
        dir_vec = np.divide(dir_vec, np.linalg.norm(dir_vec + 0.001))

        field = weights["items"] / np.abs(np.power(r + 0.001, order))

        vec += field * dir_vec

    return cmd.Cmd(vec.tolist())


def velocity(
    point,
    sim,
    order=2,
    weights=field_weights,
    max_dist=2,
    goal_set=False,
    goal=None,
    goal_order=0,
    item_types=[],
):
    """
    Args:
            poiint: (x,y) tuple
            sim: Simulation object
            order: r^(-pow)
            weights: weight given to field from bots, obstacles, goal, etc.
            max_dist: Max distance of objects (except goal) exerting a field
            goal_set: Bool; whether a goal point has been given
            goal: (x,y) tuple
            goal_order:
            item_types: List containing types of items that generate field
    Returns:
            velocity vector as Cmd object
    """
    vec = np.array([0.0, 0.0])

    p = Point(point[0], point[1])

    # print("!!!!!!!!!!")
    # If the robot is close to the goal, set its velocity to zero and mark the goal as reached
    vec = np.array([0.0, 0.0])
    return cmd.Cmd(vec.tolist())
