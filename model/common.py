import random, itertools, sys
random.seed()

class Struct(object):
    def __getitem__(self, key):
        return getattr(self, key)
    def __setitem__(self, key, value):
        setattr(self, key, value)

def intOrNone(x):
    return None if x is None or x == '' else int(x)
def intOrZero(x):
    return 0 if x is None or x == '' else int(x)


def roll_d(dice):
    """Roll a dXX dice"""
    return random.randrange(1,dice+1,1)


def decompose(a):
    return itertools.chain.from_iterable(
                map(lambda i: i if type(i) == list else [i], a))
def decomposed_sum(*args):
    base = []
    for x in args:
        base.extend(decompose(x))
    return sum(base)
def decomposed_max(*args):
    base = [0,]
    for x in args:
        base.extend(decompose(x))
    return max(base)


def has_sum(list, key):
    """Returns objects with key and the sum of those keyed values"""
    return ( filter(lambda x: x[key]!=0, list),
             sum(map(lambda x: x[key], list)) )

def has_max(list, key):
    """Returns objects with key and the max of those keyed values
       (used for buffs that do not stack"""
    return ( filter(lambda x: x[key]!=0, list),
             max(map(lambda x: x[key], list) + [0,]) )

class auditable(object):
    """
    An auditable property.  You should define _formula property in your function
    if not just summing everything together.
    http://stackoverflow.com/questions/9186395/python-is-there-a-way-to-get-a-local-function-variable-from-within-a-decorator
    http://code.activestate.com/recipes/577283-decorator-to-expose-local-variables-of-a-function-/
    http://stackoverflow.com/questions/4357851/creating-or-assigning-variables-from-a-dictionary-in-python

    """
    def __init__(self, func):
        self._func = func

    def auditableFuncFactory(self, child_self, cls, *args, **kwargs):
        func = self._func

        if not hasattr(child_self, 'audit'):
            raise ValueError("auditble wrapper must be on auditable object")

        class Tracer(object):
            def __init__(self):
                self.locals = {}
            def __call__(self, frame, event, arg):
                if event=='return':
                    self.locals = frame.f_locals.copy()

        if child_self.audit:
            # tracer is activated on next call, return or exception
            tracer = Tracer()
            old_profiler =  sys.getprofile()
            sys.setprofile(tracer)
            try:
                # trace the function call
                res = func(child_self, *args, **kwargs)
            finally:
                # disable tracer and replace with old one
                sys.setprofile(old_profiler)

            # Filter out variables we don't want (marked with _)
            v = tracer.locals
            v.pop('self', None)
            formula = None
            for k in v.keys():
                if k == '_formula':
                    formula = v[k]
                if k[0] == '_':
                    v.pop(k, None)
            return AuditResult(formula, res, v, func.func_name)
        else:
            return func(child_self, *args, **kwargs)

    def auditableSetter(self, child_self, newFuncFact):
        assert (isinstance(newFuncFact, auditable),
                "cannot set auditable properties")
        self._func = newFuncFact._func

    __get__ = auditableFuncFactory
    __set__ = auditableSetter

    #return_func = property(auditableFuncFactory, auditableSetter)

    #return return_func

from audit import AuditResult