"""Urgency-first dispatch: Earliest Deadline First with a min-heap.

Waiting parcels are placed in a min-heap keyed on delivery_window_end, so the
parcel whose window closes soonest is considered first. Each popped parcel is
added to the trip only if, at the point it would be reached along the route
built so far, it would arrive INSIDE its window:

* arrival after window end   -> skipped (it would score as a fail anyway, so it
                                should not take van space from parcels that can
                                still be on time)
* arrival before window start -> held at the hub for a later trip (an early
                                delivery also counts as a fail)

The hard constraints (capacity, trip range, 18:00 return) are checked exactly as
in the baseline. Stops are visited in the order parcels are added, i.e. in
deadline order. Inputs are snapshots and are never modified.
"""

import heapq
from typing import Dict, List

from simulator.models import Parcel, SimulationContext

HUB = "HUB"


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build one trip for context["vehicle_id"], most urgent feasible parcels first."""

    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]
    max_distance = context["max_trip_distance_km"]
    capacity = context["capacity"]
    cutoff = context["return_cutoff"]

    # Min-heap of (window end, arrival time, parcel ID) for every waiting parcel.
    # Ties on window end go to the parcel that arrived first, then to the ID.
    heap = [
        (record["delivery_window_end"], record["arrival_time"], parcel_id)
        for parcel_id, record in parcel.items()
        if record["vehicle_assigned"] is None
    ]
    heapq.heapify(heap)  # O(n)

    route: List[str] = []
    load = 0.0
    travelled = 0.0  # km driven from the hub to the current location
    location = HUB

    while heap and load < capacity:
        window_end, _, parcel_id = heapq.heappop(heap)  # O(log n)
        record = parcel[parcel_id]

        # Hard constraint 1: capacity.
        if load + record["size"] > capacity:
            continue

        destination = record["delivery_location_id"]
        trip_distance = travelled + distances[location][destination]
        # 60 km/h, so km driven = minutes driven; service time is zero.
        arrival = departure + trip_distance

        # Soft constraint (our metric): only take parcels that land inside their window.
        if arrival > window_end:
            continue  # too late on this trip
        if arrival < record["delivery_window_start"]:
            continue  # too early: hold for a later trip

        # Hard constraints 2 and 3: trip range and return by the cutoff.
        round_trip = trip_distance + distances[destination][HUB]
        if round_trip > max_distance or departure + round_trip > cutoff:
            continue

        route.append(parcel_id)
        load += record["size"]
        travelled = trip_distance
        location = destination

    return route
