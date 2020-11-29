import networkx as nx
from networkx import DiGraph
from networkx.algorithms import isomorphism
from collections import defaultdict


def get_isos(GB, GLs, edge_attr='type'):
    """returns the isomorphisms from every GL in GLs to a node induced subgraph of GB as a ordered list of nodes

    This function is used to get the needed isos. Usually called with GI or GO as GB.
    While this is called by the GraphWFCState constructor it might be useful
    to call it yourself and cache the results if some graphs are used multiple times.

    :param GB: the 'big' Graph, GI or GO
    :param GLs: the 'small' graphs GL in an order (e.g. in a list)
    :param edge_attr: the attribute used to decide whether two edges should be considered to be of the same type
    :return: the isos in G per LG
    """

    GB_isos_per_GL = list()
    for GL in GLs:
        if not nx.is_connected(GL.to_undirected()):
            print("A GL is not connected, this may take ages!")
        if __debug__:
            iso_count = 0
        order = sorted(GL.nodes())
        edgetest = isomorphism.categorical_edge_match(edge_attr, -1)
        if nx.is_directed(GB) and nx.is_directed(GL):
            matcher = isomorphism.DiGraphMatcher(GB, GL, edge_match=edgetest)
        elif (not nx.is_directed(GB)) and (not nx.is_directed(GL)):
            matcher = isomorphism.GraphMatcher(GB, GL, edge_match=edgetest)
        else:
            raise TypeError('You may not use both directed and undirected graphs.')
        iso_list = list()
        for iso_GBtoGL in matcher.subgraph_isomorphisms_iter():
            iso_GLtoGB = {GL_node: GB_node for GB_node, GL_node in iso_GBtoGL.items()}
            iso = tuple([iso_GLtoGB[GL_node] for GL_node in order])
            iso_list.append(iso)
            if __debug__:
                iso_count += 1
                print("\rIsomorphisms: " + str(iso_count), end='', flush=True)
        if __debug__:
            print("")
        GB_isos_per_GL.append(iso_list)
    return GB_isos_per_GL


def get_patterns(GI, GLs=None, GI_isos_per_GL=None, node_attr='color', edge_attr='type'):
    """extracts the patterns from GI for each GL and counts them

        This is called by the GraphWFCState constructor. If neither GI nor GLs differ for two GraphWFCStates,
        this can be used to cache the patterns. Its return value can be used as the pattern_count_per_GL parameter.

    :param GI: the input Graph to extract the patterns from
    :param GLs: the (ordered) GLs to define the 'shape' of the patterns
    :param GI_isos_per_GL: the cached isos from e.g. get_isos(GI, GL, edge_attr=edge_attr).
            Alternative for the GLs parameter
    :param node_attr: the node attribute to be used in GraphWFC
    :param edge_attr: the attribute used to decide whether two edges should be considered to be of the same type
    :return: the patterns found in GI per LG and how often they were found
    """
    assert GLs is not None or GI_isos_per_GL is not None
    if GI_isos_per_GL is None:
        GI_isos_per_GL = get_isos(GI, GLs, edge_attr=edge_attr)
    pattern_count_per_GL = [None] * len(GLs)
    for GL_id, GL in enumerate(GLs):
        counted_patterns = defaultdict(int)
        for iso in GI_isos_per_GL[GL_id]:
            counted_patterns[tuple(GI.nodes[node][node_attr] for node in iso)] += 1
        pattern_count_per_GL[GL_id] = dict(counted_patterns)
    return pattern_count_per_GL
