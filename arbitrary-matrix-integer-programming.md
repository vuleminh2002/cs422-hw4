# Arbitrary Traffic Matrix: Integer Programming Formulation

## Problem setup

There are `n` nodes. The traffic matrix `D` gives the requested traffic for
each ordered source-destination pair:

```text
D[i][j] = requested traffic from node i to node j
D[i][i] = 0
```

The demands can be different in each direction. For example, `D[0][1]` need
not equal `D[1][0]`.

The goal is to maximize `lambda`, the common fraction of every demand that
the network can carry. Thus, for each pair `(s, t)`, the network must route:

```text
lambda * D[s][t]
```

Assume the network is directed, links have capacity 1, and each node must
have exactly `d` incoming and `d` outgoing links, as in the uniform-topology
model. The formulation below chooses both the links and the routes.
Assume `D[i][j] >= 0`, capacities are nonnegative, and `1 <= d <= n - 1`.

For the assignment's fixed case, set:

```text
n = 8
d = 4
link capacity = 1
nodes = {0, 1, 2, 3, 4, 5, 6, 7}
```

The implementation for this case is in
[arbitrary_matrix_topology.py](./arbitrary_matrix_topology.py).

## Decision variables

For every possible directed link `u -> v`, with `u != v`:

```text
x[u][v] = 1 if the link u -> v is built; 0 otherwise
```

For each positive-demand pair `(s, t)` and possible link `u -> v`:

```text
f[s][t][u][v] >= 0
    amount of the s-to-t demand routed over link u -> v
```

And:

```text
lambda >= 0
    fraction of every demand that is carried
```

The topology variables `x` are binary. The routing amounts and `lambda` are
continuous: traffic is divisible and can be split among multiple paths.
Therefore this is a **mixed-integer linear program (MILP)**, not a model that
requires every flow amount to be an integer.

Only pairs with `D[s][t] > 0` need flow variables and flow-conservation
constraints. This avoids unnecessary variables for zero-demand pairs.

## Objective

Maximize the common demand fraction:

```text
maximize lambda
```

## Constraints

### 1. Degree constraints

Each node has exactly `d` outgoing and `d` incoming links:

```text
For every node u:
    sum of x[u][v] over all v != u = d
    sum of x[v][u] over all v != u = d
```

These constraints also imply that the network has exactly `n * d` directed
links.

### 2. Link capacities

The total flow from all source-destination pairs on a link cannot exceed its
capacity. A flow can use a link only if that link is built:

```text
For every possible directed link u -> v:
    sum of f[s][t][u][v] over all positive-demand pairs (s, t)
        <= capacity[u][v] * x[u][v]
```

For unit-capacity links, set `capacity[u][v] = 1`, giving:

```text
sum of f[s][t][u][v] over all pairs (s, t) <= x[u][v]
```

If `x[u][v] = 0`, this forces all flow on that link to zero. If it is 1,
the total flow is limited by the link capacity.

### 3. Flow conservation for every demand

For each positive-demand pair `(s, t)`, conserve that commodity's flow at
every node. At its source, net outgoing flow equals its scaled demand; at
its destination, net incoming flow equals that demand; at intermediate
nodes, incoming and outgoing flow balance.

```text
For every positive-demand pair (s, t):

    At node s:
        outgoing flow for (s, t) - incoming flow for (s, t)
            = lambda * D[s][t]

    At node t:
        outgoing flow for (s, t) - incoming flow for (s, t)
            = -lambda * D[s][t]

    At every other node u:
        outgoing flow for (s, t) - incoming flow for (s, t)
            = 0
```

In indexed form, for every node `u`:

```text
sum of f[s][t][u][v] over all v != u
    - sum of f[s][t][v][u] over all v != u
    =
        lambda * D[s][t]    if u = s
       -lambda * D[s][t]    if u = t
        0                   otherwise
```

The right-hand side is linear because `D[s][t]` is input data, not a decision
variable. Thus `lambda * D[s][t]` is a constant multiple of a variable.

### 4. Variable domains

```text
x[u][v] is binary
f[s][t][u][v] >= 0
lambda >= 0
```

No self-links are included: only pairs `u != v` are considered.

## Complete model in compact form

Let `A` be the set of possible directed links, containing every `(u, v)`
with `u != v`. Let `K` contain all pairs `(s, t)` for which `D[s][t] > 0`.
Let `c[u][v]` be the capacity of link `(u, v)`.

```text
maximize    lambda

subject to  sum over v != u of x[u][v] = d                  for every u
            sum over v != u of x[v][u] = d                  for every u

            sum over (s,t) in K of f[s][t][u][v]
                <= c[u][v] * x[u][v]                        for every (u,v) in A

            sum over v != u of f[s][t][u][v]
              - sum over v != u of f[s][t][v][u]
                = lambda * D[s][t]                           for (s,t) in K, u = s

            sum over v != u of f[s][t][u][v]
              - sum over v != u of f[s][t][v][u]
                = -lambda * D[s][t]                          for (s,t) in K, u = t

            sum over v != u of f[s][t][u][v]
              - sum over v != u of f[s][t][v][u]
                = 0                                          for (s,t) in K, u != s,t

            x[u][v] in {0, 1}
            f[s][t][u][v] >= 0
            lambda >= 0
```

The right-hand side of the capacity constraint can use an arbitrary
capacity `c[u][v]`. For unit-capacity links, use `c[u][v] = 1`.

## If the topology is already fixed

If links are given rather than chosen, remove the binary variables. Set
`x[u][v]` to 1 for an existing link and 0 otherwise, and omit the degree
constraints if they are already guaranteed by the input topology.

The remaining model has only continuous variables and is a **linear
program (LP)**. It finds the maximum concurrent-flow scale for that fixed
network.

## Solving and interpreting the result

1. Provide the demand matrix `D`, link capacities, and (for topology design)
   the required degree `d`.
2. Build the variables and constraints above in a MILP solver such as Gurobi,
   CPLEX, or SCIP.
3. Maximize `lambda`.
4. Read the selected links from the binary `x` variables and the routes from
   the positive `f` variables.

If the solver returns `lambda = 0.6`, the selected network and routing can
carry 60% of every requested source-destination demand simultaneously. For
example, a demand of 10 units is carried at 6 units, while a demand of 2
units is carried at 1.2 units.

If `D` contains at least one positive entry and the network has finite total
capacity, `lambda` is bounded: every unit of routed demand uses at least one
unit of link capacity. If every entry of `D` is zero, the objective is
unbounded unless an upper bound is added; in that degenerate case, define the
answer separately rather than solving this model.

## Important modeling notes

- The formulation allows traffic for a pair to split over multiple paths.
- Flow conservation plus nonnegative link flows represents path routing. Any
  cycles in a solution can be removed without reducing delivered flow or
  increasing capacity use.
- If links are undirected, change the link set and capacity accounting to
  match the problem's undirected-link rules; do not model one undirected link
  as two independent unit-capacity directed links unless that is intended.
- A MILP solver may prove global optimality slowly as `n` grows. A feasible
  result is not a proof of optimality unless the solver reports an optimal
  status (or a sufficiently tight bound/gap for the intended use).
- This optimizes topology and routing together. If the assignment instead
  gives a fixed topology, use the LP version above.

## Relation to the existing uniform-traffic model

For uniform traffic, the demand entries are all `d / (n - 1)` off the
diagonal. For arbitrary traffic, replace that formula with the actual input
value `D[s][t]` for each pair. The variables, capacity constraints, and flow
conservation structure stay the same; only the right-hand-side demands
change.

## Gurobi implementation and sample check

The code fixes `n = 8` and `d = 4`, but accepts a different 8-by-8 demand
matrix each time it runs. The binary variables select the 32 directed links;
the continuous flow variables route the positive-demand commodities. The
scale variable is maximized.

The built-in sample is an asymmetric traffic matrix:

```text
        destination
          0  1  2  3  4  5  6  7
source 0  0  0  0  0  4  0  0  0
       1  0  0  0  0  0  3  0  0
       2  0  0  0  0  0  0  2  0
       3  0  0  0  0  0  0  0  1
       4  1  0  0  0  0  0  0  0
       5  0  2  0  0  0  0  0  0
       6  0  0  1  0  0  0  0  0
       7  0  0  0  1  0  0  0  0
```

Install the Gurobi Python package if needed, then run:

```text
python3 -m pip install gurobipy
python3 arbitrary_matrix_topology.py
```

Gurobi must also have a usable license. The program prints the optimal
`lambda`, selected links, per-link loads, and nonzero commodity/link flows.
To solve a different matrix, save an 8-by-8 JSON array and pass its path:

```text
python3 arbitrary_matrix_topology.py --demand-file demands.json
```

For the sample matrix, Gurobi returned:

```text
lambda = 1.0
directed links selected = 32
maximum link load = 1.0
```

This value is optimal, not merely feasible. Node 0 has 4 units of outgoing
demand and exactly 4 outgoing links of capacity 1 each. Therefore, its
outgoing capacity implies `lambda <= 4 / 4 = 1`. The returned routing
achieves `lambda = 1` while respecting all link capacities, so the upper
bound is met.

One optimal link set returned by the solver was:

```text
0 -> {1, 2, 4, 5}
1 -> {2, 4, 5, 7}
2 -> {3, 4, 5, 7}
3 -> {0, 2, 6, 7}
4 -> {0, 1, 3, 6}
5 -> {0, 1, 6, 7}
6 -> {0, 1, 2, 3}
7 -> {3, 4, 5, 6}
```

The optimizer may return a different link set with the same optimal scale.
The test in [test_arbitrary_matrix_topology.py](./test_arbitrary_matrix_topology.py)
checks degree constraints, link capacities, per-commodity flow conservation,
input validation, and the sample optimum. Run it with:

```text
python3 -m unittest -v test_arbitrary_matrix_topology.py
```
