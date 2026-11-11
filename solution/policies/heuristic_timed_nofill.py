"""Ablation of heuristic_timed: no fill trigger, so a vehicle leaves only when a parcel is due."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.heuristic_timed import plan_trip


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Same as heuristic_timed, but a full cluster alone never sends a vehicle."""

    return plan_trip(parcel, context, fill=float("inf"))
