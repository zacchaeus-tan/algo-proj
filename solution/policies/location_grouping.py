"""Location grouping: load the busiest location first, then visit the nearest other locations."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import HUB, extend_trip, group_by_location, waiting_parcels


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build one trip that groups parcels by delivery location.

    Waiting parcels are grouped in a hash map keyed by location, oldest first.
    The first stop is the location with the most waiting parcels (ties: nearer
    the hub). After that, the vehicle moves to the nearest location it can still
    reach (nearest-neighbour heuristic). At each stop it loads every parcel that
    fits, oldest first. A stop is only chosen if the trip can still return to the
    hub within range and before the cutoff. Delivery windows are ignored.
    Inputs are snapshots and are never modified.
    """

    distances = context["travel_distance"]
    capacity = context["capacity"]

    groups = group_by_location(parcel, waiting_parcels(parcel))
    # Smallest parcel per location, so "does anything here still fit?" is O(1).
    smallest = {
        destination: min(parcel[parcel_id]["size"] for parcel_id in parcel_ids)
        for destination, parcel_ids in groups.items()
    }

    route: List[str] = []
    load = 0.0
    # km from the hub to the route's last stop, not counting the return leg.
    travelled = 0.0
    location = HUB
    while groups:
        best = None
        best_key = None
        best_distance = 0.0
        for destination, parcel_ids in groups.items():
            if load + smallest[destination] > capacity:
                continue
            trip_distance = extend_trip(context, travelled, location, destination)
            if trip_distance is None:
                continue
            if location == HUB:
                # First stop: most waiting parcels, then nearest to the hub.
                key = (-len(parcel_ids), distances[HUB][destination], destination)
            else:
                # Later stops: nearest neighbour from the current stop.
                key = (distances[location][destination], destination)
            if best_key is None or key < best_key:
                best, best_key, best_distance = destination, key, trip_distance
        if best is None:
            break
        for parcel_id in groups.pop(best):
            if load + parcel[parcel_id]["size"] <= capacity:
                route.append(parcel_id)
                load += parcel[parcel_id]["size"]
        travelled = best_distance
        location = best
    return route
