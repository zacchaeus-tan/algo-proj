"""Ablation of heuristic_timed: no cluster limit, so a trip may jump to any next stop."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.heuristic_timed import plan_trip


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Same as heuristic_timed, but nearest neighbour may pick a stop at any distance."""

    return plan_trip(parcel, context, radius=float("inf"))
