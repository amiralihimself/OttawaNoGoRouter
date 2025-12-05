from typing import Dict, List


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
