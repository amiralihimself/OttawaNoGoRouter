from dataclasses import dataclass, field
import difflib
from typing import Dict, List, Tuple, Union
import networkx as nx
from pathlib import Path
import osmnx as ox

PATH_TO_GRAPH = "backend/ottawa_drive.graphml"
LOCAL_CITY_NAMES = [
    "ottawa",
    "kanata",
    "nepean",
    "orleans",
    "gloucester",
    "vanier",
    "manotick",
    "greely",
    "stittsville",
]


@dataclass
class OttawaGraphNetwork:
    G: nx.classes.multidigraph.MultiDiGraph = field(init=False)

    def __post_init__(self):
        graph_path = Path(PATH_TO_GRAPH)
        if not graph_path.exists():
            # the graph does not exist, we will fetch it
            self.G = ox.graph_from_place(
                "Ottawa, Ontario, Canada", network_type="drive", simplify=True
            )
            ox.save_graphml(self.G, PATH_TO_GRAPH)

        else:
            self.G = ox.load_graphml(PATH_TO_GRAPH)

    def get_street_edges_to_avoid(
        self,
        input_street_names: List[str],
    ) -> Tuple[list[str], List[List[Tuple[int, int, int]]]]:
        """Given a list of street names in sorted order of dispreference, return a tuple with two things
        1) The set of edge names that were matched to these street names respectively, and
        2) the set of edges in Ottawa's road network corresponding to these streets, in the same order.
        Every edge in the road network is shown using a tuple of three integers.
        Furthermore, every street is associated with 1 or more edge."""

        all_street_edges_to_avoid: List[List[Tuple[int, int, int]]] = []
        matched_street_names_in_the_network: List[str] = []
        for input_street_name in input_street_names:
            input_street_name = input_street_name.lower()
            # we use a fuzzy matching technique
            highest_similarity_threshold = -1000
            most_similar_street_name = "INVALID STRING"
            input_street_edges: List[Tuple[int, int, int]] = []
            for u, v, key, data in self.G.edges(keys=True, data=True):
                name = data.get("name")
                if name is None:
                    continue

                elif isinstance(name, str):
                    name = name.lower()
                    if name == most_similar_street_name:
                        input_street_edges.append((u, v, key))
                    else:
                        matcher = difflib.SequenceMatcher(None, input_street_name, name)
                        similarity_ratio = matcher.ratio()
                        if similarity_ratio > highest_similarity_threshold:
                            highest_similarity_threshold = similarity_ratio
                            most_similar_street_name = name
                            input_street_edges = [(u, v, key)]

            all_street_edges_to_avoid.append(input_street_edges)
            matched_street_names_in_the_network.append(most_similar_street_name.title())

        return matched_street_names_in_the_network, all_street_edges_to_avoid

    def _graph_bbox(self) -> Tuple[float, float, float, float]:
        """Return (south, north, west, east) for self.G (Ottawa's graph)"""
        north = self.G.graph.get("north")
        south = self.G.graph.get("south")
        east = self.G.graph.get("east")
        west = self.G.graph.get("west")

        if None in (north, south, east, west):
            ys = [data["y"] for _, data in self.G.nodes(data=True)]
            xs = [data["x"] for _, data in self.G.nodes(data=True)]
            north, south = max(ys), min(ys)
            east, west = max(xs), min(xs)

        return south, north, west, east

    def _geocode_in_graph_extent(self, query: str) -> Tuple[float, float]:
        """
        Geocode query (a str) and ensure the result is inside or near
        the Ottawa graph bounding box. Raises ValueError otherwise.
        """
        try:
            lat, lon = ox.geocode(query)
        except Exception as e:
            raise ValueError(f"Could not geocode query {query!r}: {e}") from e

        south, north, west, east = self._graph_bbox()

        # allow a bit of slack (~5km) in each direction
        margin = 0.05
        if not (
            south - margin <= lat <= north + margin
            and west - margin <= lon <= east + margin
        ):
            raise ValueError(
                f"Geocoded point ({lat:.6f}, {lon:.6f}) is outside the Ottawa "
                f"road network extent."
            )

        return lat, lon

    def get_closest_vertex_to_an_ottawa_address(self, address: str) -> Tuple[int, str]:
        """
        Given a user-provided address string, try to interpret it as an address
        in the Ottawa / Greater Ottawa Area and return the nearest vertex in self.G.

        We do not require the user to type 'Ottawa'. We:
          - build a list of candidate queries,
          - geocode each,
          - keep the first result that falls within the Ottawa graph extent.
        The output is a Tuple[int, str]. the int represents the closest vertex in G, and a string corresponding to the address we interpreted it as.
        """

        if not isinstance(address, str) or not address.strip():
            raise ValueError("Address must be a non-empty string.")

        base = address.strip()
        lower = base.lower()

        # Build candidate queries, in priority order.
        candidates: List[str] = []

        # If user did NOT explicitly mention a local city name, we prepend "Ottawa, ON"
        if not any(city in lower for city in LOCAL_CITY_NAMES):
            candidates.append(f"{base}, Ottawa, Ontario, Canada")

        # Always try the raw address as well just to be safe
        candidates.append(base)

        last_error: Union[Exception, None] = None

        for q in candidates:
            try:
                lat, lon = self._geocode_in_graph_extent(q)
                # If we get here, point is inside (or near) the Ottawa graph extent
                node = ox.distance.nearest_nodes(self.G, X=lon, Y=lat)
                return node, q
            except ValueError as e:
                last_error = e
                continue

        # If all candidates failed:
        raise ValueError(
            f"Could not interpret {address!r} as an address within the Ottawa "
            f"road network. Last error: {last_error}"
        )


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
