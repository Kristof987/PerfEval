import random


def auto_assign_reviewers(member_ids: list[int], evaluations_per_employee: int) -> set[tuple[int, int]]:
    assignments: set[tuple[int, int]] = set()
    if evaluations_per_employee <= 0:
        return assignments

    out = {member_id: 0 for member_id in member_ids}
    pool = [evaluatee for evaluatee in member_ids for _ in range(evaluations_per_employee)]
    random.shuffle(pool)

    for evaluatee in pool:
        candidates = [
            evaluator
            for evaluator in member_ids
            if evaluator != evaluatee and (evaluator, evaluatee) not in assignments
        ]
        if not candidates:
            continue

        min_out = min(out[evaluator] for evaluator in candidates)
        best = [evaluator for evaluator in candidates if out[evaluator] == min_out]
        evaluator = random.choice(best)
        assignments.add((evaluator, evaluatee))
        out[evaluator] += 1

    return assignments
