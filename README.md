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

## Tech stack

**Frontend**
- React (Vite)
- Leaflet via `react-leaflet` for map rendering and route visualization

**Backend**
- Python + Flask (REST API)
- Pydantic for request validation
- NetworkX for graph representation and graph operations
- OpenStreetMap-based road network data (loaded into a graph)

## How the routing works (high level)

Ottawa’s road network is modeled as a graph:
- Intersections are nodes
- Road segments are edges

The routing algorithm treats the user’s avoid-list as “dispreferred” streets, ordered from most dispreferred to least dispreferred.

1. Convert each dispreferred street into the set of road edges that belong to that street.
2. Build a “neutral” graph by removing all dispreferred edges.
3. Use Disjoint Set Union (Union-Find) to check if the start and destination are connected using only neutral edges.
   - If they are connected, we compute a shortest path using only neutral edges and we successfully avoid all dispreferred streets.
4. If they are not connected, we add dispreferred streets back in reverse order (least dispreferred first) until connectivity is restored.
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
  "start_address": "START ADDRESS",
  "destination_address": "END ADDRESS",
  "avoid": ["Bank St"]
}
