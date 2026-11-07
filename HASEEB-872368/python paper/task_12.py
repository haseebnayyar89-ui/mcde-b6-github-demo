"""Task 12 | Custom Iterable Range Toolkit"""


class ReversibleRange:
    def __init__(self, start, stop, step=1):
        for value in (start, stop, step):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("start, stop and step must be integers")
        if step == 0:
            raise ValueError("step must not be zero")
        self.start = start
        self.stop = stop
        self.step = step

        # number of items, calculated with maths (no list is created)
        if step > 0:
            distance = stop - start
        else:
            distance = start - stop
        if distance <= 0:
            self.length = 0
        else:
            self.length = (distance - 1) // abs(step) + 1

    def __iter__(self):
        for i in range(self.length):
            yield self.start + i * self.step

    def __reversed__(self):
        for i in range(self.length - 1, -1, -1):
            yield self.start + i * self.step

    def __len__(self):
        return self.length

    def __contains__(self, value):
        if isinstance(value, bool) or not isinstance(value, int):
            return False
        difference = value - self.start
        if difference % self.step != 0:         # value does not fall on a step
            return False
        position = difference // self.step
        return 0 <= position < self.length


if __name__ == "__main__":
    r = ReversibleRange(2, 11, 3)
    print(list(r), list(reversed(r)), len(r), 5 in r, 6 in r)
    down = ReversibleRange(10, 0, -3)
    print(list(down), list(reversed(down)), len(down), 7 in down)
    print(list(ReversibleRange(5, 5)), len(ReversibleRange(5, 1)))
    try:
        ReversibleRange(1, 5, 0)
    except ValueError as error:
        print("Error:", error)
