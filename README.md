# GraphWaveFunctionCollapse (GWFC)

A python 3.x package to color a graph based on patterns extracted from an colored example graph, it's based on [WaveFunctionCollapse](https://github.com/mxgmn/WaveFunctionCollapse).
I wrote a [thesis](/thesis.pdf) on the algorithm (in German).

Below are some examples:
* On the left side the example input can be seen which was converted into the input graph *GI*.
* In the middle we see the graph *GL* which describes the structur of the patterns to be extracted.
* On the right side is the ouput. It was generated from the ouput graph *GO* which was colored by GWFC using the patterns extracted from *GI*. 

![overview.png](/examples/overview.png)

In the /examples directoy all graphs (*GI*,*GL* and *GO*) can be found as GraphML files. You may also want to look at the example in the **Usage** section.  
To display GraphML files you might want to check out [Gephi](https://gephi.org), [Tulip](http://tulip.labri.fr/TulipDrupal) and/or [Cytoscape](http://www.cytoscape.org/).  
The second example from the top (starcave) uses graphs to simulate [WFC](https://github.com/mxgmn/WaveFunctionCollapse) with N=3.  

## Algorithm
The general idea is similar to [WFC](https://github.com/mxgmn/WaveFunctionCollapse):
1. We extract patterns from the colored example input *GI*. We describe the structur of the patterns by providing the 'local similarity graph' *GL*; All patterns are subgraphs of *GI* isomorph to *GL*.
2. Initially *every* node in *GO* is colored in *all* colors.
3. We remove all the nodes from *GO* that are not in an subgraph isomorphism (with *GL*). We won't color them (see the top-left and the bottom-rigth hexagon of the first example from the top).
4. Patterns can be applied to all subgraphs of *GO* isomorph to *GL*:
    1. We select an isomorphism in *GO* that has a low Shannon entropy bigger than 0; 
        * We can select from all patterns that are applicable regarding the current coloring of the nodes. 
        * The probability of an applicable pattern is the relative amount of occurrences of that pattern in *GI*. 
        * If all nodes are colored in exactly one color we stop and output the colored *GO*.
    2. We apply a pattern to the selected isomorphism by having the respective nodes colored in *only* the respective color given by the pattern.
    3. We use constraint propagation to remove colors from nodes in *GO* that are not possible anymore given the current coloring. If we removed all colors from a node, it's a contradiction and we stop without output.

## Usage
Install with `pip install graphwfc` or after downloading this repo `python setup.py install`.

After installing you can try out the examples by going into the respective directory (e.g. /examples/beach) and running `python -m graphwfc -v value`. This will generate an out.graphml file.
All examples use the node attribute 'value' as color which is given by `-v value`.
With `-e edge_attr` it will check for equality of the edge attribute 'edge_attr' while searching for subgraph isomorphisms. The default is 'type'.

While this package was meant to be used standalone with `python -m graphwfc` an API is available which can be found in the autogenerated [documenation](https://lamelizard.github.io/GraphWaveFunctionCollapse/graphwfc.html).

*Remarks*:
* Instead of *GL* we use *GLs*, we allow to use more than one graph to extract and apply patterns.
* We use GraphML files for the graphs.
* The API accepts [networkx](https://networkx.github.io/) (Di)Graphs. Don't mix Graphs and DiGraphs.
* Since this package uses the [networkx](https://networkx.github.io/) implemetation of VF2 to find subgraph isomorphisms, only those of node induced subgraphs are used.
* Undirected Graphs are nearly untested. Since edges are only used to get subgraph isomorphisms this _should_ be fine.

Example code
```python
import networkx as nx
import graphwfc
GI = nx.Graph([(1,2),(2,3),(3,4)])
GI.add_nodes_from([(1,{'c':1}),(2,{'c':1}),(3,{'c':2}),(4,{'c':3})])
GL = nx.Graph([(1,2)])
GO = nx.random_tree(1000)
S = graphwfc.GraphWFCState(GO=GO,GLs=[GL],GI=GI,node_attr='c')
while not S.run():  # might never end -> in real code you should stop after some tries
    S.reset()
nx.write_graphml(S.GO, "out.graphml")
```
*GI* is the graph `1 -- 1 -- 2 -- 3` and *GL* is `a -- b` where *a* and *b* have no color.  
We extract the patterns `1 -- 1`, `1 -- 2` and `2 -- 3`.  
*GO* will only contain the extracted patterns. As such the out.graphml will contain a tree with 1000 nodes colored in a way
such that no node with color *2* has a neighbour colored *2* and no node colored *3* has a neighbour with color *3* or *1*. The color will be stored in the node attribute 'c'.

**Fun Fact**: This example is an [arc consistency](https://en.wikipedia.org/wiki/Local_consistency#Arc_consistency) problem. In this case GraphWaveFunctionCollapse's constraint propagation will behave somewhat similar to the [AC-3](https://en.wikipedia.org/wiki/AC-3_algorithm) algorithm.
