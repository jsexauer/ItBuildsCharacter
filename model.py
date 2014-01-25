
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
    def __init__(self, name, atk_mod=0, dmg_mod=0):
        self.name = name
        # Modifiers
        self.atk = intOrZero(atk_mod)
        self.dmg_roll = DamageRoll(None, None, dmg_mod)
        # UI Details
        self.ui_id = None
    def makeUI(self, id):
        assert type(id) is int
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
    def __str__(self):
        return self.name
    def __repr__(self):
        return "<'%s' at %s>"%(self.name, hex(id(self)))



class Attack(object):
    def __init__(self, name, atk, dmg_roll, crit_range, crit_mult):
        self.name = name
        self.base = Struct()
        self.base.atk = atk
        self.base.dmg_roll = dmg_roll
        self.base.crit_range = crit_range
        self.base.crit_mult = crit_mult
        self.buffs = []
        # UI Details
        self.ui_id = None

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

    def makeUI(self, id):
        assert type(id) is int
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
                android:layout_weight=".2"
                android:text="%(name)s" />

            <TextView
                android:id="@+id/%(id)s_Atk"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_weight=".3"
                android:layout_marginRight="30dp"
                android:text="+%(atk)s" />

            <TextView
                android:id="@+id/%(id)s_Dmg"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_weight=".3"
                android:layout_marginRight="30dp"
                android:text="%(dmg)s" />

            <Button
                android:id="@+id/RollBtn%(id)s"
                style="?android:attr/buttonStyleSmall"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_weight=".3"
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
    def roll(self):
        roll = self.add
        for n in range(self.numDice):
            roll += roll_d(self.dice)
        return roll
    def __str__(self):
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

attacks = [Attack('Tidewater Cutless +1 (MH)',8,DamageRoll(1,6,5),[18,19,20],2),
           Attack('Masterwork Handaxe (OH)',8,DamageRoll(1,6,4),[20,],3)]
buffs = [Buff('Favored Enemy (Human)',4,4),
         Buff('Favored Enemy (Monstrous Humanoid)',2,2),
         Buff('100 to damage',dmg_mod=95)]