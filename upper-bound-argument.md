# Part 1: Upper-Bound Argument for Uniform Traffic

This argument proves a limit on concurrent flow for every allowed topology.
It does not yet prove that our candidate ring topology is optimal.
All formulas below use plain text so they are readable without a math renderer.

## 1. Traffic and network capacity

Assume `1 <= d <= n - 1`. Each node has `d` outgoing links, each with capacity
1, so the network has `n*d` directed links and total link capacity `n*d`.

The uniform traffic matrix requests `d/(n - 1)` units for every ordered pair
of distinct nodes. At concurrent-flow scale `lambda`, we must carry:

```text
Traffic per pair = lambda * d/(n - 1)
```

There are `n*(n - 1)` ordered pairs. The pairs `A -> B` and `B -> A` count
separately.

## 2. Every route consumes capacity on each link it uses

Sending `x` units directly from `A` to `B` consumes `x` units of link capacity.
Sending the same amount along `A -> C -> B` consumes `x` units on each of two
links, or `2*x` units of total link capacity.

Splitting traffic among several paths does not remove this cost. If there is
no direct link, every path carrying that pair's traffic must use at least two
links. If a pair has no path at all, positive concurrent flow is impossible.

## 3. Count directly connected and non-direct pairs

Let `m` be the number of distinct ordered pairs with a direct link. Since
there are only `n*d` links:

```text
m <= n*d
```

The `m` direct pairs each require at least one link per unit of traffic.
The other `n*(n - 1) - m` pairs each require at least two.
Consequently, every feasible routing satisfies:

```text
Actual total link usage
>= lambda * d/(n - 1) * [m + 2*(n*(n - 1) - m)]

= lambda * d/(n - 1) * [2*n*(n - 1) - m]

>= lambda * d/(n - 1) * [2*n*(n - 1) - n*d]

= lambda * d/(n - 1) * n*[2*(n - 1) - d]
```

The last expression is a lower bound on usage, not necessarily the exact
usage. Longer routes or fewer distinct direct pairs can increase the cost.

## 4. Compare required usage with available capacity

No link may carry more than 1 unit. Summing the capacity constraints over all
links gives:

```text
Actual total link usage <= n*d
```

Combining this with the lower bound:

```text
lambda * d/(n - 1) * n*[2*(n - 1) - d] <= n*d
```

Divide by the positive quantity `n*d`:

```text
lambda * [2*(n - 1) - d]/(n - 1) <= 1
```

Therefore:

```text
lambda <= (n - 1) / [2*(n - 1) - d]
```

This is a topology-independent upper bound: it applies regardless of which
allowed links we choose or how we split traffic among routes.

## 5. Example: n = 7, d = 2

There are 42 ordered pairs and 14 links. At most 14 pairs are direct, so at
least 28 pairs require two or more links.

```text
Traffic per pair = lambda/3
Lower bound on usage = (lambda/3) * (14 + 2*28)
                     = (lambda/3) * 70

(lambda/3) * 70 <= 14
lambda <= 0.6
```

Thus no allowed topology for these values can carry more than 60% of every
pair's requested traffic simultaneously.

## 6. What remains to prove optimality

An upper bound is not automatically achievable. To establish optimality using
this bound, we must construct a topology and routing that:

1. Give every node exactly `d` incoming and `d` outgoing links.
2. Carry every pair's scaled demand at
   `lambda = (n - 1)/[2*(n - 1) - d]`.
3. Keep the total load on each individual link at most 1.

Meeting the bound would force direct pairs to use one-link routes and
non-direct pairs to use two-link routes, with every link fully utilized.
This is a strong requirement; it need not be possible.

For example, with `n = 7, d = 2`, a source can reach at most two distinct
destinations in one hop and at most four more in two hops. To reach all six
other nodes within two hops, all those destinations must be distinct.
But the candidate ring has two paths to the same destination:

```text
i -> i+1 -> i+3
i -> i+2 -> i+3
```

It also needs three hops to reach `i+5` and `i+6` (indices modulo 7).
Therefore, that ring cannot attain the 0.6 bound.

This does not by itself determine whether the ring is optimal at a smaller
value. We still need a matching construction and upper bound, or a different
valid comparison against all allowed topologies. The argument above is an
upper-bound section, not a complete answer to Part 1.
