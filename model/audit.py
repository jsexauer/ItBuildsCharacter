from pprint import pprint
from StringIO import StringIO

from attributes import Attributes


def get_displayworthy(k, v, fullTrace):
    # Skip any values not worth listing
    spacer = '  '
    not_modifiers = AuditResult._not_modifiers
    if not fullTrace:
        if type(v) is int and v == 0:
            return ''
        elif type(v) is list and v == []:
            return ''
        elif isinstance(v, AuditResult) and v.value == 0:
            return ''
        elif isinstance(v, AuditResult) and (
            v._name in ('_calcModChar', '_calcMod')):
            # No need to go down the rabbit hole on modifiers
            v = v.value

    s = spacer + k + ': '
    if isinstance(v, AuditResult):
        indent = len(s)
        s += '<' + v.show(fullTrace).replace('\n', '\n'+' '*indent)
        s = s.rstrip() + '>'
    elif type(v) is list:
        for i in v:
            s += '\n' + spacer*2 + str(i).replace('\n', '\n'+spacer*2)
        s = s.rstrip()
    elif (type(v) is int
          and k not in not_modifiers):
        s += '{0:+d}'.format(v)
    else:
        s += str(v)
    s += '\n'
    return s

class AuditResult(object):
    _display_order = (['base', 'BAB',] + Attributes._abilities
                      + [a+'_score' for a in Attributes._abilities]
                      + ['equipment','buffs']
                      + Attributes._scores)
    _sum_forumla_label = "Sum of"
    _not_modifiers = ('_calcAttrScore', 'AC', 'base')
    def __init__(self, formula, value, variables, name):
        if formula is None:
            self.formula = self._sum_forumla_label
        else:
            self.formula = formula
        self.value = value
        self.variables = variables.copy()
        self._name = name

        #assert self.formula_result == self.value

    @property
    def formula_result(self):
        """Result of variable using fomrula"""
        raise NotImplementedError("Need to figure out evaluate of formula")
        if self.formula == self._sum_forumla_label:
            return decomposed_sum(self.variables.values())
        else:
            try:
                env = self.variables.copy()
                env['sum'] = decomposed_sum
                env['max'] = decomposed_max
                return eval(self.formula, env)
            except:
                raise ValueError("Could not evaluate formula: " + self.formula)


    def show(self, fullTrace = True):
        variables = self.variables.copy()
        not_modifiers = AuditResult._not_modifiers

        s = self.formula + ':\n'
        # Grab keys in display order
        for k in self._display_order:
            v = variables.pop(k, None)
            if v is None:
                continue
            s += get_displayworthy(k, v, fullTrace)

        # Grab any remaining keys
        for k, v in variables.iteritems():
            s += get_displayworthy(k, v, fullTrace)

        # Print out result
        s = s.rstrip() + '\n'
        if (type(self.value) is int
            and self._name not in not_modifiers):
            s += '= {0:+d}'.format(self.value)
        elif type(self.value) is list:
            s += '= [\n   ' + ',\n   '.join(
                map(lambda x: str(x).replace('\n','\n   '), self.value))+ '\n  ]'
        else:
            s += '= %s' % self.value
        return s
    def __add__(self, other):
        return other + self.value
    def __radd__(self, other):
        return other + self.value
    def __sub__(self, other):
        return self.value - other
    def __rsub__(self, other):
        return other - self.value
    def __mul__(self, other):
        return other*self.value
    def __rmul__(self, other):
        return other*self.value
    def __div__(self, other):
        return self.value/other
    def __rdiv__(self, other):
        return other/self.value
    def __len__(self):
        return len(self.value)
    def __getitem__(self, key):
        return self.value[key]
    def __setitem__(self, value):
        raise AttributeError("can't set an attribute (or the audit of it)")
    def __str__(self):
        return self.show(False)
    def __repr__(self):
        return "<Audit of %s resulting in %s>" % (self._name, self.value)

