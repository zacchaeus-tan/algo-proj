"""Shared helpers for the dispatch policies: waiting parcels, grouping and trip checks."""

from typing import Dict, Iterable, List, Optional

from simulator.models import Parcel, SimulationContext

HUB = "HUB"


def waiting_parcels(parcel: Dict[str, Parcel]) -> List[str]:
    """Return the IDs of parcels not yet assigned to a vehicle, oldest arrival first.

    Parcel IDs break arrival-time ties, as in the baseline. Scanning every arrived
    parcel is O(N) and sorting the n waiting ones is O(n log n).
    """

    return sorted(
        (parcel_id for parcel_id, record in parcel.items() if record["vehicle_assigned"] is None),
        key=lambda parcel_id: (parcel[parcel_id]["arrival_time"], parcel_id),
    )


def group_by_location(parcel: Dict[str, Parcel], parcel_ids: Iterable[str]) -> Dict[str, List[str]]:
    """Group parcel IDs in a hash map keyed by delivery location, keeping their order.

    One pass with an O(1) average insert per parcel, so O(n) in total.
    """

    groups: Dict[str, List[str]] = {}
    for parcel_id in parcel_ids:
        groups.setdefault(parcel[parcel_id]["delivery_location_id"], []).append(parcel_id)
    return groups


def extend_trip(
    context: SimulationContext, travelled: float, location: str, destination: str
) -> Optional[float]:
    """Return the km from the hub to `destination` if the trip can still stop there.

    `travelled` is the km from the hub to `location`, the trip's current last stop.
    The stop is allowed only if the vehicle can still drive back to the hub within
    its range and before the return cutoff. Returns None otherwise. O(1).
    """

    distances = context["travel_distance"]
    trip_distance = travelled + distances[location][destination]
    round_trip = trip_distance + distances[destination][HUB]
    departure = context["current_time"] + context["departure_delay"]
    # At 60 km/h, km also equals travel time in minutes.
    if round_trip > context["max_trip_distance_km"] or departure + round_trip > context["return_cutoff"]:
        return None
    return trip_distance


def arrival_time(context: SimulationContext, km_from_hub: float) -> float:
    """Return when the vehicle reaches a stop `km_from_hub` along its route (1 km = 1 minute)."""

    return context["current_time"] + context["departure_delay"] + km_from_hub


def in_window(record: Parcel, time: float) -> bool:
    """Return True if `time` falls inside the parcel's delivery window, edges included."""

    return record["delivery_window_start"] <= time <= record["delivery_window_end"]
