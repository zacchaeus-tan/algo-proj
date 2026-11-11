"""Sensitivity run of heuristic_timed: fill trigger at 24 units instead of 28."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.heuristic_timed import plan_trip


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Same as heuristic_timed with fill=24.0."""

    return plan_trip(parcel, context, fill=24.0)
