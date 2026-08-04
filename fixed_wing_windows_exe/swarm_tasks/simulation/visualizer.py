from swarm_tasks.simulation.simulation import Simulation
import swarm_tasks.envs as envs

import matplotlib.patches as patches
from matplotlib import pyplot as plt
from matplotlib import animation
import numpy as np
from shapely.geometry import Point
class Gui:
	def __init__(self, sim):
		self.sim = sim
		self.size = sim.size
		self.env_name = sim.env_name
		#self.ax = plt.axes()
		#self.fig = plt.gcf()
		self.fig, self.ax = plt.subplots(figsize=(10,10))
		self.ax.set_ylim([0, sim.size[1]])
		self.ax.set_xlim([0, sim.size[0]])

		#self.state_colors = ['blue','green','red','orange', 'purple']
		self.state_colors = ['b','g','r','c', 'm','y','purple','orange','k','brown','lime','pink','teal','gold','gray','violet']
		self.grid_scatter = None

		#Contents list (used in remove_artists())
		self.content_fills = []
		self.limits = ([0,0,self.size[0], self.size[0]], [0,self.size[1], self.size[1],0])
		self.area_covered=0
		self.search_time=0
		self.coverage_text = None
		self.coverage_text1 = None
		self.uav_trajectories=[]
		self.uav_positions = {'uav_1': [], 'uav_2': [], 'uav_3': [], 'uav_4': [], 'uav_5': [], 'uav_6':[], 'uav_7':[], 'uav_8':[]}
		self.trail_lines = []
		self.trail_x = []
		self.trail_y = []
		self.goal_artists = []
		self.gps_artists = []
		self.circle_artists = []
		self.planned_path_artists = []

	def show_bots(self):

		# bot.size is the real collision radius used by the simulation logic
		# (often as small as 0.4) -- on a world sized in real ground units
		# (e.g. a fence loaded from swarm_env can be thousands of units wide)
		# a circle that small is sub-pixel and invisible. vis_r is a
		# draw-only radius scaled to the current world so bots stay visible
		# regardless of environment size; it never feeds back into sim state.
		vis_r = max(self.size) * 0.0009

		if not self.trail_lines:
			for i in range(len(self.sim.swarm)):
				color = self.state_colors[i % len(self.state_colors)]
				line, = self.ax.plot([], [], '-', color=color, linewidth=1, alpha=0.6)
				self.trail_lines.append(line)
				self.trail_x.append([])
				self.trail_y.append([])

		#show bots
		for i,bot in enumerate(self.sim.swarm):
			#self.show_neighbourhood(bot,3)

			x,y,theta = bot.get_pose()
			bot_color = self.state_colors[i % len(self.state_colors)]

			self.trail_x[i].append(x)
			self.trail_y[i].append(y)
			self.trail_lines[i].set_data(self.trail_x[i], self.trail_y[i])

			circle = plt.Circle((x,y), vis_r, color=bot_color, fill=True)
			self.fig.gca().add_artist(circle)

			l=vis_r*0.4
			self.ax.arrow(x,y, \
				(vis_r-l)*np.cos(theta), (vis_r-l)*np.sin(theta), \
				head_width=l, head_length=l, \
				fc='k', ec='k', zorder=50)

	def show_goals(self, goals):
		"""goals: list of (x,y) target points, one per bot. Pass the same
		list across frames (only overwriting entries as new goals are
		computed) rather than rebuilding it each frame, so a bot with no
		goal yet (None) simply has no marker instead of flickering."""
		for artist in self.goal_artists:
			artist.remove()
		self.goal_artists = []
		for i, goal in enumerate(goals):
			if goal is None:
				continue
			gx, gy = goal
			color = self.state_colors[i % len(self.state_colors)]
			marker, = self.ax.plot(gx, gy, marker='x', markersize=5, markeredgewidth=2, color=color)
			self.goal_artists.append(marker)

	def show_gps_positions(self, points):
		"""Plot each bot's real (live GPS-derived) position, distinct from
		the simulated bot circle drawn by show_bots(), so simulated vs real
		position can be compared visually during a search operation.

		points: list of (x, y) in the same local sim frame as s.swarm[i].x/y
		(already converted from lat/lon by the caller), one entry per bot,
		or None where no live GPS fix is available yet. Current position
		only -- no trail, redrawn fresh every call.
		"""
		for artist in self.gps_artists:
			artist.remove()
		self.gps_artists = []
		for i, point in enumerate(points):
			if point is None:
				continue
			gx, gy = point
			color = self.state_colors[i % len(self.state_colors)]
			marker, = self.ax.plot(
				gx, gy, marker='+', markersize=10, markeredgewidth=2,
				color=color, zorder=60,
			)
			self.gps_artists.append(marker)

	def show_circles(self, circles_by_bot):
		"""Draw each bot's guided-circle loiter ring, so you can visually
		confirm where _start_guided_circle_task actually centered it (one
		ring per bot -- they will coincide if every bot's final goal was the
		same point, and differ if bots had different final goals).

		circles_by_bot: list aligned with s.swarm, each entry either None
		(bot has no active circle) or that bot's list of circle_points
		[(x, y), ...] in the same local sim frame as s.swarm[i].x/y.
		"""
		for artist in self.circle_artists:
			artist.remove()
		self.circle_artists = []
		for i, points in enumerate(circles_by_bot):
			if not points:
				continue
			color = self.state_colors[i % len(self.state_colors)]
			ring = list(points) + [points[0]]  # close the loop
			xs, ys = zip(*ring)
			line, = self.ax.plot(xs, ys, linestyle=':', linewidth=1.5, color=color, alpha=0.8)
			self.circle_artists.append(line)
			dots, = self.ax.plot(
				[p[0] for p in points], [p[1] for p in points],
				linestyle='', marker='o', markersize=4, color=color, alpha=0.8,
			)
			self.circle_artists.append(dots)

	def show_planned_path(self, paths_by_bot):
		"""Draw each bot's full planned waypoint list (the whole search/
		goal/split path, not just the single current target show_goals()
		draws) as a static reference line, so you can see the entire
		intended coverage area/route and judge where a bot is relative to
		its whole plan -- not just its very next point. Useful for spotting
		a bot stalled/circling partway through its route instead of
		continuing along it.

		paths_by_bot: list aligned with s.swarm, each entry either None (no
		plan for this bot) or a list of (x, y) points in the same local sim
		frame as s.swarm[i].x/y, in visit order.
		"""
		for artist in self.planned_path_artists:
			artist.remove()
		self.planned_path_artists = []
		for i, points in enumerate(paths_by_bot):
			if not points:
				continue
			color = self.state_colors[i % len(self.state_colors)]
			xs = [p[0] for p in points]
			ys = [p[1] for p in points]
			line, = self.ax.plot(xs, ys, linestyle='--', linewidth=1, color=color, alpha=0.35, zorder=10)
			self.planned_path_artists.append(line)

	def show_env(self):
	    for obs in self.sim.env.obstacles:
	    	x, y = obs.exterior.xy
	    	self.ax.fill(x, y, fc='gray', alpha=0.9)
	    	if(self.env_name=="rectangles1"):
	    		x_coords = [int(i) for i in x]
		    	y_coords = [int(i) for i in y]

			# Set the grid cells inside the obstacle to True
		    	for i in range(max(0, min(x_coords)), min(self.sim.size[0], max(x_coords))):
		    		for j in range(max(0, min(y_coords)), min(self.sim.size[1], max(y_coords))):
		    			if 0 <= i < self.sim.size[1] and 0 <= j < self.sim.size[0]:
		    				if obs.contains(Point(i, j)):  # Check if the point is inside the polygon
		    					self.sim.grid[j, i] = True

	'''
	def show_env(self):
		for obs in self.sim.env.obstacles:
			x,y = obs.exterior.xy
			self.ax.fill(x,y, fc='gray', alpha=0.9)
			
			x_coords = [int(i) for i in x]
			y_coords = [int(i) for i in y]

			# Set the grid cells inside the obstacle to True
			for i in range(max(0, min(x_coords)), min(self.sim.size[0], max(x_coords) )):
		    		for j in range(max(0, min(y_coords)), min(self.sim.size[1], max(y_coords) )):
		    			if obs.contains(Point(i, j)):  # Check if the point is inside the polygon
		    				self.sim.grid[j, i] = True
			    				
			
			x_coords = [int(i) for i in x]
			y_coords = [int(i) for i in y]

			# Set the grid cells inside the obstacle to True
			for i in range(self.sim.size[0]):
			    for j in range(self.sim.size[1]):
			    	if (
				    min(x_coords) >= i >= max(x_coords)
				    and min(y_coords) >= j >= max(y_coords)
				    and obs.contains(Point(i, j))):
				    	self.sim.grid[j, i] = True
	'''

	def show_contents(self):
		for item in self.sim.contents.items:
			x,y = item.polygon.exterior.xy
			if item.subtype == 'contamination':
				self.ax.fill(x,y, fc='red', alpha=0.5)
				continue
			elif item.subtype == 'nest':
				self.ax.fill(x,y, fc='purple', alpha =0.3)
				continue
			self.ax.fill(x,y, fc='orange', alpha=0.9)
			#self.content_fills.append((x,y))
	

	def update(self):
		"""

		"""
		self.remove_artists()
		#self.show_bots()
		if self.sim.has_item_moved:
			#for ext in self.content_fills:
				#self.ax.fill(*ext, fc='w')
			#self.content_fills=[]
			#self.ax.fill(*self.limits, 'w')
			self.show_contents()
			self.show_env()
			self.sim.has_item_moved = False
		self.show_bots()
		if(self.env_name=="rectangles1"):
			self.show_coverage(self.area_covered,self.search_time)
		plt.pause(0.0005)

	def remove_artists(self):
		"""
		Previous figures need to be removed before updating positions on GUI
		"""
		for obj in self.ax.findobj(plt.Circle):
			obj.remove()

		for obj in self.ax.findobj(patches.FancyArrow):
			obj.remove()
		
		if self.sim.has_item_moved:
			for obj in self.ax.findobj(patches.Polygon):
				obj.remove()


	def show_neighbourhood(self, bot, r=None):
		#Shows the neighbourhood of a robot
		x,y = bot.get_position()
		if r == None:
			r = bot.neighbourhood_radius
		circle2 = plt.Circle((x,y), r, color='red', fill=True, alpha=0.1)
		circle1 = plt.Circle((x,y), r/2+bot.size, color='red', fill=True, alpha=0.1)
		self.fig.gca().add_artist(circle1)
		self.fig.gca().add_artist(circle2)


	def show_grid(self):
		"""
		Args:
			grid: A 2D array of values from 0-1 
		
		TODO:
		Plotting the grid as an image takes high computation
		Plot in another format
		"""
		if self.grid_scatter != None:
			self.grid_scatter.remove()

		x_size, y_size = self.sim.size
		x_labels = [i +0.5 for i in range(x_size)]*y_size
		y_labels = [int(i/x_size)+0.5 for i in range(y_size*x_size)]
		
		grid_1d = self.sim.grid.ravel()
		#grid_1d[20:40] = True	#debug

		col = ['green' if i else 'yellow' for i in grid_1d]


		if len(col) != len(x_labels) or len(x_labels) != len(y_labels):
			print("ERROR: Grid shape mismatch")
			return False

		self.grid_scatter = self.ax.scatter(x_labels, y_labels, c=col)
		#plt.draw()

	def show_coverage(self, area_covered,search_time):
		self.area_covered=area_covered
		self.search_time=search_time
		#self.elapsed_time_value = elapsed_time
		timer_text = f"Time: {int(self.search_time // 60):02d}:{int(self.search_time % 60):02d}"
		if self.coverage_text is not None:
			self.coverage_text.remove()			
			#if hasattr(self, 'elapsed_time_text'):
			 #   self.elapsed_time.remove()
		if self.coverage_text1 is not None:
			self.coverage_text1.remove()	
		# Adjust the coordinates as needed for the position of the text box
		text_box_props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
		label_text = "Area Covered ="
		self.coverage_text = self.ax.text(1, 1.05, f"{label_text} {area_covered}", transform=self.ax.transAxes,
		                  fontsize=10, verticalalignment='top', horizontalalignment='right', bbox=text_box_props)
            
            
		text_box_props1 = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
		label_text1 = "Time ="
		self.coverage_text1 = self.ax.text(1, 1.09, f"{timer_text} ", transform=self.ax.transAxes,
		                  fontsize=10, verticalalignment='top', horizontalalignment='right', bbox=text_box_props1)
        
		return area_covered
	def run(self):
		plt.show(block=False)
		
	def close(self):
		plt.close()
		
