import math
import random
from collections import defaultdict
from .helpers import get_isos, get_patterns


class _FinishedObserving(RuntimeError):
    pass


class _Contradiction(RuntimeError):
    def __init__(self, location=None):
        self.location = location


class GraphWFCState:
    """includes everything needed to run GraphWaveFunctionCollapse

    :ivar GO: a copy of the input GO but with 'invisible' nodes removed.
            After :func:`~graphwfc.GraphWFCState.run` returned True it will be colored.
    :ivar iteration_count: The amount of iterations that :py:meth:run did since the last :py:meth:reset
    :ivar invisible_nodes: The nodes omitted from GO since they are not targeted by any isomorphism

    """
    __slots__ = '_pattern_count_per_GL', '_GL_count', '_all_colors', '_values_per_node', '_node_attr', \
                'GO', '_GO_backup', '_GO_isos_per_GL', \
                '_isos_per_node', '_patterns_per_GL_per_iso', '_iso_entropies_per_GL', \
                'iteration_count', 'invisible_nodes'

    def __init__(self, GO, GI=None, GLs=None, pattern_count_per_GL=None, GI_isos_per_GL=None, GO_isos_per_GL=None,
                 node_attr='color', edge_attr='type'):
        """the constructor sets up the state after 0 iterations

        This will create a GraphWFCState. Since we have to find isomorphisms this can take a while if a GL in GLs is
        'big'. If available GI_isos_per_GL, GO_isos_per_GL and pattern_count_per_GL can be set
        so they do need to be computed.

        :param GO: the output graph to be colored
        :param GI: the colored graph used as the example input. Every node must be colored and
                None is not a accepted as color.
        :param GLs: the ordered (e.g. a list) graphs that describe the patterns
                (optional if pattern_count_per_GL, GI_isos_per_GL and GO_isos_per_GL are given)
        :param pattern_count_per_GL: (optional) a cached return value from helpers.get_patterns()
        :param GI_isos_per_GL: (optional) a cached return value from helpers.get_isos()
        :param GO_isos_per_GL: (optional) a cached return value from helpers.get_isos()
        :param node_attr: the name of the node attribute used as color
        :param edge_attr: the name of the edge attribute used to distinguish between edges
        :raises ValueError: if OG can't be colored (if it doesn't throw it still may be impossible)
        """
        assert GLs is not None or GO_isos_per_GL is not None
        assert pattern_count_per_GL is not None or (GI is not None and (GLs is not None or GI_isos_per_GL is not None))
        self._node_attr = node_attr

        # count patterns in GI for each GL
        if pattern_count_per_GL is None:
            pattern_count_per_GL = get_patterns(GI=GI, GLs=GLs, GI_isos_per_GL=GI_isos_per_GL,
                                                node_attr=node_attr, edge_attr=edge_attr)
        self._pattern_count_per_GL = pattern_count_per_GL
        # count the GLs
        self._GL_count = len(pattern_count_per_GL)

        # get the color a GO node can be set to
        # this might not be every color of GI since only those in an area targeted by an iso are considered
        # although this might be a way to optimize...
        self._values_per_node = dict()
        self._all_colors = set()
        for counted_patterns in self._pattern_count_per_GL:
            for pattern in counted_patterns.keys():
                self._all_colors.update(pattern)
        assert None not in self._all_colors

        # find the isos in GO
        if GO_isos_per_GL is None:
            GO_isos_per_GL = get_isos(GB=GO, GLs=GLs, edge_attr=edge_attr)
        self._GO_isos_per_GL = GO_isos_per_GL

        # copy since we won't change input graph (deepcopy?)
        # self.GO will be set in reset()
        self._GO_backup = GO.copy()

        # save per node in which isos it is
        self._isos_per_node = dict()
        for node in self._GO_backup.nodes():
            self._isos_per_node[node] = [set() for GL in GLs]
        for GL_id, isos in enumerate(self._GO_isos_per_GL):
            for iso in isos:
                for node in iso:
                    assert node in self._GO_backup.nodes()
                    self._isos_per_node[node][GL_id].add(iso)

        # are some nodes in no are of an iso (aka invisible)? -> remove them from our Graph
        # technically not needed but it's easier if we don't need to keep them in mind
        self.invisible_nodes = {node for node, isos_per_node in self._isos_per_node.items()
                                if not any(isos_per_node[GL_id] for GL_id in range(self._GL_count))}
        if self.invisible_nodes:
            self._GO_backup = self._GO_backup.subgraph(self._GO_backup.nodes() - self.invisible_nodes).copy()
            if __debug__:
                print('not all nodes are in a GL-iso area, namely: ' + str(self.invisible_nodes))

        # create self.GO and set initial colors
        self.reset()

    def reset(self):
        """resets the object to the state after the construction

        This is useful if run() runs into a contradiction (it returns false).
        Call this method and and run() can be called again.
        This is not called automatically so that information about the contradiction can be extracted
        """
        # create new GO
        self.GO = self._GO_backup.copy()

        # set possible colors per node
        for node in self.GO.nodes():
            self._values_per_node[node] = self._all_colors.copy()

        # set initially all patterns to allowed in all isos per GL and the respective iso entropies
        self._patterns_per_GL_per_iso = [{} for GL_id in range(self._GL_count)]
        self._iso_entropies_per_GL = [{} for GL_id in range(self._GL_count)]
        for GL_id in range(self._GL_count):
            for iso in self._GO_isos_per_GL[GL_id]:
                self._patterns_per_GL_per_iso[GL_id][iso] = set(self._pattern_count_per_GL[GL_id].keys())
                # TODO, if I start with all possible patterns, then this entroy is allways the same
                self._iso_entropies_per_GL[GL_id][iso] = self._iso_entropy_per_GL(GL_id, iso)

        # constraint propagation -> remove some unallowed colors per node and patterns per iso
        try:
            self._propagate(self.GO.nodes())
        except _Contradiction as contradiction:
            raise ValueError("the input GO contains unallowed patterns, or isos have no allowed patterns , e.g. at: " +
                             str(contradiction.location))

        # reset iteration count
        self.iteration_count = 0

    def _fitting_patterns_per_GL(self, GL_id, iso, removed_colors_per_node):
        iso_patterns = self._patterns_per_GL_per_iso[GL_id][iso].copy()
        for node in set(iso).intersection(removed_colors_per_node.keys()):
            iso_patterns -= {pattern for pattern in iso_patterns if
                                    pattern[iso.index(node)] in removed_colors_per_node[node]}
        return iso_patterns

    def _fitting_values(self, node):
        assert self.GO.has_node(node)
        allowedvalues_per_iso = [self._values_per_node[node]]  # it will always be a subset of this
        for GL_id in range(self._GL_count):
            for iso in self._isos_per_node[node][GL_id]:
                # should safre index per node and iso, seems to be expensive?
                value_id = iso.index(node)
                allowedvalues_per_iso.append(
                    {pattern[value_id] for pattern in self._patterns_per_GL_per_iso[GL_id][iso]})
        return set.intersection(*allowedvalues_per_iso)

    # multithread this?
    def _propagate_nodes(self, nodes_to_propagate):
        isos_to_propagate_per_GL = [set() for GL_id in range(self._GL_count)]
        removed_values_per_node = defaultdict(set)
        while nodes_to_propagate:
            node = nodes_to_propagate.pop()
            old_colors = self._values_per_node[node]
            new_colors = self._fitting_values(node)
            if len(new_colors) < len(old_colors):
                self._values_per_node[node] = new_colors
                removed_values_per_node[node].update(old_colors - new_colors)
                for GL_id in range(self._GL_count):
                    for iso in self._isos_per_node[node][GL_id]:
                        isos_to_propagate_per_GL[GL_id].add(iso)
            if len(new_colors) == 0:
                raise _Contradiction(node)  # we can't fill GO with given patterns in the current state
            if len(new_colors) == 1 and \
                    (self._node_attr not in self.GO.nodes[node] or self.GO.nodes[node][self._node_attr] is None):
                # we have the final color for this node and set it in GO
                self.GO.nodes[node][self._node_attr] = next(iter(new_colors))  # extract the only element
        return isos_to_propagate_per_GL, removed_values_per_node

    # multithread this?
    def _propagate_isos(self, isos_to_propagate_per_GL, removed_values_per_node):
        nodes_to_propagate = set()
        for GL_id in range(self._GL_count):
            for iso in isos_to_propagate_per_GL[GL_id]:
                old_iso_patterns = self._patterns_per_GL_per_iso[GL_id][iso]
                new_iso_patterns = self._fitting_patterns_per_GL(GL_id, iso, removed_values_per_node)
                # this contradiction would be found in _propagate nodes, but it's nice to know there it comes from
                if len(new_iso_patterns) == 0:
                    raise _Contradiction(iso)
                if len(new_iso_patterns) < len(old_iso_patterns):
                    self._patterns_per_GL_per_iso[GL_id][iso] = new_iso_patterns
                    self._iso_entropies_per_GL[GL_id][iso] = self._iso_entropy_per_GL(GL_id, iso)
                    nodes_to_propagate.update(iso)
        return nodes_to_propagate

    def _propagate(self, startnodes):
        """constraint propagation"""
        assert startnodes is not None
        nodes_to_propagate = set(startnodes)
        while nodes_to_propagate:
            isos_to_propagate_per_GL, removed_values_per_node = self._propagate_nodes(nodes_to_propagate)
            nodes_to_propagate = self._propagate_isos(isos_to_propagate_per_GL, removed_values_per_node)

    def _iso_observe(self):
        """"chooses iso with low entropy > 0 and applies a pattern"""
        # choose an isomorphism
        min_GL_and_isos = []
        min_entropy = float('inf')
        for GL_id in range(self._GL_count):
            for iso, entropy in self._iso_entropies_per_GL[GL_id].items():
                if entropy > 0:
                    if entropy < min_entropy:
                        min_GL_and_isos = []
                        min_entropy = entropy
                    if entropy == min_entropy:
                        min_GL_and_isos.append((GL_id, iso))
        if not min_GL_and_isos:
            # we finished observing GO since all entropies are 0
            raise _FinishedObserving
        observe_GL, observe_iso = random.choice(min_GL_and_isos)
        # choose a pattern
        possible_patterns = self._patterns_per_GL_per_iso[observe_GL][observe_iso]
        weighted_patterns = []
        for pattern in possible_patterns:
            weighted_patterns.extend([pattern] * self._pattern_count_per_GL[observe_GL][pattern])
        chosen_pattern = random.choice(weighted_patterns)
        # apply pattern
        self._patterns_per_GL_per_iso[observe_GL][observe_iso] = {chosen_pattern}
        self._iso_entropies_per_GL[observe_GL][observe_iso] = 0  # 0 == self.iso_entropy(observe_iso)
        return observe_iso

    def run(self, iter: int = -1):
        """runs GraphWaveFunctionCollapse on the graphs

        After initialising the GraphWFCState, we need to run the GraphWaveFunctionCollapse algorithm using this method.
        It will iterate until a contradiction is observed, colors were determined for all nodes
        or after the given amount of maximal iterations.

        :param iter: the maximum amount of GraphWaveFunctionCollapse-iterations. No limiting if negative
        :return: True if GO has been completely colored, False if a contradiction occurred and nothing if the maximum amount
                of iterations was used up.
        """
        try:
            while iter != 0:
                self.iteration_count += 1
                iso = self._iso_observe()
                self._propagate(iso)
                iter -= 1
        except _FinishedObserving:
            return True
        except _Contradiction:
            return False

    def _iso_entropy_per_GL(self, GL_id, iso):
        """returns isos Shannon entropy"""
        fitting_patterns = self._patterns_per_GL_per_iso[GL_id][iso]
        if not fitting_patterns:
            return 0
        fitting_patterns_count_total = sum(self._pattern_count_per_GL[GL_id][pattern] for pattern in fitting_patterns)
        pattern_probabilities = {self._pattern_count_per_GL[GL_id][pattern] / fitting_patterns_count_total
                                 for pattern in fitting_patterns}
        entropy = -sum(probability * math.log(probability) for probability in pattern_probabilities)
        if len(fitting_patterns) == 1:
            assert entropy == 0
        return entropy
