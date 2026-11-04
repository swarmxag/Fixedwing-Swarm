import sys, yaml, os
import swarm_tasks.envs.world

import shapely
from shapely.geometry import Polygon
"""
Each env is stored as a yaml file listing size & obstacles
Loader will load the shapely polygon array in an World object
"""

def fence_polygon(world_dict):
	"""The drawn fence outline (`fence:` in the world yaml, same frame as the
	obstacles) as a Polygon, or None for a file written before it existed."""
	ring = (world_dict or {}).get('fence')
	try:
		if ring and len(ring) >= 3:
			poly = Polygon(ring)
			return poly if poly.is_valid else poly.buffer(0)
	except Exception as e:
		print("Invalid fence outline in world file:", e)
	return None

#Relative paths (May cause complications while running from different folders)
envs_path = os.path.dirname(os.path.abspath(__file__))
worlds_path = os.path.join(envs_path, 'worlds')

class World:
	"""
	An instance of this is loaded in th simulation
	A world is defined using dimensions and a list of obstcles
	"""
	def __init__(self, size=(20,20), obstacles=[], filename = None):

		self.fence = None  # drawn fence outline (inside area), if the file has one
		if filename !=None:
			file = os.path.join(worlds_path, filename)

			self.size, self.obstacles = self.load_yaml(file)
		else:
			self.size = size
			self.obstacles = obstacles

	def load_yaml(self, filename):
		f = open(filename)
		dict_=yaml.safe_load(f)
		obstacles = []
		size = (dict_['size']['x'], dict_['size']['y'])
		
		if dict_['obstacles']!=None:
			obstacle_list = dict_['obstacles']
			for o in obstacle_list:
				obstacles.append(Polygon(o))

		self.fence = fence_polygon(dict_)

		name = dict_['name']

		print("Loaded world: "+name)
		return size, obstacles