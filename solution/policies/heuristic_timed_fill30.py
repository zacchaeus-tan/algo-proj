"""Sensitivity run of heuristic_timed: fill trigger at 30 units (a completely full vehicle)."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.heuristic_timed import plan_trip


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Same as heuristic_timed with fill=30.0."""

    return plan_trip(parcel, context, fill=30.0)
