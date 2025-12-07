from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Union
import networkx

from backend.utils import DisjointSetUnion, _build_subgraph, _shortest_path_edges


@dataclass
class BaseRoutingAlgorithm(ABC):
    """This is the abstract routing algorithm class. Any routing algorithm must be defined as a child of this class."""

    ottawa_road_network: networkx.classes.multidigraph.MultiDiGraph
    source_vertex: int
    """An int representing the start vertex in the corresponding road network of Ottawa"""
    destination_vertex: Union[str, None]
    """An int representing the destination vertex in the corresponding road network of Ottawa"""
    edges_to_avoid: List[List[Tuple[int, int, int]]]
    """A list of edges to avoid in decreasing order of dispreference. Every edge in the road network is shown using a tuple of three integers.
    Furthermore, every street is associated with 1 or more edge."""
    street_names_to_avoid: List[str]
    """"The name of the streets to avoid, in case they need to be referenced directly in the logs by the routing algorithm(s)"""

    @abstractmethod
    def find_route(self) -> Tuple[List[Tuple[int, int, int]], str]:
        """The routing algorithm must return a list of edges to be included in the shortest path,
        which is of type List[Tuple[int, int, int]]. Moreover, it needs to return a log string
        of type str briefly explaining the result of the algorithm, i.e., if a street could not be
        avoided whatsoever.
        """
        raise NotImplementedError


@dataclass
class RoutingWithContinuousDeletions(BaseRoutingAlgorithm):
    """
    Algorithm:
    1) Treat edges_to_avoid as dispreferred streets.
    2) Start with all non-dispreferred edges present (neutral network).
    3) If s-t already connected: compute shortest path using only neutral edges.
    4) Otherwise, add dispreferred streets back from least- to most-dispreferred until
    s and t become connected.
    5) Compute shortest path on the graph restricted to:
    - all neutral edges
    - plus only those dispreferred streets that were actually needed.
    6) Return that path (as a list of edges) and a log describing which streets
    were needed vs successfully avoided.
    """

    def find_route(self) -> Tuple[List[Tuple[int, int, int]], str]:
        if self.destination_vertex is None:
            raise ValueError("Destination vertex must be provided")

        G = self.ottawa_road_network
        s = self.source_vertex
        t = self.destination_vertex

        nodes = list(G.nodes)
        dsu = DisjointSetUnion(nodes)

        # Build set of all dispreferred edges (those in the avoid list)
        avoid_edge_set = set()  # type: set[Tuple[int, int, int]]
        for street_edges in self.edges_to_avoid:
            for u, v, key in street_edges:
                avoid_edge_set.add((u, v, key))

        #Union all NON-avoid edges first (neutral network)
        for u, v, key, data in G.edges(keys=True, data=True):
            if (u, v, key) not in avoid_edge_set:
                dsu.union(u, v)

        # If s and t are already connected via neutral edges, we can avoid all dispreferred streets.
        if dsu.find(s) == dsu.find(t):
            # Build subgraph with ONLY neutral edges
            allowed_edge_set = {
                (u, v, key)
                for u, v, key in G.edges(keys=True)
                if (u, v, key) not in avoid_edge_set
            }
            H = _build_subgraph(G, allowed_edge_set)
            path_edges = _shortest_path_edges(H, s, t)

            log = (
                "Source and destination are connected using only non-dispreferred streets. "
                "All requested streets to avoid were successfully avoided."
            )
            return path_edges, log

        # Need some dispreferred streets: add them back from least to most disliked 
        # edges_to_avoid / street_names_to_avoid are in decreasing dispreference:
        #   index 0 = most hated, last = least hated.
        # We want to bring back least-disliked first, so we iterate in reverse.
        streets_reversed = list(
            zip(reversed(self.edges_to_avoid), reversed(self.street_names_to_avoid))
        )

        required_edges: set[Tuple[int, int, int]] = set()
        included_streets: List[str] = []

        for street_edges, street_name in streets_reversed:
            for u, v, key in street_edges:
                dsu.union(u, v)
                required_edges.add((u, v, key))

            included_streets.append(street_name)

            if dsu.find(s) == dsu.find(t):
                # We just reached connectivity; no need to add more dispreferred streets
                break

        if dsu.find(s) != dsu.find(t):
            raise ValueError(
                "No path between source and destination exists in the graph."
            )

        #  Build set of allowed edges for routing ---
        allowed_edge_set = set()
        for u, v, key in G.edges(keys=True):
            if (u, v, key) not in avoid_edge_set:
                # Neutral edges are always allowed
                allowed_edge_set.add((u, v, key))
            elif (u, v, key) in required_edges:
                # Dispreferred edge is only allowed if it was required for connectivity
                allowed_edge_set.add((u, v, key))

        # Build the restricted graph and compute shortest path
        H = _build_subgraph(G, allowed_edge_set)
        path_edges = _shortest_path_edges(H, s, t)

        # Build logs about what portion of the user's request was satisfied 
        included_set = set(included_streets)
        avoided_streets = [
            name for name in self.street_names_to_avoid if name not in included_set
        ]

        log_lines = [
            f"Total dispreferred streets in request: {len(self.street_names_to_avoid)}",
            f"Streets that could NOT be omitted (needed in some s–t connection): {included_streets if included_streets else 'None'}",
            f"Streets successfully avoided: {avoided_streets if avoided_streets else 'None'}",
        ]
        log = "\n".join(log_lines)

        return path_edges, log
