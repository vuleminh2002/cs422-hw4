import argparse
import json
from dataclasses import dataclass
from typing import Dict, Tuple

import gurobipy as gp
from gurobipy import GRB


@dataclass(frozen=True)
class TopologySolution:
    scale: float
    edges: Tuple[Tuple[int, int], ...]
    routing: Dict[Tuple[int, int, int, int], float]


def construct_optimal_uniform_topology(
    n: int, d: int, *, verbose: bool = False
) -> TopologySolution:
    if (
        not isinstance(n, int)
        or isinstance(n, bool)
        or not isinstance(d, int)
        or isinstance(d, bool)
        or n < 2
        or not 1 <= d <= n - 1
    ):
        raise ValueError("Require integer n >= 2 and 1 <= d <= n - 1.")

    nodes = range(n)
    arcs = [(u, v) for u in nodes for v in nodes if u != v]
    flow_keys = [(s, t, u, v) for s, t in arcs for u, v in arcs]
    demand = d / (n - 1)

    with gp.Env(params={"OutputFlag": int(verbose)}) as env:
        with gp.Model("optimal_uniform_topology", env=env) as model:
            model.Params.MIPGap = 0.0
            model.Params.MIPGapAbs = 0.0
            model.Params.FeasibilityTol = 1e-9
            model.Params.IntFeasTol = 1e-9

            links = model.addVars(arcs, vtype=GRB.BINARY, name="link")
            flows = model.addVars(flow_keys, lb=0.0, name="flow")
            scale = model.addVar(
                lb=0.0,
                ub=(n - 1) / (2 * (n - 1) - d),
                name="lambda",
            )

            for u in nodes:
                model.addConstr(
                    gp.quicksum(links[u, v] for v in nodes if v != u) == d,
                    name=f"out_degree[{u}]",
                )
                model.addConstr(
                    gp.quicksum(links[v, u] for v in nodes if v != u) == d,
                    name=f"in_degree[{u}]",
                )

            for u, v in arcs:
                model.addConstr(
                    gp.quicksum(flows[s, t, u, v] for s, t in arcs)
                    <= links[u, v],
                    name=f"capacity[{u},{v}]",
                )

            for s, t in arcs:
                for u in nodes:
                    balance = 1 if u == s else -1 if u == t else 0
                    model.addConstr(
                        gp.quicksum(
                            flows[s, t, u, v] for v in nodes if v != u
                        )
                        - gp.quicksum(
                            flows[s, t, v, u] for v in nodes if v != u
                        )
                        == balance * demand * scale,
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
            routing = {}
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
                if value > 0.0:
                    routing[key] = value

            return TopologySolution(scale=scale.X, edges=edges, routing=routing)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synthesize an optimal uniform-traffic directed topology."
    )
    parser.add_argument("n", type=int)
    parser.add_argument("d", type=int)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    if args.n < 2 or not 1 <= args.d <= args.n - 1:
        parser.error("Require n >= 2 and 1 <= d <= n - 1.")

    solution = construct_optimal_uniform_topology(
        args.n, args.d, verbose=args.verbose
    )
    print(
        json.dumps(
            {
                "n": args.n,
                "d": args.d,
                "lambda": solution.scale,
                "edges": solution.edges,
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
