import json
import subprocess
import sys
import unittest
from pathlib import Path

from uniform_topology import construct_optimal_uniform_topology


class UniformTopologyTests(unittest.TestCase):
    def test_known_optima_and_routing_feasibility(self) -> None:
        tolerance = 1e-6
        for n, d, expected in [(2, 1, 1.0), (4, 1, 0.5), (4, 3, 1.0), (5, 2, 2 / 3)]:
            with self.subTest(n=n, d=d):
                solution = construct_optimal_uniform_topology(n, d)
                self.assertAlmostEqual(solution.scale, expected, places=6)
                edges = set(solution.edges)
                self.assertEqual(len(edges), n * d)
                self.assertEqual(len(solution.edges), len(edges))
                for node in range(n):
                    self.assertEqual(sum(u == node for u, v in edges), d)
                    self.assertEqual(sum(v == node for u, v in edges), d)
                for u, v in edges:
                    self.assertNotEqual(u, v)
                    load = sum(
                        value
                        for (s, t, a, b), value in solution.routing.items()
                        if (a, b) == (u, v)
                    )
                    self.assertLessEqual(load, 1.0 + tolerance)
                for (s, t, u, v), value in solution.routing.items():
                    self.assertNotEqual(s, t)
                    self.assertIn((u, v), edges)
                    self.assertGreater(value, 0.0)

                demand = solution.scale * d / (n - 1)
                for s in range(n):
                    for t in range(n):
                        if s == t:
                            continue
                        for node in range(n):
                            balance = sum(
                                value * ((u == node) - (v == node))
                                for (a, b, u, v), value in solution.routing.items()
                                if (a, b) == (s, t)
                            )
                            expected_balance = (
                                demand if node == s else -demand if node == t else 0.0
                            )
                            self.assertAlmostEqual(balance, expected_balance, places=6)

    def test_invalid_parameters(self) -> None:
        for n, d in [(1, 1), (4, 0), (4, 4), (4.0, 2), (4, True)]:
            with self.subTest(n=n, d=d):
                with self.assertRaises(ValueError):
                    construct_optimal_uniform_topology(n, d)

    def test_cli_json(self) -> None:
        script = Path(__file__).with_name("uniform_topology.py")
        result = subprocess.run(
            [sys.executable, str(script), "2", "1"],
            capture_output=True,
            text=True,
            check=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(output["n"], 2)
        self.assertEqual(output["d"], 1)
        self.assertAlmostEqual(output["lambda"], 1.0)
        self.assertEqual(sorted(output["edges"]), [[0, 1], [1, 0]])
        self.assertEqual(len(output["routing"]), 2)

    def test_cli_invalid_parameters(self) -> None:
        script = Path(__file__).with_name("uniform_topology.py")
        result = subprocess.run(
            [sys.executable, str(script), "1", "1"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Require n >= 2", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
