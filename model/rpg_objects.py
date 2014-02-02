
from common import *
from attributes import Attributes
from audit import AuditResult

class Attack(object):
    def __init__(self, atk, dmg_roll, crit_range, crit_mult, oh=False):
        self.name = ''
        self.character = Character()
        self.iterative = 0
        self.base = Struct()
        self.base.atk = atk
        self.base.dmg_roll = dmg_roll
        self.base.crit_range = crit_range
        self.base.crit_mult = crit_mult
        self.is_oh = oh     # Off hand attack
        # UI Details
        self.id = -1
        self.ui_id = ''

    @auditable
    def atk(self):
        _formula = "BAB at iterative + weapon"
        iterative = self.iterative
        if self.is_oh:
            BAB = self.character.oh_melee_atk_bonus[self.iterative]
        else:
            BAB = self.character.mh_melee_atk_bonus[self.iterative]
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
    def __eq__(self, other):
        if not isinstance(other, Attack):
            raise AssertionError    # We probably didn't mean to do this
            return False
        return (self.atk+0 == other.atk+0) and \
                (self.dmg_roll == other.dmg_roll) and \
                (self.crit_range == other.crit_range) and \
                (self.crit_mult == other.crit_mult)




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
    def __eq__(self, other):
        if isinstance(other, AuditResult):
            other = other.value
        if not isinstance(other, DamageRoll):
            raise AssertionError    # Probably didn't mean to do this
            return False
        return str(self) == str(other)  # If the descripter matches, I'm happy

class Skill(object):
    def __init__(self, name, attr, useUntrained, useACP, character):
        self.name = name
        self.attr = attr
        self.useUntrained = useUntrained
        self.useACP = useACP
        self.character = character
        self.ranks = 0
        self.isClassSkill = False

    @auditable
    def value(self):
        if not self.useUntrained and self.ranks == 0:
            raise RuntimeWarning('Tried to %s untrained' % self.name)
            return -999
        locals()[self.attr] = self.character[self.attr]  # dex/str/int/etc...
        ranks = self.ranks
        buffs, _buffs = has_skill(self.character.buffs, self.name)
        equipment, eqp = has_skill(self.character.equipment, self.name)
        _cs = 0
        if self.ranks > 0:
            class_skill = self.character.rpg_class.skills[self.name]
            _cs = class_skill
        _acp = 0
        if self.useACP:
            ACP = self.character.ACP
            _acp = ACP

        return locals()[self.attr] + ranks + _buffs + eqp + _cs + _acp

    @property
    def audit(self):
        return self.character.audit




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


class Feat(Attributes):
    def __init__(self, name, atk_mod=0, dmg_mod=0):
        Attributes.__init__(self)
        self.name = name

class RPGClass(Attributes):
    pass


from character import Character