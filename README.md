# OttawaNoGoRouter

<img width="1003" height="499" alt="image" src="https://github.com/user-attachments/assets/f75c4f07-0efc-4acf-8319-84b859856214" />

After living in Ottawa for a few years, I have grown to love the city. At the same time, there are a few streets I personally try to avoid when driving, depending on traffic, construction, or just preference. To my surprise, most existing route planning apps do not let you say “avoid these specific streets” in a flexible way. OttawaNoGoRouter is my attempt to build that feature.

OttawaNoGoRouter is a full-stack web app that computes a driving route while trying to avoid user-provided streets as much as possible. You provide a start address, a destination address, and a list of streets you would like to avoid in **decreasing order of dispreference** (most dispreferred first). The router avoids as many as it can, and if avoiding everything is not feasible, it relaxes the constraints gradually until a route becomes possible. The app also returns a short routing log explaining what happened.

## What the app does

- Takes:
  - Start address
  - Destination address
  - A list of streets to avoid (one per line), ordered from most dispreferred to least dispreferred
- Tries to avoid all dispreferred streets if possible
- If that is not possible, it adds back dispreferred streets gradually, starting from the least dispreferred, until start and destination become connected
- Computes a shortest path on the resulting restricted network
- Visualizes the route on an interactive map and shows a routing log

## Examples

**Note on inputs.**  
Addresses should correspond to places in Ottawa. Standard civic addresses like `296 Bank St` work perfectly. In most cases, well-known place names like `Parliament of Canada` also work, though I have seen cases where the app was unable to locate specific places using only their names.

These examples are intentionally simple, but the app also supports long routes across the city.

---

### Example 1: Basic route (no dispreferred streets)

- Start: `Parliament of Canada`
- Destination: `296 Bank St`
- Avoid list: *(empty)*

**Result:** A route is computed and displayed on the map.

<img width="1300" height="500" alt="example1" src="https://github.com/user-attachments/assets/cab51781-3345-46f8-b63c-64c196deb6bd" />

---

### Example 2: Avoid one street

- Start: `Parliament of Canada`
- Destination: `296 Bank St`
- Avoid list (in decreasing order of dispreference):
  1. `Albert St`

**Result:** The computed route avoids `Albert St`, and the log reports that the requested dispreferred street was successfully avoided.

<img width="1300" height="500" alt="example2" src="https://github.com/user-attachments/assets/7b871611-2af0-4f68-bdf9-e28972600fd0" />

---

### Example 3: Avoid two streets (ordered)

- Start: `Parliament of Canada`
- Destination: `296 Bank St`
- Avoid list (in decreasing order of dispreference):
  1. `Albert St` (more dispreferred)
  2. `Queen St` (less dispreferred)

**Result:** The computed route avoids both `Albert St` and `Queen St`, and the log reports that all requested dispreferred streets were successfully avoided.

<img width="1300" height="500" alt="example3" src="https://github.com/user-attachments/assets/7f7944ca-b7a4-47bc-af37-4c956d7e387c" />

## Tech stack

**Frontend**
- React (Vite)
- Leaflet via `react-leaflet` for map rendering and route visualization

**Backend**
- Python + Flask (REST API)
- Pydantic for request validation
- NetworkX for graph representation and graph operations
- OpenStreetMap-based road network data (loaded into a graph)

## The Routing Algorithm 

Ottawa’s road network is modeled as a graph:
- Intersections are nodes
- Road segments are edges

The routing algorithm treats the user’s avoid-list as “dispreferred” streets, ordered from most dispreferred to least dispreferred.

1. Convert each dispreferred street into the set of road edges that belong to that street.
2. Build a “neutral” graph by removing all dispreferred edges. The dispreferred edges are the ones corresponding to some dispreferred street spcified by the user. 
3. Use the Disjoint Set Union (DSU) data structire (Union-Find) to check if the start and destination are connected using only neutral edges. This data structure lets us check connecitivity in $\mathcal{O}(1)$ amortized time after adding each edge. This is a massive speed up over running a BFS on the entire graph every time.
   - If source and destination are connected, we compute a shortest path using only neutral edges and we successfully avoid all dispreferred streets.
4. If they are not connected, we add dispreferred streets back in reverse order (least dispreferred first) until connectivity is restored. This is effectively equivalent to continuously removing the edges corresponding to dispreferred streets from most dispreferred to least preferred until we can no longer do so, i.e., we stop when source and destination become disconnected. 
5. Compute a shortest path on the restricted graph containing:
   - all neutral edges, plus
   - only the dispreferred edges that were required to restore connectivity.
6. Return the route and a routing log describing which streets were successfully avoided versus which ones had to be included.

### Fuzzy matching of street names

User-provided street names are mapped to actual street names in the OpenStreetMap network using fuzzy string matching (via `difflib.SequenceMatcher`). This helps handle small spelling differences and formatting variations.

## API

The backend exposes a REST endpoint:

### `POST /api/find_route`

Example request:

```json
{
  "start_address": "Parliament of Canada",
  "destination_address": "296 Bank St",
  "avoid": ["Bank St"]
}
