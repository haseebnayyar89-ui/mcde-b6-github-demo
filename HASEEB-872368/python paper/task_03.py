"""Task 03 | Recursive JSON Path Explorer"""


def is_match(value, target):
    """Equal values, but True/False are never treated as 1/0."""
    if isinstance(value, bool) or isinstance(target, bool):
        return isinstance(value, bool) and isinstance(target, bool) and value == target
    return value == target


def find_paths(data, target):
    """Return all paths (like 'a[0].x') whose value equals target."""
    paths = []
    search(data, target, "", paths)
    return paths


def search(node, target, path, paths):
    if is_match(node, target):
        paths.append(path)

    if isinstance(node, dict):
        for key in node:
            new_path = path + "." + str(key) if path else str(key)
            search(node[key], target, new_path, paths)
    elif isinstance(node, list):
        for index in range(len(node)):
            search(node[index], target, path + "[" + str(index) + "]", paths)


if __name__ == "__main__":
    data = {"a": [{"x": 5}, 5], "b": {"y": 5}}
    print(find_paths(data, 5))                       # ['a[0].x', 'a[1]', 'b.y']
    print(find_paths({"flag": True, "n": 1}, 1))     # ['n']  (True is not 1)
    print(find_paths({"flag": True, "n": 1}, True))  # ['flag']
    print(find_paths({}, 5))                         # []
