from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Union
import networkx

from backend.utils import DisjointSetUnion


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

    def find_route(self) -> Tuple[List[Tuple[int, int, int]], str]:
        nodes = list(self.ottawa_road_network.nodes)
        dsu = DisjointSetUnion(nodes)
        included_edges: List[Tuple[int, int, int]] = []
        log_messages: List[str] = []

        # Process streets in the order provided by edges_to_avoid
        for street_idx, street_edges in enumerate(self.edges_to_avoid):
            # Temporarily add all edges of the street
            temp_union_made = False
            for u, v, key in street_edges:
                if dsu.union(u, v):
                    temp_union_made = True

            # Check if source and destination are now connected
            if self.destination_vertex is not None and dsu.find(
                self.source_vertex
            ) == dsu.find(self.destination_vertex):
                # Cannot omit this street fully without disconnecting s-t
                # Log that some streets could not be avoided
                if temp_union_made:
                    log_messages.append(
                        f"Street '{self.street_names_to_avoid[street_idx]}' could not be avoided; included to maintain s-t connectivity."
                    )
                # All its edges must be added
                included_edges.extend(street_edges)
            else:
                # Street successfully avoided
                log_messages.append(
                    f"Street '{self.street_names_to_avoid[street_idx]}' fully avoided."
                )
                # Do NOT add edges to included_edges; they are omitted

        # Final check in case destination is None
        if self.destination_vertex is None:
            log_messages.append(
                "Destination not specified; all processed streets handled as above."
            )

        return included_edges, "\n".join(log_messages)
