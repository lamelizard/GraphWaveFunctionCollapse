import networkx as nx
import graphwfc
GI = nx.Graph([(1,2),(2,3),(3,4)])
GI.add_nodes_from([(1,{'c':'b'}),(2,{'c':'b'}),(3,{'c':'r'}),(4,{'c':'y'})])
GL = nx.Graph([(1,2)])
GO = nx.random_tree(40)
S = graphwfc.GraphWFCState(GO=GO,GLs=[GL],GI=GI,node_attr='c')
while not S.run():
    S.reset()

import matplotlib.pyplot as plt
colors = list(nx.get_node_attributes(S.GO,'c').values())
nx.draw(S.GO, node_color=colors, node_size=200)
plt.show()
