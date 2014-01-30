
import random, sys
from pprint import pprint
from StringIO import StringIO
random.seed()

intOrNone = lambda x: None if x is None or x == '' else int(x)
intOrZero = lambda x: 0 if x is None or x == '' else int(x)

class Struct(object):
    def __getitem__(self, key):
        return getattr(self, key)
    def __setitem__(self, key, value):
        setattr(self, key, value)

class Buff(Struct):
    _last_id = -1
    def __init__(self, name, atk_mod=0, dmg_mod=0):
        self.name = name
        # Modifiers
        self.atk = intOrZero(atk_mod)
        if type(dmg_mod) is int:
            self.dmg_roll = DamageRoll(None, None, dmg_mod)
        elif isinstance(dmg_mod, DamageRoll):
            self.dmg_roll = dmg_mod
        elif isinstance(dmg_mod, basestring):
            self.dmg_roll = DamageRoll(None, None, intOrZero(dmg_mod))
        else:
            raise ValueError("Unrecognized damage modifier %s" % dmg_mod)
        # UI Details
        Buff._last_id += 1
        self.id = self._last_id
        self.ui_id = ''


    @classmethod
    def fromDict(cls, d):
        """Create a Buff from a dictionary (JSON) object"""
        buff = Buff(d['name'], atk_mod=d['atk'],
                    dmg_mod=DamageRoll.fromString(d['dmg_roll']))
        buff.id = d['id']
        Buff._last_id = max(Buff._last_id, buff.id)
        return buff


    def makeUI(self, id):
        id = "Buff" + str(id)
        template = """
        <CheckBox
            android:id="@+id/%(id)s"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="%(name)s" />
        """
        self.ui_id = id
        return template % {'id': id, 'name': self.name}
    def makeDict(self):
        return dict(id=self.id, name=self.name, dmg_roll=str(self.dmg_roll),
                atk=self.atk)
    def __str__(self):
        return self.name
    def __repr__(self):
        return "<'%s' at %s>"%(self.name, hex(id(self)))



class Attack(object):
    _last_id = 0
    def __init__(self, name, atk, dmg_roll, crit_range, crit_mult):
        self.name = name
        self.base = Struct()
        self.base.atk = atk
        self.base.dmg_roll = dmg_roll
        self.base.crit_range = crit_range
        self.base.crit_mult = crit_mult
        self.buffs = []
        # UI Details
        self.id = self._last_id
        self.ui_id = ''
        Attack._last_id += 1

    @property
    def atk(self):
        return self._getprop('atk')
    @property
    def dmg_roll(self):
        return self._getprop('dmg_roll')
    @property
    def crit_range(self):
        # Don't support buffs that mess with crits yet
        return self.base.crit_range
    @property
    def crit_mult(self):
        # Don't support buffs that mess with crits yet
        return self.base.crit_mult

    def _getprop(self, prop):
        """Return property like attack, dmg, etc but adding base"""
        adders = 0
        for b in self.buffs:
            adders = b[prop] + adders
        return self.base[prop] + adders

    def roll(self):
        s = ''
        atk_roll = roll_d(20)
        dmg = self.dmg_roll.roll()
        if atk_roll in self.crit_range:
            # We threat
            if atk_roll == 20:
                s += "Natural <20>\n"
            else:
                s += "Thretan with a <%d> (%d to  hit)\n" % \
                      (atk_roll, atk_roll+self.atk)
            # Roll to confirm
            conf_roll = roll_d(20) + self.atk
            crit_dmg = dmg + sum([self.dmg_roll.roll()
                                  for n in range(self.crit_mult-1)])
            s += "If a %d confirms, %d damage." % (conf_roll, crit_dmg)
            s += "            Else: %d damage" % dmg
        else:
            s += "Rolled a <%d>.\n%d to hit for %d damage.\n" % \
                  (atk_roll, atk_roll+self.atk, dmg)
        return s

    def makeUI(self, id=None):
        assert id is None or id == self.id # Old feature no longer needed
        id = "Atk"+str(id)
        template = """
        <TableRow
            android:id="@+id/tableRow_%(id)s"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:gravity="center" >

            <TextView
                android:id="@+id/%(id)s_Name"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_weight="0"
                android:text="%(name)s" />

            <TextView
                android:id="@+id/%(id)s_Atk"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_weight="0"
                android:layout_marginRight="15dp"
                android:text="+%(atk)s" />

            <TextView
                android:id="@+id/%(id)s_Dmg"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_weight="0"
                android:layout_marginRight="15dp"
                android:text="%(dmg)s" />

            <Button
                android:id="@+id/RollBtn%(id)s"
                style="?android:attr/buttonStyleSmall"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_weight="0"
                android:text="Roll" />

        </TableRow>
        """
        self.ui_id = id
        return template % {'id': id, 'name': self.name,
                            'atk':self.atk, 'dmg':self.dmg_roll}
    def updateUI(self, buffs, droid):
        self.buffs = buffs
        droid.fullSetProperty(self.ui_id+'_Atk',"text","+"+str(self.atk))
        droid.fullSetProperty(self.ui_id+'_Dmg',"text",str(self.dmg_roll))




class DamageRoll(Struct):
    def __init__(self, dmg_numDice, dmg_dice, dmg_add):
        self.numDice = intOrNone(dmg_numDice)
        self.dice = intOrNone(dmg_dice)
        self.add = intOrZero(dmg_add)
        super(DamageRoll, self).__init__()
    @classmethod
    def fromString(self, s):
        """Build a damage roll from string (like "1d4+5" or "+7")"""
        s = s.replace(' ','').lower()
        if s.find('+') != -1:
            # 1d4+3 or +2
            dice, adder = s.split('+')
            adder = int(adder)
        elif s.find('-') != -1:
            # 1d4-1 or -2
            dice, adder = s.split('-')
            adder = -int(adder)
        else:
            #1d4
            dice = s
            adder = 0
        if dice == '':
            # +2 or -2
            return DamageRoll(None, None, adder)
        else:
            numDice, dice = dice.split('d')
            return DamageRoll(numDice, dice, adder)


    def roll(self):
        roll = self.add
        for n in range(self.numDice):
            roll += roll_d(self.dice)
        return roll
    def __str__(self):
        if self.numDice is None and self.dice is None:
            if self.add < 0:
                return "%d" % self.add
            else:
                return "+%d" % self.add
        return "%dd%d+%d" % (self.numDice, self.dice, self.add)
    def __add__(self, other):
        if isinstance(other, DamageRoll):
            # Add two damage rolls
            if other.numDice is not None:
                raise NotImplementedError()
            if other.dice is not None:
                raise NotImplementedError()
            return DamageRoll(self.numDice, self.dice, self.add+other.add)
        elif type(other) is int:
            return DamageRoll(self.numDice, self.dice, self.add+other)
        else:
            raise ValueError("Cannot add %s to %s" % (other, self))

def roll_d(dice):
    """Roll a dXX dice"""
    return random.randrange(1,dice+1,1)




#########################################################################


def auditable(func):
    """
    An auditable property.  You should define _formula property in your function
    if not just summing everything together.
    http://stackoverflow.com/questions/9186395/python-is-there-a-way-to-get-a-local-function-variable-from-within-a-decorator
    http://code.activestate.com/recipes/577283-decorator-to-expose-local-variables-of-a-function-/
    http://stackoverflow.com/questions/4357851/creating-or-assigning-variables-from-a-dictionary-in-python

    """
    def auditableFuncFactory(child_self, *args, **kwargs):
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
            v.pop('self')
            formula = None
            for k in v.keys():
                if k == '_formula':
                    formula = v[k]
                if k[0] == '_':
                    v.pop(k)
            return AuditResult(formula, res, v, func.func_name)
        else:
            return func(child_self, *args, **kwargs)
    return property(auditableFuncFactory)


def has_sum(list, key):
    """Returns objects with key and the sum of those keyed values"""
    return ( filter(lambda x: x[key]!=0, list),
             sum(map(lambda x: x[key], list)) )

def has_max(list, key):
    """Returns objects with key and the max of those keyed values
       (used for buffs that do not stack"""
    return ( filter(lambda x: x[key]!=0, list),
             max(map(lambda x: x[key], list) + [0,]) )

def _makeMod(_attr):
    def _calcMod(self):
        _formula = '(score-10)/2 where'
        score = self[_attr+'_score']
        return (score - 10) // 2
    return _calcMod

def _makeScore(_attr):
    _attr_score = _attr+'_score'
    def _calcAttrScore(self):
        base = self.base[_attr_score]
        racial = self.race[_attr_score]
        buffs, _buffs = has_sum(self.buffs, _attr_score)
        equipment, _eqp = has_sum(self.equipment, _attr_score)
        return (base+ racial + _buffs + _eqp)
    return _calcAttrScore


class AttributesMeta(type):
    def __new__(cls, name, bases, attrdict):
        _abilities = attrdict.get('_abilities', {})
        for k in _abilities:
            attrdict[k] = auditable(_makeMod(k))

        _scores = attrdict.get('_scores', {})
        for k in _scores:
            attrdict[k] = 0
        return super(AttributesMeta, cls).__new__(cls, name, bases, attrdict)

class Attributes(Struct):
    __metaclass__ = AttributesMeta
    _abilities = ['str', 'dex', 'con', 'int', 'wis', 'cha']
    _scores = ['AC', 'natural_armor', 'deflection_bonus', 'dodge_bonus']

    def __init__(self, default_value=0):
        for k in self._abilities:
            self[k+'_score'] = default_value
        self.audit = False

    def __add__(self, other):
        assert isinstance(other, Attributes)
        added = Attributes()
        for attr in self._abilities:
            added[attr+'_score'] = self[attr+'_score'] + other[attr+'_score']
        return added

    def __str__(self):
        # Display only non-zero values of self
        s = []
        displayable = (self._abilities + self._scores +
                        [a+'_score' for a in self._abilities])
        for k, v in self.__dict__.iteritems():
            if k not in displayable:
                continue
            if v != 0:
                s.append("{0:s}: {1:+d}".format(k,v))
        return '(%s)' % ', '.join(s)


class Race(Attributes):
    pass

class Equipment(Attributes):
    def __init__(self, name):
        Attributes.__init__(self)
        self.name = name
    def __str__(self):
        return '%s %s' % (self.name, Attributes.__str__(self))

class CharacterMeta(AttributesMeta):
    def __new__(cls, name, bases, attrdict):
        _abilities = Attributes._abilities
        for k in _abilities:
            attrdict[k+'_score'] = auditable(_makeScore(k))

        return super(CharacterMeta, cls).__new__(cls, name, bases, attrdict)

class Character(Attributes):
    __metaclass__ = CharacterMeta
    def __init__(self):
        self.audit = False
        self.base = Attributes(10)
        self.race = Race()
        self.buffs = []
        self.equipment = []
        self.size_mod = 0
        self.BAB = 0

    @auditable
    def AC(self):
        """Armor Class"""
        base = 10
        equipment, _eqp = has_sum(self.equipment, 'AC')
        dex = self.dex
        natural_armor = self.natural_armor
        deflection_bonus = self.deflection_bonus
        dodge_bonus = self.dodge_bonus
        size_mod = self.size_mod
        return (base + _eqp + dex + natural_armor + deflection_bonus +
                  dodge_bonus + size_mod)

    @auditable
    def touch_AC(self):
        base = 10
        dex = self.dex
        deflection_bonus = self.deflection_bonus
        dodge_bonus = self.dodge_bonus
        size_mod = self.size_mod
        return (base + dex + deflection_bonus + dodge_bonus + size_mod)

    @auditable
    def flatfooted_AC(self):
        # Everything except dex
        base = 10
        equipment, _eqp = has_sum(self.equipment, 'AC')
        natural_armor = self.natural_armor
        deflection_bonus = self.deflection_bonus
        dodge_bonus = self.dodge_bonus
        size_mod = self.size_mod
        return (base + _eqp + dex + natural_armor + deflection_bonus +
                  dodge_bonus + size_mod)

    @auditable
    def deflection_bonus(self):
        # Deflection bonuses do not stack
        _formula = "max(buffs, equpment)"
        buffs, _buffs = has_max(self.buffs, 'deflection_bonus')
        equipment, _eqp = has_max(self.equipment, 'deflection_bonus')
        return max(_buffs, _eqp)

    @auditable
    def dodge_bonus(self):
        # Dodge bonus _does_ stack
        buffs, _buffs = has_sum(self.buffs, 'dodge_bonus')
        equipment, _eqp = has_sum(self.equipment, 'dodge_bonus')
        return _buffs + _eqp

    @auditable
    def natural_armor(self):
        _formula = "max(buffs, equpment)"
        buffs, _buffs = has_max(self.buffs, 'natural_armor')
        equipment, _eqp = has_max(self.equipment, 'natural_armor')
        return max(_buffs, _eqp)

    @auditable
    def melee_atk_bonus(self):
        BAB = self.BAB
        str = self.str
        size = self.size_mod
        buffs, _buffs = has_sum(self.buffs, 'atk')
        # Figure out all the attacks
        _a = [BAB,]
        while _a[-1] > 0:
            _a.append(_a[-1]-5)
        _a = _a[:-1]
        return [_aa+str+size+_buffs for _aa in _a]

    @auditable
    def ranged_atk_bonus(self):
        BAB = self.BAB
        dex = self.dex
        size = self.size_mod
        buffs, _buffs = has_sum(self.buffs, 'atk')
        # Figure out all the attacks
        _a = [BAB,]
        while _a[-1] > 0:
            _a.append(_a[-1]-5)
        if len(_a) > 1:
            _a = _a[:-1]
        return [_aa+dex+size+_buffs for _aa in _a]

class AuditResult(object):
    _display_order = (['base', 'BAB',] + Attributes._abilities
                      + [a+'_score' for a in Attributes._abilities]
                      + ['equipment','buffs']
                      + Attributes._scores)
    def __init__(self, formula, value, variables, name):
        if formula is None:
            self.formula = "Sum of"
        else:
            self.formula = formula
        self.value = value
        self.variables = variables.copy()
        self._name = name
    def show(self, fullTrace = True):
        spacer = '  '
        not_modifiers = ('_calcAttrScore', 'AC', 'base')
        variables = self.variables.copy()

        def get_displayworthy(v):
            # Skip any values not worth listing
            if not fullTrace:
                if type(v) is int and v == 0:
                    return ''
                elif type(v) is list and v == []:
                    return ''
                elif isinstance(v, AuditResult) and v.value == 0:
                    return ''
                elif isinstance(v, AuditResult) and v._name == '_calcMod':
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
                s += '{:+d}'.format(v)
            else:
                s += str(v)
            s += '\n'
            return s

        s = self.formula + ':\n'
        # Grab keys in display order
        for k in self._display_order:
            v = variables.pop(k, None)
            if v is None:
                continue
            s += get_displayworthy(v)

        # Grab any remaining keys
        for k, v in variables.iteritems():
            s += get_displayworthy(v)

        # Print out result
        s = s.rstrip() + '\n'
        if (type(self.value) is int
            and self._name not in not_modifiers):
            s += '= {:+d}'.format(self.value)
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
    def __str__(self):
        return self.show(False)





c = Character()
c.audit = True
c.base.str_score = 19
c.base.dex_score = 16
c.base.con_score = 14
c.BAB = 5
print c.AC
chain_shirt = Equipment('Chain Shirt')
chain_shirt.AC = 6
c.equipment.append(chain_shirt)
amulate = Equipment('Amulate of Natural Armor')
amulate.natural_armor = 2
c.equipment.append(amulate)
print c.AC

print c.ranged_atk_bonus