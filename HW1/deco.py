#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper


def disable(fn):
    '''
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    >>> memo = disable

    '''
    return fn


def decorator(dec):
    '''
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    '''

    def wrapped(fn):
        return update_wrapper(dec(fn), fn)

    return update_wrapper(wrapped, dec)


@decorator
def countcalls(fn):
    '''Decorator that counts calls made to the function decorated.'''

    def count(*args, **kwargs):
        count.calls += 1
        return fn(*args, **kwargs)

    count.calls = 0
    return count


@decorator
def memo(fn):
    '''
    Memoize a function so that it caches all return values for
    faster future lookups.
    '''
    result = {}

    def helper(*args):
        update_wrapper(helper, fn)
        if args not in result:
            result[args] = fn(*args)
        return result[args]

    return helper


@decorator
def n_ary(f):
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''

    def helper(x, *args):
        return x if not args else f(x, helper(*args))

    return helper


def trace(fill_type):
    '''Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    '''

    @decorator
    def trace_decorator(f):
        def wrapper(n):
            print "{} --> {}({})".format(fill_type * wrapper.level, f.__name__, n)
            wrapper.level += 1
            result = f(n)
            print "{} <-- {}({}) == {}".format(fill_type * wrapper.level, f.__name__, n, result)
            wrapper.level -= 1
            return result

        wrapper.level = 0
        return wrapper

    return trace_decorator


@memo
@countcalls
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@trace("###")
@memo
def fib(n):
    """Computes and prints the first n Fibonacci numbers."""

    return 1 if n <= 1 else fib(n - 1) + fib(n - 2)


def main():
    print foo(4, 3)
    print foo(4, 3, 2)
    print foo(4, 3)
    print "foo was called", foo.calls, "times"

    print bar(4, 3)
    print bar(4, 3, 2)
    print bar(4, 3, 2, 1)
    print "bar was called", bar.calls, "times"

    print fib.__doc__
    fib(3)
    print fib.calls, 'calls made'


if __name__ == '__main__':
    main()
