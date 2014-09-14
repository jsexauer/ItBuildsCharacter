
from common import *
from attributes import Attributes
from audit import AuditResult

class Attack(object):
    def __init__(self, atk, dmg_roll, crit_range=[20,], crit_mult=2, oh=False,
                  name=None, two_handed=False, ranged=False):
        self.name = name
        self.character = Character()
        self.iterative = 0
        self.base = Struct()
        self.base.atk = atk
        if isinstance(dmg_roll, basestring):
            # Create a damage roll
            self.base.dmg_roll = DamageRoll.fromString(dmg_roll)
        elif isinstance(dmg_roll, DamageRoll):
            self.base.dmg_roll = dmg_roll
        else:
            raise ValueError("Unexpected damage roll: %s" % dmg_roll)
        self.base.crit_range = crit_range
        self.base.crit_mult = crit_mult
        self.is_oh = oh     # Off hand attack
        self.two_handed = two_handed
        self.ranged = ranged

    @auditable
    def atk(self):
        _formula = "Attack Bonus at iterative + weapon"
        iterative = self.iterative
        if self.is_oh:
            AB = self.character.oh_melee_atk_bonus[self.iterative]
        else:
            if self.ranged:
                AB = self.character.ranged_atk_bonus[self.iterative]
            else:
                AB = self.character.mh_melee_atk_bonus[self.iterative]
        weapon = self.base.atk
        return AB + weapon

    @auditable
    def dmg_roll(self):
        weapon = self.base.dmg_roll
        equipment, _eqp = has_sum(self.character.equipment, 'dmg_roll')
        buffs, _buff = has_sum(self.character.buffs, 'dmg_roll')
        _str = 0
        if not self.ranged:
            str = self.character.str
            _str = str
        _th = 0
        if self.two_handed:
            two_handed_str_bonus = int(self.character.str*0.5)
            _th = two_handed_str_bonus

        return weapon + _eqp + _buff + _str + _th

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
        s = str(self) + '\n\n'
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
            conf_note = ''
            # See if we have Critical Focus feat
            crit_focus = [f for f in self.character.feats if f.name == 'Critical Focus']
            if len(crit_focus) > 0:
                conf_roll += 4
                conf_note = ' (includes critical focus)'
            crit_dmg = dmg + sum([self.dmg_roll.roll()
                                  for n in range(self.crit_mult-1)])
            s += "If a %d confirms, %d damage.\n" % (conf_roll, crit_dmg)
            s += "            Else: %d damage\n" % dmg
            s += conf_note
        elif atk_roll == 1:
            # Critical Failure
            s += "Rolled a <1>.\nCritical Failure."
        else:
            s += "Rolled a <%d>.\n%d to hit for %d damage.\n" % \
                  (atk_roll, atk_roll+self.atk, dmg)
        return s

    def makeUI(self, id):
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
        return template % {'id': id, 'name': self.name,
                            'atk':self.atk, 'dmg':self.dmg_roll}
    def updateUI(self, id, droid):
        ui_id = "Atk"+str(id)
        droid.fullSetProperty(ui_id+'_Atk',"text","+"+str(self.atk))
        droid.fullSetProperty(ui_id+'_Dmg',"text",str(self.dmg_roll))

    @auditable
    def _as_audit_object(self):
        """Make a version of this attack which is an audit object"""
        _formula = "Attack of..."
        attack = self.atk
        damage = self.dmg_roll
        return str(self)

    def __str__(self):
        if self.audit:
            atk = self.atk.value
            dmg = self.dmg_roll.value
        else:
            atk = self.atk
            dmg = self.dmg_roll
        s = '{0:+d} for {1} damage'.format(atk, dmg)
        if self.audit:
            # We're auditing so be special
##            return '<<\n' + get_displayworthy('Attack', self.atk, False) + \
##                    ';\n' + get_displayworthy('Damage', self.dmg_roll, False) + \
##                    '>>\n  = ' + s
            return s
        else:
            return s
    def __eq__(self, other):
        if not isinstance(other, Attack):
            #raise AssertionError    # We probably didn't mean to do this
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
    def __radd__(self, other):
        return self + other

    def __eq__(self, other):
        if isinstance(other, AuditResult):
            other = other.value
        if not isinstance(other, DamageRoll):
            #raise AssertionError    # Probably didn't mean to do this
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
    def __str__(self):
        return self.name + ' ' + Attributes.__str__(self)
    def __repr__(self):
        return "<'%s' at %s>"%(self.name, hex(id(self)))

class RPGClass(Attributes):
    def __init__(self):
        Attributes.__init__(self)
        self.hit_die = 0
    pass


from character import Character
from audit import get_displayworthy