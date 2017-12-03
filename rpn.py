#!/usr/bin/env python
# -*- coding: utf-8 -*-

LEFT_ASSOC = 0
RIGHT_ASSOC = 1

OPERATORS = {
    "+": (0, LEFT_ASSOC),
    "-": (0, LEFT_ASSOC),
    "*": (5, LEFT_ASSOC),
    "/": (5, LEFT_ASSOC),
    "**": (20, RIGHT_ASSOC),
    "log": (6, LEFT_ASSOC),
    "ln": (6, LEFT_ASSOC),
    "Sum": (7, RIGHT_ASSOC)
}

IGNORE_TO_SPACE = [chr(x) for x in range(97, 123)]
IGNORE_TO_SPACE += [str(x) for x in range(0, 10)]
IGNORE_TO_SPACE.append(".")
IGNORE_TO_SPACE.remove("x")


def is_operator(token):
    return token in OPERATORS.keys()


def is_associative(token, assoc):
    if not is_operator(token):
        raise ValueError("Invalid token: %s" % token)

    return OPERATORS[token][1] == assoc


def cmp_precedence(token1, token2):
    if not is_operator(token1) or not is_operator(token2):
        raise ValueError("Invalid tokens: %s %s" % (token1, token2))

    return OPERATORS[token1][0] - OPERATORS[token2][0]


def splited_to_rpn(tokens):
    """
    Reverse Polish Notation.
    Source: http://andreinc.net/2010/10/05/converting-infix-to-rpn-shunting-yard-algorithm/
    FIXME: No funciona con sumatorias
    """

    out = []
    stack = []

    #For all the input tokens [S1] read the next token [S2]
    for token in tokens:
        if is_operator(token):
            # If token is an operator (x) [S3]
            while len(stack) > 0 and is_operator(stack[-1]):
                # [S4]
                if (is_associative(token, LEFT_ASSOC) and cmp_precedence(token, stack[-1]) <= 0) or \
                   (is_associative(token, RIGHT_ASSOC) and cmp_precedence(token, stack[-1]) < 0):

                    # [S5] [S6]
                    out.append(stack.pop())
                    continue

                break

            # [S7]
            stack.append(token)

        elif token == "(":
            stack.append(token) # [S8]

        elif token == ")":
            # [S9]
            while len(stack) > 0 and stack[-1] != "(":
                out.append(stack.pop()) # [S10]

            stack.pop() # [S11]

        else:
            out.append(token) # [S12]

    while len(stack) != 0:
        # [S13]
        s = stack.pop()
        out.append(s)

    return out


def split_expr(string):
    if type(string) != str:
        string = str(string)

    tokens = []
    obligatory = ["(", ")", ","]
    ignore = [" ", ","]

    for char in string:
        if char in ignore:
            if char in obligatory:
                tokens.append("")

            continue

        if tokens and len(tokens[-1]) >= 1:
            last_char = tokens[-1][-1]
        else:
            last_char = ""

        prev = ""

        if not tokens or char in obligatory:
            if last_char == "":
                tokens = tokens[:-1]

            tokens.append(char)
            continue

        if len(tokens) > 2:
            prev = tokens[-2]

        if last_char == "-" and not is_operator(char) and (is_operator(prev) or prev in obligatory):
            tokens[-1] = tokens[-1] + char

        elif last_char not in obligatory and is_operator(last_char) == is_operator(char):
            tokens[-1] = tokens[-1] + char

        else:
            tokens.append(char)


    return tokens


def expr_to_rpn(expr, blocks=False):
    splited = split_expr(expr)
    rpn = splited_to_rpn(splited)

    if blocks:
        # Solo para pruebas
        import math_view
        return math_view.parse_rpn(rpn)

    return rpn


if __name__ == "__main__":
    import sympy

    #expr = str(sympy.log(-3*sympy.E+15)*((x**2)-1)/(x+2))
    i = sympy.Symbol("i")
    x = sympy.Symbol("x")
    expr = sympy.Sum(x**2, (i, 0, sympy.oo))

    print expr
    print split_expr(str(expr))
    print splited_to_rpn(split_expr(str(expr)))
