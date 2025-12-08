from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import networkx as nx
import osmnx as ox

PATH_TO_GRAPH = "backend/ottawa_drive.graphml"


@dataclass
class OttawaGraphNetwork:
    G: nx.classes.multidigraph.MultiDiGraph = field(init=False)

    def __post_init__(self):
        self.G = ox.load_graphml(PATH_TO_GRAPH)

    def get_street_edges_to_avoid(
        input_street_names: List[str],
    ) -> Tuple[list[str], List[List[Tuple[int, int, int]]]]:
        """Given a list of street names in sorted order of dispreference, return a tuple with two things 
        1) The set of edge names 
        the set of edges in Ottawa's road network corresponding to these streets, in the same order.
        Every edge in the road network is shown using a tuple of three integers.
        Furthermore, every street is associated with 1 or more edge."""
        


def shortest_path_edges(
    H: nx.MultiDiGraph, s: int, t: int, weight: str = "length"
) -> List[Tuple[int, int, int]]:
    """Compute shortest path from s to t in H and return it as a list of (u, v, key) edges."""
    path_nodes = nx.shortest_path(H, s, t, weight=weight)
    edges: List[Tuple[int, int, int]] = []

    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        # There may be multiple parallel edges; pick one (e.g., first) between u and v that exists in H.
        edge_data = H.get_edge_data(u, v)
        if edge_data is None:
            raise RuntimeError(
                f"No edge in H between {u} and {v} on the computed path."
            )
        key = next(iter(edge_data.keys()))
        edges.append((u, v, key))

    return edges


def build_subgraph(
    G: nx.MultiDiGraph,
    allowed_edge_set: set[Tuple[int, int, int]],
) -> nx.MultiDiGraph:
    """Build a MultiDiGraph containing only the allowed edges (and all original node attributes).
    In other words, given a graph G and an edge set E this method retuns the induced graph G[E]
    """
    H = nx.MultiDiGraph()
    H.add_nodes_from(G.nodes(data=True))
    for u, v, key in allowed_edge_set:
        data = G[u][v][key]
        H.add_edge(u, v, key=key, **data)
    return H


class DisjointSetUnion:
    """Disjoint Set Union (Union-Find) structure with path compression and union by rank."""

    def __init__(self, elements: List[int]):
        self.parent: Dict[int, int] = {x: x for x in elements}
        self.rank: Dict[int, int] = {x: 0 for x in elements}

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        x_root = self.find(x)
        y_root = self.find(y)
        if x_root == y_root:
            return False
        if self.rank[x_root] < self.rank[y_root]:
            self.parent[x_root] = y_root
        elif self.rank[x_root] > self.rank[y_root]:
            self.parent[y_root] = x_root
        else:
            self.parent[y_root] = x_root
            self.rank[x_root] += 1
        return True
