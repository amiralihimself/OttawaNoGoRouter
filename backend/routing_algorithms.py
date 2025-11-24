from dataclasses import dataclass
from typing import List, Tuple, Union
import networkx

@dataclass
class CoreRoutingAlgorithm:
    ottawa_road_network: networkx.classes.multidigraph.MultiDiGraph
    source_vertex: int
    """An int representing the start vertex in the corresponsding road network of Ottawa"""
    destination_vertex: Union[str, None]
    """An int representing the destination vertex in the corresponsding road network of Ottawa"""
    edges_to_avoid:List[Tuple[int,int,int]]
    """A list of edges to avoid in decreasing order of dispreference. Every edge in the road network is shown using a tuple of three integers. """
    
    def __post_init__(self):
        return 0
        
    
    