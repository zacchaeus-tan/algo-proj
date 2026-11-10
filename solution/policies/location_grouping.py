"""Location grouping: load the busiest location first, then visit the nearest other locations."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext

HUB = "HUB"


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build one trip that groups parcels by delivery location.

    Waiting parcels are grouped in a hash map keyed by location, oldest first.
    The first stop is the location with the most waiting parcels (ties: nearer
    the hub). After that, the van moves to the nearest location it can still
    reach (nearest-neighbour heuristic). At each stop it loads every parcel that
    fits, oldest first. A stop is only chosen if the trip can still return to the
    hub within range and before the cutoff. Delivery windows are ignored.
    Inputs are snapshots and are never modified.
    """

    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]
    max_distance = context["max_trip_distance_km"]
    capacity = context["capacity"]

    waiting = sorted(
        (parcel_id for parcel_id, record in parcel.items() if record["vehicle_assigned"] is None),
        key=lambda parcel_id: (parcel[parcel_id]["arrival_time"], parcel_id),
    )
    # Hash map: location -> its waiting parcel IDs, oldest first.
    groups: Dict[str, List[str]] = {}
    for parcel_id in waiting:
        groups.setdefault(parcel[parcel_id]["delivery_location_id"], []).append(parcel_id)
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
        for destination, parcel_ids in groups.items():
            if load + smallest[destination] > capacity:
                continue
            trip_distance = travelled + distances[location][destination]
            round_trip = trip_distance + distances[destination][HUB]
            # At 60 km/h, km also equals travel time in minutes.
            if round_trip > max_distance or departure + round_trip > context["return_cutoff"]:
                continue
            if location == HUB:
                # First stop: most waiting parcels, then nearest to the hub.
                key = (-len(parcel_ids), distances[HUB][destination], destination)
            else:
                # Later stops: nearest neighbour from the current stop.
                key = (distances[location][destination], destination)
            if best_key is None or key < best_key:
                best, best_key = destination, key
        if best is None:
            break
        for parcel_id in groups.pop(best):
            if load + parcel[parcel_id]["size"] <= capacity:
                route.append(parcel_id)
                load += parcel[parcel_id]["size"]
        travelled += distances[location][best]
        location = best
    return route
