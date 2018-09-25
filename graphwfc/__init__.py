"""A python implementation of GraphWaveFunctionCollapse

This algorithm is based on WaveFunctionCollapse.
It colors an output graph GO such that all patterns used
are from the example input graph GI. A pattern is a colored subgraph
which shape is determined by a small graph GL.
Some usage examples can be found on the `GitHub page <https://github.com/lamelizard/GraphWaveFunctionCollapse>`_.
We use 'iso' in the API as a short form of 'subgraph isomorphism'.

Example code:

>>> import networkx as nx
>>> import graphwfc
>>> GI = nx.Graph([(1,2),(2,3),(3,4)]).to_directed()
>>> GI.add_nodes_from([(1,{'c':1}),(2,{'c':1}),(3,{'c':2}),(4,{'c':3})])
>>> GL = nx.Graph([(1,2)]).to_directed()
>>> GO = nx.random_tree(1000).to_directed()
>>> S = graphwfc.GraphWFCState(GO=GO,GLs=[GL],GI=GI,node_attr='c')
>>> while not S.run():
...     S.reset()
...
>>> nx.write_graphml(S.GO, "out.graphml")

GI is the graph 1 -- 1 -- 2 -- 3 and GL is a -- b where a and b have no color.  
We extract the patterns 1 -- 1, 1 -- 2 and 2 -- 3.  
GO will only contain the extracted patterns. As such the out.graphml will contain a tree with 1000 nodes colored in a way
such that no node with color 2 has a neighbour colored 2 and no node colored 3 has a neighbour with color 3 or 1. The color will be stored in the node attribute 'c'.

"""
from .GraphWFCState import GraphWFCState
