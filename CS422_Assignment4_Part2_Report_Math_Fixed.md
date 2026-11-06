# Assignment 4 — Part 2: Arbitrary Traffic Matrix

## 1. Problem and approach

We are given a directed network with **8 nodes**. Each node must have **exactly 4 outgoing links and 4 incoming links**, and each link has capacity **1**. The input is an arbitrary traffic matrix $D$, where $D_{st}$ is the amount of traffic node $s$ wants to send to node $t$. The matrix belongs to the hose-model traffic set:

$$
D_{st}\ge 0,\qquad D_{ss}=0,\qquad
\sum_t D_{st}\le 4,\qquad \sum_s D_{st}\le 4.
$$

Unlike uniform traffic, demands can be different for different pairs, so the best connections may change with $D$. Our goal is to **choose the topology and route the traffic at the same time**, maximizing the *concurrent-flow multiplier* $\lambda$. For every pair $(s,t)$, the network must deliver $\lambda D_{st}$ units simultaneously. For example, when $D_{04}=4$ and $\lambda=0.75$, the routing must deliver 3 units from node 0 to node 4.

We formulate this as a **mixed-integer linear program (MILP)** and solve it using Gurobi.

## 2. Decision variables

Let $V=\{0,1,\ldots,7\}$, $A=\{(u,v):u,v\in V,\ u\ne v\}$, and $K=\{(s,t):D_{st}>0\}$.

- **Topology:** $x_{uv}\in\{0,1\}$. It equals 1 if the directed link $u\to v$ is built, and 0 otherwise.
- **Routing:** $f_{uv}^{st}\ge0$. It is the amount of the traffic **from source $s$ to destination $t$** that uses the link $u\to v$. A demand may be split across multiple paths.
- **Concurrent flow:** $\lambda\ge0$. This is the common multiplier applied to all demands.

For example, $f_{02}^{04}=0.5$ means that 0.5 units of traffic destined from **node 0 to node 4** travel over the **link 0 → 2**. These indices let the model track each demand separately even when multiple demands share a link.

## 3. Objective and constraints

**Objective:** maximize the amount of every demand that can be carried together:

$$
\boxed{\max\ \lambda}
$$

### A. Degree constraints

Each node must have exactly 4 outgoing and 4 incoming links:

$$
\boxed{\sum_{v\ne u}x_{uv}=4,\qquad \sum_{v\ne u}x_{vu}=4\qquad\forall u\in V.}
$$

For instance, if $x_{01}=x_{02}=x_{04}=x_{05}=1$, then node 0 has its required four outgoing links. Across the whole network there are $8\times4=32$ directed links.

### B. Link-capacity constraints

The sum of **all demands using the same link** must fit within its capacity:

$$
\boxed{\sum_{(s,t)\in K}f_{uv}^{st}\le x_{uv}\qquad\forall(u,v)\in A.}
$$

If $x_{uv}=0$, the right-hand side is 0, so no traffic can use a link that does not exist. If $x_{uv}=1$, the total load cannot exceed 1. For example, two demands can share one link with loads 0.6 and 0.4, but not 0.6 and 0.7.

### C. Flow-conservation constraints

For each positive-demand pair $(s,t)$, at every node $u$:

$$
\boxed{
\sum_{v\ne u}f_{uv}^{st}-\sum_{v\ne u}f_{vu}^{st}
=\begin{cases}
\lambda D_{st},&u=s,\\
-\lambda D_{st},&u=t,\\
0,&u\ne s,t.
\end{cases}
}
$$

This ensures the correct amount arrives at its destination:

- At the **source**, net outgoing traffic equals the scaled demand.
- At the **destination**, net incoming traffic equals the scaled demand.
- At an **intermediate node**, incoming and outgoing traffic are equal.

For example, if 1 unit of the 0 → 4 demand travels along **0 → 2 → 4**, then that unit appears on both links, and node 2 receives and forwards the same 1 unit.

These equations, together with $x_{uv}\in\{0,1\}$, $f_{uv}^{st}\ge0$, and $\lambda\ge0$, form the complete MILP.

## 4. Intuition and Optimality of the Formulation

We **do not give Gurobi a network with links already chosen**. We give it the traffic matrix and the rules from Section 3, and ask it to find the best network.

Gurobi decides three things together:

1. **Which links exist (`x`).** For example, setting $x_{02}=1$ builds the link **0 → 2**, while $x_{03}=0$ means **0 → 3** is not built.
2. **How traffic travels (`f`).** For example, traffic from node 0 to node 4 might travel along **0 → 2 → 4**. The model records how much of that demand uses each link. It can split a demand across multiple paths.
3. **How much demand can be delivered (`\lambda`).** Gurobi tries to make $\lambda$ as large as possible without violating any of the rules.

For every choice, the model checks that each node has four links in and out, no link carries more than one unit, and all scaled demands reach their destinations. **The final topology is the list of links where $x_{uv}=1$.** We can also read $f$ to see how traffic is routed and $\lambda$ to see the achieved concurrent flow.

To keep the model smaller, we only track routing for pairs that actually request traffic ($D_{st}>0$). If all demands are zero, there is no meaningful finite maximum for $\lambda$, so that case is handled separately.

## 5. Why the answer is optimal

The program is not limited to a ring, chordal ring, or any other predefined graph. **It is allowed to choose any directed topology that satisfies the four-incoming/four-outgoing rule**, with at most one link per ordered pair.

For each possible topology, the model also allows any routing that obeys flow conservation and link capacities. This means that a better topology, if one existed, would also be a possible solution to the same optimization problem.

Suppose Gurobi reports that its solution is **optimal**, with value $\lambda^*$. If another allowed network could carry a larger multiplier, that network and its routing would satisfy our constraints and give Gurobi a better feasible answer. This would contradict the optimal result. Therefore, the returned topology maximizes concurrent flow **for the given input matrix**.

This guarantee requires Gurobi to finish and report an *optimal* solution. Finding a valid topology without proving optimality is not enough.

## 6. Sample result and verification

The provided sample includes demands $D_{04}=4$, $D_{15}=3$, $D_{26}=2$, and $D_{37}=1$, with additional demands in the reverse direction. The accompanying implementation reports:

- **Optimal concurrent flow:** $\lambda=1$
- **Selected directed links:** 32
- **Maximum link load:** 1

We can independently establish an upper bound for this example. Node 0 requests 4 units of outgoing traffic, but it has only four outgoing links, each of capacity 1. Therefore:

$$
4\lambda\le4\quad\Rightarrow\quad \lambda\le1.
$$

The reported feasible solution reaches $\lambda=1$, so it matches the upper bound and is optimal **for this sample**. The same MILP formulation works for any nonzero traffic matrix satisfying the hose-model conditions.

**Implementation:** [Insert GitHub/GitLab repository link to the Gurobi Python code and relevant lines.]

*Modeling assumption:* This formulation permits **at most one directed link per ordered pair**, since $x_{uv}$ is binary. If parallel links are allowed, the model must use integer link-count variables instead.
