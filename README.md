ItBuildsCharacter
=================
Yet another app for the [Pathfinder Roleplaying Game](http://paizo.com/pathfinderRPG)
to manage characters and combat.
http://jsexauer.github.io/ItBuildsCharacter
Overview
--------

Some features that make ItBuildsCharacter unique over others:
  - **Andorid App**: Android app built using [kivy](http://www.kivy.org) framework.
    See pictures [below](#app_ss).
  - **Python Model**: An extensive model has been created to allow the definition of characters
  as python objects.  An example is [presented below](#char_def) and is
  the character used in the following examples.
  - **Auditing**: Full auditing of all statistics to show how they were derived:
```
>>> with c.audit_context:
...     print c.HP
hit_die + (level-1)*hp_per_level + con*level + favored_class + feats:
  con: +1
  level: +5
  favored_class: +5
  hit_die: +10
  feats:
    Toughness (HP: +5)
  hp_per_level: +6
= +49
>>> with c.audit_context:
...     print c.attacks[0]
Attack of...:
  attack: <Attack Bonus at iterative + weapon:
            weapon: +2
            AB: <Sum of:
                  BAB: +5
                  str: +4
                = +9>
          = +11>
  damage: <Sum of:
            str: +4
            weapon: 2d6+2
            two_handed_str_bonus: +2
          = 2d6+8>
= +11 for 2d6+8 damage
```
  - **Buffs**:  Toggle on buffs and conditions like flanking, rage, Bless,
  Inspire Courage, etc...  Statistics and attacks automatically update.  For
  example, let's say our [example Cavalier](#char_def) is blessed and
  challenges his target:
```
>>> challenge = Buff('Challenge', dmg_mod=5)
>>> challenge.AC = 1
>>> c.buffs.append(challenge)
>>> c.buffs.append(Buff('Bless', atk_mod=1))
>>> with c.audit_context:
...     print c.attacks[0]
Attack of...:
  attack: <Attack Bonus at iterative + weapon:
            weapon: +2
            AB: <Sum of:
                  BAB: +5
                  str: +4
                  buffs:
                    Bless (+1)
                = +10>
          = +12>
  damage: <Sum of:
            str: +4
            buffs:
              Challenge (+5)
            weapon: 2d6+2
            two_handed_str_bonus: +2
          = 2d6+13>
= +12 for 2d6+13 damage
```
  - **Counters**:  Track things like HP, gold, XP, ki pool, etc.  These are
  automatically saved to the sever, which brings us to...
  - **Website Integration**:  The character definition and counter statuses are
  automatically synced between the phone app and the website.  Ultimately, I
  hope to build off of the web-ui of [MythWeavers](http://www.myth-weavers.com/sheetindex.php),
  which is based on the open-source project [3EProfiler](http://sourceforge.net/projects/rpgwebprofiler/).


<a name="app_ss"/>
Android App Screenshots
-----------------------
### Statistics Screen ###
![Stats Screen](http://jsexauer.github.io/ItBuildsCharacter/img/stats.png)
### Attacks/Buffs Screen ###
![Attacks/Buffs Screen](http://jsexauer.github.io/ItBuildsCharacter/img/buffs.png)
### Counters ###
![Counters Screen](http://jsexauer.github.io/ItBuildsCharacter/img/counters.png)
### Audits ###
A long-press on any dark-colored number will show its audit results

![Audit Screen](http://jsexauer.github.io/ItBuildsCharacter/img/audit.png)

<a name="char_def"/>
Example Character Definition
----------------------------
The code below will create a level 5 human Cavalier named Henri.
```python
from model import (Character, RPGClass, Equipment, Weapon, Attack,
                   Buff, Feat, auditable)

class Cavalier(RPGClass):
    def __init__(self):
        super(Cavalier, self).__init__()
        self.hit_die = 10
        self.fort = 4       # TODO: Scale will level
        self.ref = 1
        self.will = 1

c = Character()
c.name = 'Henri'
c.lvl = 5
c.BAB = 5
c.rpg_class = Cavalier()

# Ability Scores
c.base.str_score = 19
c.base.dex_score = 12
c.base.con_score = 13
c.base.cha_score = 14
# All the others are the default value of 10
```
Let's now give him a Masterwork Breastplate +2 and a Cloak of Resistance +1.
```python
# Armor
breastplate = Equipment("Masterwork Breastplate +2")
breastplate.AC = 8
breastplate.ACP = -3
c.equipment.append(breastplate)

cr = Equipment("Cloak of Resistance +1")
cr.fort = 1
cr.ref = 1
cr.will = 1
c.equipment.append(cr)
```
To defend himself against the evils of Golarion, he needs a +2 Feybane
Greatsword and a Composite long bow (in case he has to fight at range).
```python
# Weapons
feybane_greatsword = Weapon("+2 Feybane Greatsword",
                        Attack(2, "2d6+2", [19,20], two_handed=True))
c.equipment.main_hand = feybane_greatsword

cmpst_lng_bow = Weapon("+2 Cmpst Lng Bow", Attack(2, "1d8", ranged=True))
c.equipment.append(cmpst_lng_bow)
```
Finally, Henri took Toughness, which will scale as he levels.  Notice that we
can define a custom formula which show up during when we audit how his
hit points were calculated.
```python
# Feats
class Toughness(Feat):
    def on_apply(self, character):
        self.character = character
    @auditable
    def HP(self):
        _formula = "3 + max(lvl-3, 0)"
        lvl = self.character.lvl
        return 3 + max(lvl-3,0)
toughness = Toughness("Toughness")
c.feats.append(toughness)
```

Installing and Using
--------------------

Right now, ItBuildsCharacter is alpha-quality software.  I develop it as I find
new features I'd like to have.  However, I am interested in releasing it to a
larger user base if other find it useful.  If you would like to use the program:
  - Download the [Kivy Launcher](https://play.google.com/store/apps/details?id=org.kivy.pygame)
  - Copy the contents of the [master branch](https://github.com/jsexauer/ItBuildsCharacter/zipball/master)
    into a subdirectory of `/sdcard/kivy`.
  - Launch the Kivy Launcher and select "ItBuildsCharacter"
  - Very basic web support (editing the character definition) can be done at:
  http://genericlifeform.pythonanywhere.com/IBC/characters/0 (Replace 0 with
  any character id)
  - Please feel free to [contact me](mailto:genericcarbonlifeform@gmail.com) for
  additional help.

Development
-----------
Right now [I](https://github.com/jsexauer) am the only developer.  Pull requests
are welcome!  Developed for Python 2.7 and Android 4.1.2.