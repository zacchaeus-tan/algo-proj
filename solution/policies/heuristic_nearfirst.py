"""Variation of heuristic_best: the first stop is the nearest location to the hub that has an on-time parcel."""

import heapq
from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import (
    HUB,
    arrival_time,
    extend_trip,
    group_by_location,
    in_window,
    waiting_parcels,
)


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build one trip of stops where parcels will arrive inside their windows.

    Waiting parcels are grouped in a hash map keyed by location. For each stop the
    vehicle could reach next, its arrival time decides which parcels there would be
    on time. The first stop is the location with the most on-time parcels (ties:
    nearer the hub); later stops follow the nearest-neighbour heuristic among
    locations with at least one on-time parcel. At each stop, on-time parcels are
    loaded most urgent first (earliest window end, via a heap), then parcels whose
    window has already closed fill any spare space. Parcels that would arrive early
    stay at the hub for a later trip. If no stop has an on-time parcel, the vehicle
    waits for the next planning round. Inputs are snapshots and are never modified.
    """

    distances = context["travel_distance"]
    capacity = context["capacity"]

    groups = group_by_location(parcel, waiting_parcels(parcel))

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
            trip_distance = extend_trip(context, travelled, location, destination)
            if trip_distance is None:
                continue
            reach = arrival_time(context, trip_distance)
            on_time = sum(
                1 for parcel_id in parcel_ids
                if in_window(parcel[parcel_id], reach) and load + parcel[parcel_id]["size"] <= capacity
            )
            if on_time == 0:
                continue
            if location == HUB:
                # First stop: most on-time parcels, then nearest to the hub.
                key = (distances[HUB][destination], destination)
            else:
                # Later stops: nearest neighbour from the current stop.
                key = (distances[location][destination], destination)
            if best_key is None or key < best_key:
                best, best_key, best_distance = destination, key, trip_distance
        if best is None:
            break

        reach = arrival_time(context, best_distance)
        on_time_heap = []
        late = []
        for parcel_id in groups.pop(best):
            record = parcel[parcel_id]
            if in_window(record, reach):
                on_time_heap.append((record["delivery_window_end"], parcel_id))
            elif record["delivery_window_end"] < reach:
                late.append(parcel_id)
        # Min-heap on window end: the most urgent on-time parcel is popped first.
        heapq.heapify(on_time_heap)
        while on_time_heap:
            _, parcel_id = heapq.heappop(on_time_heap)
            if load + parcel[parcel_id]["size"] <= capacity:
                route.append(parcel_id)
                load += parcel[parcel_id]["size"]
        # Already-late parcels cost no extra km here, so they use any space left.
        for parcel_id in late:
            if load + parcel[parcel_id]["size"] <= capacity:
                route.append(parcel_id)
                load += parcel[parcel_id]["size"]
        travelled = best_distance
        location = best
    return route
