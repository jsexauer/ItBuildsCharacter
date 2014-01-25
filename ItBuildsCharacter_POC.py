# From:
# https://code.google.com/p/android-scripting/wiki/FullScreenUI
import android
try:
    # Create droid object if we're on the phone
    droid = android.Android()
except:
    try:
        # Create droid object if we're on computer
        droid=android.Android(('192.168.3.10','36161'))
    except:
        raise RuntimeError("Could not connect to android device")

import random
random.seed()


layout_template = """<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/background"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="#ff000000"
    android:orientation="vertical" >

    <TextView
        android:id="@+id/textView2"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Buffs:" />

        %(Buffs)s

    <TextView
        android:id="@+id/TextView01"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Attacks:" />

    <TableLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:gravity="center"
        android:stretchColumns="0">

        %(Attacks)s

    </TableLayout>
</LinearLayout>
"""

layout2 = """<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/background"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="#ff000000"
    android:orientation="vertical" >

    <TextView
        android:id="@+id/textView1"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Create Buff"
        android:textAppearance="?android:attr/textAppearanceLarge" />

    <TableLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content" >

        <TableRow
            android:id="@+id/tableRow1"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content" >

            <TextView
                android:id="@+id/textView2"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Buff Name:" />

            <EditText
                android:id="@+id/buffName"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:ems="10" >

                <requestFocus />
            </EditText>

        </TableRow>

        <TableRow
            android:id="@+id/tableRow2"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content" >

            <TextView
                android:id="@+id/textView3"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Buff Attack Modifier:" />

            <EditText
                android:id="@+id/buffAtk"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:ems="10"
                android:inputType="number" />

        </TableRow>

        <TableRow
            android:id="@+id/tableRow3"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content" >

            <TextView
                android:id="@+id/textView4"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Buff Damage Modifier:" />

            <EditText
                android:id="@+id/buffDmg"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:ems="10"
                android:inputType="number" />

        </TableRow>
    </TableLayout>

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content" >

        <Button
            android:id="@+id/btnSave"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:text="Save" />

        <Button
            android:id="@+id/btnCancel"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:text="Cancel" />

    </LinearLayout>

</LinearLayout>


"""


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
        alert_dialog(self.name, s)
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

def alert_dialog(title, message, buttonText='Ok'):
  droid.dialogCreateAlert(title, message)
  droid.dialogSetPositiveButtonText('Continue')
  droid.dialogShow()
  response = droid.dialogGetResponse().result
  return response['which'] == 'positive'

def eventloop():
    global buffs, attacks
    while True:
        event=droid.eventWait().result
        print event
        if event["name"]=="click":
            id=event["data"]["id"]
            if id[:4] == "Buff":
                # A buff has been updated
                active_buffs = []
                for n, b in enumerate(buffs):
                    info = get_info = droid.fullQueryDetail("Buff%d"%n).result
                    if info['checked']=='true':
                        active_buffs.append(b)
                print "Active Buffs:", active_buffs
                for a in attacks:
                    a.updateUI(active_buffs, droid)
            elif id[:10] == "RollBtnAtk":
                # User asked for us to roll an attack
                atk_id = int(id[10:])
                attacks[atk_id].roll()
        elif event['name']=='menu_newBuff':
            #droid.fullDismiss()
            print droid.fullShow(layout2)
            buffs = eventloop_newBuff()
            buildMainWindow(attacks, buffs)
        elif event['name']=='menu_quit':
            # Quit menu bar button
            return
        elif event["name"]=="screen":
            if event["data"]=="destroy":
                return

def eventloop_newBuff():
    global buffs
    while True:
        event=droid.eventWait().result
        print "In newBuff:", event
        if event["name"]=="click":
            id=event["data"]["id"]
            if id == "btnSave":
                # A buff has been updated
                name = droid.fullQueryDetail("buffName").result['text']
                atk = droid.fullQueryDetail("buffAtk").result['text']
                dmg = droid.fullQueryDetail("buffDmg").result['text']
                print name, atk, dmg
                buffs += [Buff(name, atk, dmg)]
                break
            elif id[:10] == "btnCancel":
                # User cancels, return
                break
        elif event['name']=='menu_quit':
            # Quit menu bar button
            break
        elif event["name"]=="screen":
            if event["data"]=="destroy":
                break
    return buffs

print "Started"


attacks = [Attack('Tidewater Cutless +1 (MH)',8,DamageRoll(1,6,5),[18,19,20],2),
           Attack('Masterwork Handaxe (OH)',8,DamageRoll(1,6,4),[20,],3)]
buffs = [Buff('Favored Enemy (Human)',4,4),
         Buff('Favored Enemy (Monstrous Humanoid)',2,2),
         Buff('100 to damage',dmg_mod=95)]

def buildMainWindow(attacks, buffs):
    global layout_template
    atk_xml = '\n\n'.join([x.makeUI(n) for n,x in enumerate(attacks)])
    buffs_xml = '\n\n'.join([x.makeUI(n) for n,x in enumerate(buffs)])

    layout = layout_template % {'Buffs':buffs_xml, 'Attacks':atk_xml}
    print layout

    ###################################################################
    # See: http://www.mithril.com.au/android/doc/UiFacade.html#addOptionsMenuItem
    # Icons: http://androiddrawableexplorer.appspot.com/
    droid.clearOptionsMenu()
    droid.addOptionsMenuItem("Silly","silly",None,"star_on")
    droid.addOptionsMenuItem("New Buff","menu_newBuff",None,"star_off")
    droid.addOptionsMenuItem("Quit","menu_quit",None,"btn_close_normal")

    print droid.fullShow(layout)

buildMainWindow(attacks, buffs)
eventloop()
print droid.fullQuery()
print "Data entered =",droid.fullQueryDetail("editText1").result
droid.fullDismiss()