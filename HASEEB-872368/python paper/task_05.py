"""Task 05 | Expression Validator and Evaluator (two stacks, no eval)"""


def evaluate_expression(expression):
    """Evaluate +, -, *, /, parentheses and unary minus. Returns a float."""
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")

    precedence = {"+": 1, "-": 1, "*": 2, "/": 2, "u": 3}   # "u" = unary minus
    numbers = []        # stack of numbers
    operators = []      # stack of operators

    def apply(op):
        if op == "u":
            if not numbers:
                raise ValueError("invalid expression")
            numbers.append(-numbers.pop())
            return
        if len(numbers) < 2:
            raise ValueError("invalid expression")
        right = numbers.pop()
        left = numbers.pop()
        if op == "+":
            numbers.append(left + right)
        elif op == "-":
            numbers.append(left - right)
        elif op == "*":
            numbers.append(left * right)
        else:
            if right == 0:
                raise ZeroDivisionError("division by zero")
            numbers.append(left / right)

    expect_number = True    # True when a number, "(" or unary sign must come next
    i = 0
    while i < len(expression):
        ch = expression[i]
        if ch.isspace():
            i += 1
            continue

        if ch in "0123456789":
            if not expect_number:
                raise ValueError("missing operator before number")
            start = i
            while i < len(expression) and expression[i] in "0123456789":
                i += 1
            numbers.append(float(expression[start:i]))
            expect_number = False
            continue

        if ch == "(":
            if not expect_number:
                raise ValueError("missing operator before '('")
            operators.append("(")
        elif ch == ")":
            if expect_number:
                raise ValueError("unexpected ')'")
            while operators and operators[-1] != "(":
                apply(operators.pop())
            if not operators:
                raise ValueError("unbalanced parentheses")
            operators.pop()                     # remove "("
        elif ch in "+-*/":
            if expect_number:                   # unary sign
                if ch == "-":
                    operators.append("u")
                elif ch != "+":
                    raise ValueError("operator '" + ch + "' has no left side")
            else:
                while operators and operators[-1] != "(" and precedence[operators[-1]] >= precedence[ch]:
                    apply(operators.pop())
                operators.append(ch)
                expect_number = True
        else:
            raise ValueError("invalid character: " + ch)
        i += 1

    if expect_number:
        raise ValueError("expression is empty or incomplete")
    while operators:
        op = operators.pop()
        if op == "(":
            raise ValueError("unbalanced parentheses")
        apply(op)
    return numbers[0]


if __name__ == "__main__":
    for text in ["-(3 + 2) * 4 + 18 / 3", "2 + 3 * 4", "(2 + 3) * 4", "2 * -3",
                 "8 / (4 - 4)", "2 +", "(1 + 2", "2 3", "abc", ""]:
        try:
            print(repr(text), "->", evaluate_expression(text))
        except (ValueError, ZeroDivisionError) as error:
            print(repr(text), "->", type(error).__name__ + ":", error)
