"""Sensitivity run of heuristic_timed: a parcel counts as due 30 minutes before its last round instead of 20."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.heuristic_timed import plan_trip


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Same as heuristic_timed with margin=30.0."""

    return plan_trip(parcel, context, margin=30.0)
