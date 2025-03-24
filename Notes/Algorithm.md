outer_model = GaussianProcess()
inner_model = GaussianProcess()

outer_data = []
inner_data = []

A_current, B_current = initialize()
f_initial = evaluate(A_current, B_current)
outer_data.append((A_current, f_initial))
inner_data.append((A_current, B_current, f_initial))

for outer_iter in range(max_outer_iters):
    A_candidates = generate_A_candidates()
    A_next = select_A_via_EI(outer_model, A_candidates)
    B_current = initialize_B()
    best_f_inner = -inf
    for inner_iter in range(max_inner_iters):
        B_candidates = generate_B_candidates(A_next)
        B_next = select_B_via_EI(inner_model, B_candidates, fixed_A=A_next)
        f_val = evaluate(A_next, B_next)
        inner_data.append((A_next, B_next, f_val))
        inner_model.update(inner_data)
        if f_val > best_f_inner:
            best_f_inner = f_val
    outer_data.append((A_next, best_f_inner))
    outer_model.update(outer_data)**Algo Objectives**
1. Integrate the collected **performance** and **preference** (Ranking) metrics to prepare optimization data for the Bayesian optimizer.
2. Build proper kenels for the Bayesian optimizer.
3. Design a workflow for Designer in the loop model.

