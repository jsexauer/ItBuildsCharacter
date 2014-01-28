
import random
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


def _makeMod(attr):
    def _calcMod(self):
        return (self[attr+'Score'] - 10) // 2
    return _calcMod

def _makeScore(attr):
    attr = attr+'Score'
    def _calcAttrScore(self):
        return (self.base[attr] + self.race[attr] +
                sum(map(lambda x: x[attr], self.buffs)) )
    return _calcAttrScore

class AttributesMeta(type):
    def __new__(cls, name, bases, attrdict):
        _attrs = attrdict.get('_attrs', {})
        for k in _attrs:
            attrdict[k] = property(_makeMod(k))

        return super(AttributesMeta, cls).__new__(cls, name, bases, attrdict)

class Attributes(Struct):
    __metaclass__ = AttributesMeta
    _attrs = ['str', 'dex', 'con', 'int', 'wis', 'cha']

    def __init__(self, default_value=0):
        for k in self._attrs:
            self[k+'Score'] = default_value

    def __add__(self, other):
        assert isinstance(other, Attributes)
        added = Attributes()
        for attr in self._attrs:
            added[attr+'Score'] = self[attr+'Score'] + other[attr+'Score']
        return added

class Race(Attributes):
    pass



class CharacterMeta(AttributesMeta):
    def __new__(cls, name, bases, attrdict):
        _attrs = Attributes._attrs
        for k in _attrs:
            attrdict[k+'Score'] = property(_makeScore(k))

        return super(CharacterMeta, cls).__new__(cls, name, bases, attrdict)

class Character(Attributes):
    __metaclass__ = CharacterMeta
    def __init__(self):
        super(Attributes, self).__init__()
        self.base = Attributes(10)
        self.race = Race()
        self.buffs = []

