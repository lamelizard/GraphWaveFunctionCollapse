"""takes .graphml files and runs GraphWaveFunctionCollapse

This allows to run GraphWaveFunctionCollapse with the command 'python -m graphwfc'.
I takes .graphml files as input and generates one as output.
"""
import networkx as nx
from .GraphWFCState import GraphWFCState
import argparse

if __name__ == '__main__':
    # parsing arguments
    parser = argparse.ArgumentParser(description='GraphWaveFuntionCollapse on .graphml files')
    parser.add_argument('-GI', dest='GI', default='GI.graphml', help='GI GraphML, the example')
    parser.add_argument('-GLs', dest='GLs', default=['GL.graphml'], nargs='+', help='GL GraphML, describing the areas')
    parser.add_argument('-GO', dest='GO', default='GO.graphml',
                        help='OG GraphML, describing the output graph (this is an INPUT file)')
    parser.add_argument('-n', type=int, dest='n', default=10, help='how often we try')
    parser.add_argument('-o', '--output', dest='outputPath', default='out.graphml',
                        help='the output graph GO with the colors set')
    parser.add_argument('-v', '--node_attr', dest='node_attr', default='value',
                        help='the node attribute used by GraphWaveFunctionCollapse')
    parser.add_argument('-e', '--edge_attr', dest='edge_attr', default='type',
                        help='the edge attribute used by GraphWaveFunctionCollapse')
    args = parser.parse_args()
    # initialization
    GI = nx.read_graphml(args.GI)
    GLs = [nx.read_graphml(GL) for GL in args.GLs]
    GO = nx.read_graphml(args.GO)
    state = GraphWFCState(GO=GO, GI=GI, GLs=GLs, node_attr=args.node_attr, edge_attr=args.edge_attr)
    # run GraphWaveFunctionCollapse
    for _ in range(args.n):
        if state.run():
            print('SUCCESS')
            nx.write_graphml(state.GO, args.outputPath)
            break
        else:
            print('FAILURE')
            state.reset()
