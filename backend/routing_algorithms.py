from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Union
import networkx


@dataclass
class BaseRoutingAlgorithm(ABC):
    """This is the abstract routing algorithm class. Any routing algorithm must be defined as a child of this class."""

    ottawa_road_network: networkx.classes.multidigraph.MultiDiGraph
    source_vertex: int
    """An int representing the start vertex in the corresponding road network of Ottawa"""
    destination_vertex: Union[str, None]
    """An int representing the destination vertex in the corresponding road network of Ottawa"""
    edges_to_avoid: List[Tuple[int, int, int]]
    """A list of edges to avoid in decreasing order of dispreference. Every edge in the road network is shown using a tuple of three integers. """
    street_names_to_avoid: List[str]
    """"The name of the streets to avoid, in case they need to be reference directly in the logs by the routing algorithm(s)"""

    @abstractmethod
    def find_route(self) -> Tuple[List[Tuple[int, int, int]], str]:
        """The routing algorithm must return a list of edges to be included in the shortest path,
        which is of type List[Tuple[int, int, int]]. Moreover, it needs to return a log string
        of type str briefly explaining the result of the algorithm, i.e., if a street could not be
        avoided whatsoever.
        """
        raise NotImplementedError
