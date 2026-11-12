"""Timed combined policy: send a vehicle only when a load is due or full, and keep the fleet home for future windows."""

import heapq
import math
from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import (
    HUB,
    arrival_time,
    extend_trip,
    in_window,
    waiting_parcels,
)

# Minutes before a parcel's last valid planning time at which it counts as due.
MARGIN = 20.0
# Load (out of a capacity of 30) that counts as a full vehicle.
FILL = 28.0
# Locations at most this many km apart count as one cluster. In this data, locations
# inside a cluster are at most 12.9 km apart and clusters are at least 15.8 km apart.
RADIUS = 15.0


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Plan one trip with the chosen settings; see plan_trip."""

    return plan_trip(parcel, context)


def plan_trip(
    parcel: Dict[str, Parcel],
    context: SimulationContext,
    margin: float = MARGIN,
    fill: float = FILL,
    radius: float = RADIUS,
    reserve: bool = True,
) -> List[str]:
    """Plan one trip, or return [] so the vehicle waits for a later planning round.

    1. Timers. For each waiting parcel, assuming a direct trip to its stop:
       release = window start - loading delay - km from hub (earliest planning time
       that is not early), and due = the last planning time at which it can still
       arrive inside its window and return by the cutoff. Parcels past `due` are
       expired; parcels before `release` are kept for later.
    2. Trigger. Send the vehicle only if a ready parcel is within `margin` minutes of
       its due time, or a cluster of nearby locations holds at least `fill` units of
       ready parcels. Otherwise wait, so idle vehicles are free for urgent work.
    3. Route. Start at the urgent parcel's location (or the fullest cluster), then
       greedy nearest neighbour among locations within `radius` km of the current stop
       that still have an on-time parcel. At each stop, on-time parcels are loaded
       most urgent first (min-heap on due time); expired parcels for that stop fill
       spare space at no extra distance.
    4. Reservation (if `reserve`). While parcels with a future window are waiting,
       a trip that is not urgent must return before the earliest of their release
       times, so the whole fleet is at the hub when that wave becomes deliverable.
    Inputs are snapshots and are never modified.
    """

    distances = context["travel_distance"]
    capacity = context["capacity"]
    now = context["current_time"]
    delay = context["departure_delay"]
    cutoff = context["return_cutoff"]

    # 1. Timers: split waiting parcels into ready, expired and future, by location.
    ready: Dict[str, List[str]] = {}
    expired: Dict[str, List[str]] = {}
    due: Dict[str, float] = {}
    future_release = None
    for parcel_id in waiting_parcels(parcel):
        record = parcel[parcel_id]
        loc = record["delivery_location_id"]
        out = distances[HUB][loc]
        release = record["delivery_window_start"] - delay - out
        last = min(record["delivery_window_end"] - delay - out, cutoff - delay - out - distances[loc][HUB])
        if last < now:
            expired.setdefault(loc, []).append(parcel_id)
        elif release > now:
            if future_release is None or release < future_release:
                future_release = release
        else:
            ready.setdefault(loc, []).append(parcel_id)
            due[parcel_id] = last

    if not ready:
        return []

    # 2. Trigger: the most urgent ready parcel is due, or some cluster can fill a vehicle.
    urgent_id = min(due, key=lambda parcel_id: (due[parcel_id], parcel_id))
    urgent = due[urgent_id] - now < margin
    if urgent:
        seed = parcel[urgent_id]["delivery_location_id"]
    else:
        # math.fsum is exactly rounded, so the result is the same on every Python version
        # (plain sum() of floats changed in Python 3.12).
        load_at = {loc: math.fsum(parcel[p]["size"] for p in ids) for loc, ids in ready.items()}
        best_key = None
        seed = None
        for loc in load_at:
            cluster = math.fsum(v for other, v in load_at.items() if distances[loc][other] <= radius)
            key = (-cluster, distances[HUB][loc], loc)
            if best_key is None or key < best_key:
                best_key, seed = key, loc
        if -best_key[0] < fill:
            return []

    # 3. Route: seed first, then nearest neighbour inside the cluster.
    route: List[str] = []
    load = 0.0
    # km from the hub to the route's last stop, not counting the return leg.
    travelled = 0.0
    location = HUB
    remaining = {loc: list(ids) for loc, ids in ready.items()}
    nxt = seed
    while nxt is not None:
        trip_distance = extend_trip(context, travelled, location, nxt)
        if trip_distance is None:
            break
        reach = arrival_time(context, trip_distance)
        # Min-heap on due time: the parcel with the least slack is loaded first.
        heap = [
            (due[p], p)
            for p in remaining.pop(nxt, [])
            if in_window(parcel[p], reach)
        ]
        heapq.heapify(heap)
        while heap:
            _, p = heapq.heappop(heap)
            if load + parcel[p]["size"] <= capacity:
                route.append(p)
                load += parcel[p]["size"]
        # Expired parcels for this stop cost no extra km, so they use any space left.
        for p in expired.pop(nxt, []):
            if load + parcel[p]["size"] <= capacity:
                route.append(p)
                load += parcel[p]["size"]
        travelled = trip_distance
        location = nxt

        nxt = None
        best_d = None
        for loc, ids in remaining.items():
            dist = distances[location][loc]
            if dist > radius or (best_d is not None and dist >= best_d):
                continue
            trip_distance = extend_trip(context, travelled, location, loc)
            if trip_distance is None:
                continue
            reach = arrival_time(context, trip_distance)
            if any(in_window(parcel[p], reach) and load + parcel[p]["size"] <= capacity for p in ids):
                nxt, best_d = loc, dist

    if not route:
        return []

    # 4. Reservation: keep the vehicle home if a non-urgent trip would miss the next wave.
    if reserve and not urgent and future_release is not None:
        back = now + delay + travelled + distances[location][HUB]
        if back > future_release:
            return []
    return route
