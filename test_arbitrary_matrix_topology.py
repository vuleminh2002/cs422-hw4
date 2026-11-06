import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from arbitrary_matrix_topology import (
    DEGREE,
    LINK_CAPACITY,
    N_NODES,
    SAMPLE_DEMAND_MATRIX,
    solve_arbitrary_matrix,
)


class ArbitraryMatrixTopologyTests(unittest.TestCase):
    def test_sample_matrix_solution_is_feasible_and_optimal(self) -> None:
        solution = solve_arbitrary_matrix(SAMPLE_DEMAND_MATRIX)
        edges = set(solution.edges)

        self.assertAlmostEqual(solution.scale, 1.0, places=7)
        self.assertEqual(len(edges), N_NODES * DEGREE)
        for node in range(N_NODES):
            self.assertEqual(sum(u == node for u, _ in edges), DEGREE)
            self.assertEqual(sum(v == node for _, v in edges), DEGREE)

        for u, v in edges:
            load = sum(
                amount
                for (_, _, flow_u, flow_v), amount in solution.routing.items()
                if (flow_u, flow_v) == (u, v)
            )
            self.assertLessEqual(load, LINK_CAPACITY + 1e-7)

        for s in range(N_NODES):
            for t in range(N_NODES):
                if SAMPLE_DEMAND_MATRIX[s][t] == 0:
                    continue
                for node in range(N_NODES):
                    net_outflow = sum(
                        amount * ((u == node) - (v == node))
                        for (source, destination, u, v), amount in solution.routing.items()
                        if (source, destination) == (s, t)
                    )
                    expected = solution.scale * SAMPLE_DEMAND_MATRIX[s][t] * (
                        1 if node == s else -1 if node == t else 0
                    )
                    self.assertAlmostEqual(net_outflow, expected, places=7)

        # Node 0 has 4 units of outgoing demand and only 4 units of outgoing
        # link capacity, so no feasible solution can have scale above 1.
        self.assertLessEqual(solution.scale, 1.0 + 1e-7)

    def test_invalid_demand_matrices(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly 8 rows"):
            solve_arbitrary_matrix([[0.0]])

        diagonal_demand = [list(row) for row in SAMPLE_DEMAND_MATRIX]
        diagonal_demand[0][0] = 1
        with self.assertRaisesRegex(ValueError, "Self-demands"):
            solve_arbitrary_matrix(diagonal_demand)

        negative_demand = [list(row) for row in SAMPLE_DEMAND_MATRIX]
        negative_demand[0][1] = -1
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            solve_arbitrary_matrix(negative_demand)

        no_traffic = [[0] * N_NODES for _ in range(N_NODES)]
        with self.assertRaisesRegex(ValueError, "At least one"):
            solve_arbitrary_matrix(no_traffic)

        nonfinite_demand = [list(row) for row in SAMPLE_DEMAND_MATRIX]
        nonfinite_demand[0][1] = math.inf
        with self.assertRaisesRegex(ValueError, "finite and nonnegative"):
            solve_arbitrary_matrix(nonfinite_demand)

    def test_cli_accepts_a_json_demand_matrix(self) -> None:
        script = Path(__file__).with_name("arbitrary_matrix_topology.py")
        with tempfile.TemporaryDirectory() as directory:
            demand_file = Path(directory) / "demands.json"
            demand_file.write_text(json.dumps(SAMPLE_DEMAND_MATRIX), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script), "--demand-file", str(demand_file)],
                capture_output=True,
                text=True,
                check=True,
            )

        output = json.loads(result.stdout)
        self.assertEqual(output["n"], N_NODES)
        self.assertEqual(output["d"], DEGREE)
        self.assertAlmostEqual(output["lambda"], 1.0, places=7)
        self.assertEqual(len(output["edges"]), N_NODES * DEGREE)


if __name__ == "__main__":
    unittest.main()
