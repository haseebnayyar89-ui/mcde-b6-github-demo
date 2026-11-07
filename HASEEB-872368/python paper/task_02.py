"""Task 02 | Longest Valid Window"""


def longest_unique_window(text):
    """Return (substring, start_index, length) of the longest window with no repeated character."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    last_seen = {}       # character -> last index where we saw it
    window_start = 0
    best_start = 0
    best_length = 0

    for index, char in enumerate(text):
        # if char is already inside the current window, move the window start after it
        if char in last_seen and last_seen[char] >= window_start:
            window_start = last_seen[char] + 1
        last_seen[char] = index

        length = index - window_start + 1
        if length > best_length:        # '>' (not '>=') keeps the earliest window
            best_length = length
            best_start = window_start

    return text[best_start:best_start + best_length], best_start, best_length


if __name__ == "__main__":
    for sample in ["abcabcbb", "", "bbbbb", "pwwkew", "a b!a b"]:
        print(repr(sample), "->", longest_unique_window(sample))
