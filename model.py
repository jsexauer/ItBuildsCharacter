
import random, sys, itertools
from pprint import pprint
from StringIO import StringIO
from copy import copy
random.seed()

intOrNone = lambda x: None if x is None or x == '' else int(x)
intOrZero = lambda x: 0 if x is None or x == '' else int(x)

class Struct(object):
    def __getitem__(self, key):
        return getattr(self, key)
    def __setitem__(self, key, value):
        setattr(self, key, value)


def roll_d(dice):
    """Roll a dXX dice"""
    return random.randrange(1,dice+1,1)




#########################################################################

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
        _formula = '(score-10)/2'
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
        return (base + racial + _buffs + _eqp)
    return _calcAttrScore

def _makeSave(_save, _attr):
    def _calcMod(self):
        base = self.base[_save]
        locals()[_attr] = self[_attr]   # Con/Ref/Dex modifier
        buffs, _buffs = has_sum(self.buffs, _attr)
        return base + locals()[_attr] + _buffs
    return _calcSave


class AttributesMeta(type):
    def __new__(cls, name, bases, attrdict):
        _abilities = attrdict.get('_abilities', {})
        for k in _abilities:
            attrdict[k] = auditable(_makeMod(k))

        _scores = attrdict.get('_scores', {})
        for k in _scores:
            attrdict[k] = 0

        _saves = attrdict.get('_saves', {})
        for k, v in _saves.iteritems():
            attrdict[k] = 0
        return super(AttributesMeta, cls).__new__(cls, name, bases, attrdict)

class Attributes(Struct):
    __metaclass__ = AttributesMeta
    _abilities = ['str', 'dex', 'con', 'int', 'wis', 'cha']
    _scores = ['HP', 'AC', 'natural_armor', 'deflection_bonus', 'dodge_bonus',
               'atk', 'dmg']
    _saves = {'fort': 'con',
              'ref':  'dex',
              'will': 'wis'
             }

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

class Attack(object):
    def __init__(self, atk, dmg_roll, crit_range, crit_mult):
        self.name = ''
        self.character = Character()
        self.iterative = 0
        self.base = Struct()
        self.base.atk = atk
        self.base.dmg_roll = dmg_roll
        self.base.crit_range = crit_range
        self.base.crit_mult = crit_mult
        # UI Details
        self.id = -1
        self.ui_id = ''

    @auditable
    def atk(self):
        _formula = "BAB at iterative + weapon"
        iterative = self.iterative
        BAB = self.character.melee_atk_bonus[self.iterative]
        weapon = self.base.atk
        return BAB + weapon

    @auditable
    def dmg_roll(self):
        weapon = self.base.dmg_roll
        equipment, _eqp = has_sum(self.character.equipment, 'dmg')
        buffs, _buff = has_sum(self.character.buffs, 'dmg')
        str = self.character.str
        return weapon + _eqp + _buff + str

    @property
    def crit_range(self):
        # Don't support buffs that mess with crits yet
        return self.base.crit_range
    @property
    def crit_mult(self):
        # Don't support buffs that mess with crits yet
        return self.base.crit_mult
    @property
    def audit(self):
        return self.character.audit

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

    def __str__(self):
        if self.audit:
        #    # We're auditing so be special
        #    return ('<<\n' + get_displayworthy('Attack', self.dmg_roll, False) +
        #            ';\n' + get_displayworthy('Damage', self.atk, False) + '>>')
            return '{0:+d} for {1} damage'.format(self.atk.value,
                                                  self.dmg_roll.value)
        else:
            return '{0:+d} for {1} damage'.format(self.atk,
                                                  self.dmg_roll)



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
        elif isinstance(other, AuditResult):
            return self + other.value
        else:
            raise ValueError("Cannot add %s to %s" % (other, self))


class Equipment(Attributes):
    def __init__(self, name):
        Attributes.__init__(self)
        self.name = name
    def __str__(self):
        return '%s (%s)' % (self.name, Attributes.__str__(self))

class Weapon(Equipment):
    def __init__(self, name, attack):
        Attributes.__init__(self)
        self.name = name
        assert isinstance(attack, Attack)
        self._attack = attack

    @auditable
    def atk(self):
        return self._attack

    def __str__(self):
        return '%s (%s)' % (self.name, self.atk)

class CharacterEquipmentList(list):

    @property
    def main_hand(self):
        return getattr(self, '_main_hand', None)
    @main_hand.setter
    def main_hand(self, value):
        self._main_hand = value
        if value not in self:
            self.append(value)

    @property
    def off_hand(self):
        return getattr(self, '_off_hand', None)
    @off_hand.setter
    def off_hand(self, value):
        self._off_hand = value
        if value not in self:
            self.append(value)



class CharacterMeta(AttributesMeta):
    def __new__(cls, name, bases, attrdict):
        # Ability scores are devrived instead of settable for a character
        _abilities = Attributes._abilities
        for k in _abilities:
            attrdict[k+'_score'] = auditable(_makeScore(k))

        # Saress are devrived instead of settable for a character
        _saves = attrdict.get('_saves', {})
        for k, v in _saves.iteritems():
            attrdict[k] = auditable(_makeSave(k, v))

        return super(CharacterMeta, cls).__new__(cls, name, bases, attrdict)

class Character(Attributes):
    __metaclass__ = CharacterMeta
    def __init__(self):
        self.audit = False
        self.base = Attributes(10)
        self.race = Race()
        self.buffs = []
        self.equipment = CharacterEquipmentList()
        self.size_mod = 0
        self.BAB = 0
        # Alias attack as BAB
        self.atk = self.BAB

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
        _formula = "max(buffs, equipment)"
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
        _formula = "max(buffs, equipment)"
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
        if BAB > 0:
            # At 0 BAB, we'll remove ourselves if we're not careful
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

    @auditable
    def attacks(self):
        # Values for display
        _formula = "Permuations of"
        attacks = self.melee_atk_bonus

        # Now do the real calculations
        _attacks = []
        main_hand = self.equipment.main_hand
        assert isinstance(main_hand, Weapon)
        if self.equipment.off_hand is not None:
            off_hand = self.equipment.off_hand
            assert isinstance(off_hand, Weapon)
            # Two weapon fighting
            # TODO: Include calcs if you don't have the feat
            #   and/or off-hand is not light
            _mh_debuff = Buff('TWF MH Debuff (with feat)')
            _mh_debuff.atk = -2
            _oh_debuff = Buff('TWF OH Debuff (with feat)')
            _oh_debuff.atk = -2
            self.buffs.append(_mh_debuff)

        # Main Hand
        for _iter in range(len(self.melee_atk_bonus)):
            _atk = copy(main_hand.atk)
            #_atk = _wep.atk
            _atk.character = self
            _atk.iterative = int(_iter)
            _attacks.append(_atk)

        # Off Hand
        if self.equipment.off_hand is not None:
            self.buffs.append(_oh_debuff)
            attacks = self.melee_atk_bonus  # Update to show debuffs
            self.buffs.remove(_mh_debuff)

            for _iter in range(len(self.melee_atk_bonus)):
                _atk = copy(off_hand.atk)
                #_atk = _wep.atk
                _atk.character = self
                _atk.iterative = int(_iter)
                _attacks.append(_atk)


        return _attacks

    @property
    def dmg(self):
        raise AttributeError("Characters do not have dmg. Use attacks instead.")

class Buff(Attributes):
    _last_id = -1
    def __init__(self, name, atk_mod=0, dmg_mod=0):
        Attributes.__init__(self)
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





c = Character()
c.audit = True
c.base.str_score = 19
c.base.dex_score = 16
c.base.con_score = 14
c.BAB = 5
print "AC no armor:", c.AC
chain_shirt = Equipment('Chain Shirt')
chain_shirt.AC = 6
c.equipment.append(chain_shirt)
amulate = Equipment('Amulate of Natural Armor')
amulate.natural_armor = 2
c.equipment.append(amulate)
print "AC with armor: ", c.AC
print "Ranged atk bonus: ", c.ranged_atk_bonus
tidewater_cutless = Weapon("Tidewater Cuttless +1",
                      Attack(atk=+1, dmg_roll=DamageRoll.fromString("1d6+1"),
                             crit_range=[18,19,20], crit_mult=2))
c.equipment.main_hand = tidewater_cutless
masterwork_handaxe = Weapon("Masterwork Handaxe",
                      Attack(atk=0, dmg_roll=DamageRoll.fromString("1d6"),
                             crit_range=[20,], crit_mult=3))
print "Attacks (no OH): ", c.attacks
c.equipment.off_hand = masterwork_handaxe
print "Attacks (with OH): ", c.attacks