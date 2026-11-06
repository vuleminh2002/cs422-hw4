import argparse
import json
import math
from dataclasses import dataclass
from numbers import Real
from pathlib import Path
from typing import Dict, Sequence, Tuple

import gurobipy as gp
from gurobipy import GRB


N_NODES = 8
DEGREE = 4
LINK_CAPACITY = 1.0
SAMPLE_DEMAND_MATRIX = (
    (0, 0, 0, 0, 4, 0, 0, 0),
    (0, 0, 0, 0, 0, 3, 0, 0),
    (0, 0, 0, 0, 0, 0, 2, 0),
    (0, 0, 0, 0, 0, 0, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 0),
    (0, 2, 0, 0, 0, 0, 0, 0),
    (0, 0, 1, 0, 0, 0, 0, 0),
    (0, 0, 0, 1, 0, 0, 0, 0),
)


@dataclass(frozen=True)
class TopologySolution:
    scale: float
    edges: Tuple[Tuple[int, int], ...]
    routing: Dict[Tuple[int, int, int, int], float]


def _validate_demands(
    demands: Sequence[Sequence[Real]],
) -> Tuple[Tuple[float, ...], ...]:
    if (
        not isinstance(demands, Sequence)
        or isinstance(demands, (str, bytes))
        or len(demands) != N_NODES
    ):
        raise ValueError(f"Demand matrix must have exactly {N_NODES} rows.")

    normalized = []
    for i, row in enumerate(demands):
        if (
            not isinstance(row, Sequence)
            or isinstance(row, (str, bytes))
            or len(row) != N_NODES
        ):
            raise ValueError(
                f"Demand matrix row {i} must have exactly {N_NODES} entries."
            )
        values = []
        for j, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError(f"Demand D[{i}][{j}] must be a real number.")
            amount = float(value)
            if not math.isfinite(amount) or amount < 0:
                raise ValueError(f"Demand D[{i}][{j}] must be finite and nonnegative.")
            if i == j and amount != 0:
                raise ValueError("Self-demands must be zero.")
            values.append(amount)
        normalized.append(tuple(values))

    if not any(normalized[i][j] > 0 for i in range(N_NODES) for j in range(N_NODES)):
        raise ValueError("At least one off-diagonal demand must be positive.")
    return tuple(normalized)


def solve_arbitrary_matrix(
    demands: Sequence[Sequence[Real]], *, verbose: bool = False
) -> TopologySolution:
    matrix = _validate_demands(demands)
    nodes = range(N_NODES)
    arcs = [(u, v) for u in nodes for v in nodes if u != v]
    commodities = [
        (s, t)
        for s in nodes
        for t in nodes
        if s != t and matrix[s][t] > 0
    ]
    flow_keys = [(s, t, u, v) for s, t in commodities for u, v in arcs]
    lambda_upper_bound = N_NODES * DEGREE * LINK_CAPACITY / sum(
        matrix[s][t] for s, t in commodities
    )

    with gp.Env(params={"OutputFlag": int(verbose)}) as env:
        with gp.Model("arbitrary_matrix_topology_8_4", env=env) as model:
            model.Params.MIPGap = 0.0
            model.Params.MIPGapAbs = 0.0
            model.Params.FeasibilityTol = 1e-9
            model.Params.IntFeasTol = 1e-9

            links = model.addVars(arcs, vtype=GRB.BINARY, name="link")
            flows = model.addVars(flow_keys, lb=0.0, name="flow")
            scale = model.addVar(
                lb=0.0, ub=lambda_upper_bound, name="lambda"
            )

            for u in nodes:
                model.addConstr(
                    gp.quicksum(links[u, v] for v in nodes if v != u) == DEGREE,
                    name=f"out_degree[{u}]",
                )
                model.addConstr(
                    gp.quicksum(links[v, u] for v in nodes if v != u) == DEGREE,
                    name=f"in_degree[{u}]",
                )

            for u, v in arcs:
                model.addConstr(
                    gp.quicksum(flows[s, t, u, v] for s, t in commodities)
                    <= LINK_CAPACITY * links[u, v],
                    name=f"capacity[{u},{v}]",
                )

            for s, t in commodities:
                for u in nodes:
                    net_outflow = gp.quicksum(
                        flows[s, t, u, v] for v in nodes if v != u
                    ) - gp.quicksum(
                        flows[s, t, v, u] for v in nodes if v != u
                    )
                    balance = 1 if u == s else -1 if u == t else 0
                    model.addConstr(
                        net_outflow == balance * matrix[s][t] * scale,
                        name=f"conservation[{s},{t},{u}]",
                    )

            model.setObjective(scale, GRB.MAXIMIZE)
            model.optimize()
            if model.Status != GRB.OPTIMAL:
                raise RuntimeError(
                    "Global optimality was not established; "
                    f"Gurobi status: {model.Status}."
                )

            edges = tuple(arc for arc in arcs if links[arc].X > 0.5)
            installed = set(edges)
            routing: Dict[Tuple[int, int, int, int], float] = {}
            tolerance = model.Params.FeasibilityTol
            for key in flow_keys:
                value = flows[key].X
                if value < -tolerance:
                    raise RuntimeError(f"Negative flow exceeds solver tolerance: {key}.")
                if (key[2], key[3]) not in installed:
                    if value > tolerance:
                        raise RuntimeError(
                            f"Flow on an absent link exceeds solver tolerance: {key}."
                        )
                    continue
                if value > tolerance:
                    routing[key] = value

            return TopologySolution(scale=scale.X, edges=edges, routing=routing)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Optimize an 8-node, degree-4 directed topology for an arbitrary "
            "traffic matrix."
        )
    )
    parser.add_argument(
        "--demand-file",
        type=Path,
        help="JSON file containing an 8x8 matrix (defaults to the sample matrix).",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.demand_file is None:
        demands = SAMPLE_DEMAND_MATRIX
    else:
        try:
            with args.demand_file.open(encoding="utf-8") as demand_file:
                demands = json.load(demand_file)
        except (OSError, json.JSONDecodeError) as error:
            parser.error(f"Could not read demand matrix: {error}")

    try:
        solution = solve_arbitrary_matrix(demands, verbose=args.verbose)
    except ValueError as error:
        parser.error(str(error))
    link_loads = {
        f"{u}->{v}": sum(
            value
            for (s, t, flow_u, flow_v), value in solution.routing.items()
            if (flow_u, flow_v) == (u, v)
        )
        for u, v in solution.edges
    }
    print(
        json.dumps(
            {
                "n": N_NODES,
                "d": DEGREE,
                "lambda": solution.scale,
                "edges": solution.edges,
                "link_loads": link_loads,
                "routing": [
                    {
                        "source": s,
                        "destination": t,
                        "link": [u, v],
                        "flow": value,
                    }
                    for (s, t, u, v), value in solution.routing.items()
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
