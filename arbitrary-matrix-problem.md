# Arbitrary Traffic Matrix Problem

## What is an arbitrary traffic matrix?

A traffic matrix specifies how much traffic each source node wants to send to
each destination node. Unlike **uniform traffic**, the demands do not have to
be equal.

Let `D[i][j]` mean the amount of traffic requested from node `i` to node `j`.
For example:

```text
        destination
          0   1   2
source 0  0   8   1
       1  2   0   0
       2  0   3   0
```

Here, node 0 requests 8 units to node 1 and 1 unit to node 2; node 2 requests
3 units to node 1. The diagonal is zero because a node does not send traffic
to itself. Demands can be asymmetric: `D[0][1]` need not equal `D[1][0]`.

## What are we trying to maximize?

Choose routes for the demands so that the same fraction of every demand can
be carried. Call that fraction `lambda`.

```text
Traffic to route from i to j = lambda * D[i][j]
```

For example, if `lambda = 0.5`, the network must carry half of every
source-destination demand. In the example above, that means routing 4 units
from node 0 to node 1, 0.5 units from node 0 to node 2, and 1.5 units from
node 2 to node 1.

The goal is to make `lambda` as large as possible without exceeding any link's
capacity.

## How do routes use capacity?

Each directed link has a capacity. Traffic consumes capacity on **every**
link along its route. Thus, routing 2 units along a two-link path uses 2 units
of capacity on each of those links.

Traffic for one source-destination pair may be split across multiple paths.
For example, 4 units from node 0 to node 1 could be routed as 2 units on one
path and 2 units on another, as long as every link's capacity limit is
respected.

For each link:

```text
total traffic using the link <= capacity of the link
```

If a positive-demand pair has no path from its source to its destination,
then no positive value of `lambda` is feasible.

## A useful upper bound from a cut

Take any set of nodes `S`. A demand is **leaving S** if its source is in `S`
and its destination is outside `S`. Every route carrying such traffic must
cross a directed link that leaves `S`.

Therefore:

```text
lambda * (sum of D[i][j] for every i in S and every j outside S)
    <= sum of capacities of all directed links from S to outside S
```

In words:

> The scaled demand leaving a group of nodes cannot exceed the capacity of
> the links leaving that group.

This inequality gives an upper bound on `lambda` for each choice of `S`.
The tightest such bound is the smallest of those upper bounds.

### Example

Suppose the demand leaving some set `S` totals 12 units, and the links leaving
`S` have 6 units of capacity in total. Then:

```text
lambda * 12 <= 6
lambda <= 6 / 12
lambda <= 0.5
```

So the network cannot carry more than half of every demand, regardless of
how the traffic is routed.

Cut inequalities are useful necessary conditions: if one is violated,
routing is impossible. By themselves, they do not always prove that a
routing achieving the bound exists.

## What is being chosen?

There are two versions of the problem:

1. **Fixed topology:** The links are already given. Choose routes to maximize
   `lambda`.
2. **Topology design:** Choose the links as well as the routes, subject to
   the network's rules, such as a fixed number of incoming and outgoing
   links per node.

In either version, the objective is to maximize `lambda`; the difference is
whether the network itself is part of the decision.

## How this relates to uniform traffic

Uniform traffic is a special case of an arbitrary traffic matrix. If there
are `n` nodes and every node sends a total of `d` units evenly to the other
`n - 1` nodes, then:

```text
D[i][j] = d / (n - 1)    when i != j
D[i][i] = 0
```

An arbitrary matrix removes that equal-demand assumption. Some pairs may have
large demands, some may have small demands, and some may have zero demand.
Consequently, arguments that rely on all pairs carrying the same amount
usually apply only to the uniform case.
