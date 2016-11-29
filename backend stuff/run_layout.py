import os
import json
import math
from tulip import tlp

'''
input: (graphID : Int), (algorithm : String)
output: Dict (NodeName -> (X, Y))

algorithm options:
	"FM^3 (OGDF)"
	"Fast Multipole Embedder (OGDF)"
	"Fast Multipole Multilevel Embedder (OGDF)"
	"Pivot MDS (OGDF)"
	"GRIP" (kind of slow for larger data sets)
	- (weird result) "Frutcherman Reingold (OGDF)"
	- (weird result) "GEM Frick (OGDF)"
	- (slow) "GEM (Frick)"
	- (slow) "Bertault (OGDF)"
	- (slow) "Kamada Kawai (OGDF)"
	- (slow) "LinLog"
	- (slow) "Upward Planarization (OGDF)"
	- (slow) "Visibility (OGDF)"
	- (InsufficientMemoryException) "Stress Majorization (OGDF)"
	- (Python stops working?) "Sugiyama (OGDF)"
'''
def runLayout(graphID, algorithm, **extraParams):
	with open('test_data/%s_links.json' % graphID) as f:
		linksJson = json.loads(f.read())

	g = tlp.newGraph()
	nameToNode = { node : g.addNode() for node in linksJson.keys() }

	for source, targets in linksJson.items():
		for target in targets:
			g.addEdge(nameToNode[source], nameToNode[target])

	layout = g.getLayoutProperty('viewLayout')
	params = tlp.getDefaultPluginParameters(algorithm, g)
	params.update(extraParams)
	
	successful, errorMsg = g.applyLayoutAlgorithm(algorithm, layout, params)

	if not successful:
		raise Exception(errorMsg)

	nameToCoords = {}
	for nodeName in linksJson.keys():
		x, y, z = layout[nameToNode[nodeName]]
		nameToCoords[nodeName] = x, y

	normalizeCoords(nameToCoords)
	reduceGaps(nameToCoords)
	normalizeCoords(nameToCoords)
	makeCircular(nameToCoords)

	return nameToCoords


def normalizeCoords(nodeDict):
	maxX, maxY = 0.0, 0.0

	for x, y in nodeDict.values():
		maxX = max(x, maxX)
		maxY = max(y, maxY)

	for node, (x, y) in nodeDict.items():
		nodeDict[node] = x / maxX, y / maxY


def reduceGaps(nodeDict):
	maxGap = 0.02

	byXCoord = sorted(list(nodeDict.items()), key=lambda node: node[1][0])
	totalReduction = 0
	for (n1, (x1, y1)), (_, (x2, _)) in zip(byXCoord, byXCoord[1:]):
		nodeDict[n1] = x1 - totalReduction, y1
		totalReduction += max(0, x2 - x1 - maxGap)
	n, (x, y) = byXCoord[-1]
	nodeDict[n] = x - totalReduction, y

	byYCoord = sorted(list(nodeDict.items()), key=lambda node: node[1][1])
	totalReduction = 0
	for (n1, (x1, y1)), (_, (_, y2)) in zip(byYCoord, byYCoord[1:]):
		nodeDict[n1] = x1, y1 - totalReduction
		totalReduction += max(0, y2 - y1 - maxGap)
	n, (x, y) = byYCoord[-1]
	nodeDict[n] = x, y - totalReduction


def makeCircular(nodeDict):
	for node, (x, y) in nodeDict.items():
		x -= 0.5
		y -= 0.5
		r = max(abs(x), abs(y))
		x = r * math.cos(math.atan2(y, x))
		y = r * math.sin(math.atan2(y, x))
		nodeDict[node] = x, y


def writeLayout(coords, graphID):
	with open('test_data/%s_links.json' % graphID) as f:
		linksJson = json.loads(f.read())

	with open('test_data/%s_nodes_viz.json' % graphID) as f:
		nodesJson = json.loads(f.read())

	output = {}
	for node, (x, y) in coords.items():
		output[node] = {
			'x' : x,
			'y' : y,
			'cluster' : nodesJson[node]['cluster'],
			'default_size' : nodesJson[node]['default_size'],
		}

	with open('test_data/%s_nodes_viz.json' % graphID, 'w') as f:
		f.write(json.dumps(output))


if __name__ == '__main__':
	graphID = int(sys.argv[1])
	algorithm = sys.argv[2]
	print("Running layout algorithm...")
	coords = runLayout(graphID, algorithm)
	print("Saving coordinates...")
	writeLayout(coords, graphID)
	os.system('jython generate_image.py %s' % graphID)
