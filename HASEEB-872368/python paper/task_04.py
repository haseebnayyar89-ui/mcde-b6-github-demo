"""Task 04 | Dependency Execution Planner"""


def plan_execution(tasks, dependencies):
    """Return a valid execution order. Raises ValueError for unknown tasks or cycles."""
    if not isinstance(tasks, list):
        raise TypeError("tasks must be a list")
    if len(set(tasks)) != len(tasks):
        raise ValueError("duplicate task names")

    prerequisites = {}                  # task -> set of tasks that must finish first
    for name in tasks:
        prerequisites[name] = set()

    for pair in dependencies:
        if len(pair) != 2:
            raise ValueError("each dependency must be a pair (A, B)")
        before, after = pair
        if before not in prerequisites or after not in prerequisites:
            raise ValueError("unknown task name in dependency: " + str(pair))
        prerequisites[after].add(before)

    order = []
    remaining = list(tasks)
    while remaining:
        # tasks whose prerequisites are all finished, alphabetical order
        ready = sorted(t for t in remaining if all(p in order for p in prerequisites[t]))
        if not ready:
            raise ValueError("cycle detected among tasks: " + ", ".join(sorted(remaining)))
        chosen = ready[0]               # alphabetically first available task
        order.append(chosen)
        remaining.remove(chosen)
    return order


if __name__ == "__main__":
    print(plan_execution(["build", "test", "deploy"], [("build", "test"), ("test", "deploy")]))
    print(plan_execution(["c", "b", "a"], []))
    for tasks, deps in [(["a", "b"], [("a", "b"), ("b", "a")]), (["a"], [("a", "z")])]:
        try:
            plan_execution(tasks, deps)
        except ValueError as error:
            print("Error:", error)
