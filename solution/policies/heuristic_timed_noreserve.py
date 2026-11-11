"""Ablation of heuristic_timed: no fleet reservation for parcels with a future window."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.heuristic_timed import plan_trip


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Same as heuristic_timed, but a vehicle may leave even if it misses the next wave."""

    return plan_trip(parcel, context, reserve=False)
