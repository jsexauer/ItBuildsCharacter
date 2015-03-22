############################################################################
# Henri
# Level 11 Cavalier
############################################################################

# Detect if we're already inside IBC and thus, all of this has been
#   provided for us
if 'Character' not in locals().keys():
    from model import (Character, RPGClass, Equipment, Weapon, Attack,
                       Buff, Feat, auditable)

class Cavalier(RPGClass):
    def __init__(self):
        super(Cavalier, self).__init__()
        self.hit_die = 10
        self.fort = 7      # TODO: Scale will level
        self.ref = 3
        self.will = 3

c = Character()
c.name = 'Henri (Level 11)'
c.lvl = 11
c.BAB = 11
c.rpg_class = Cavalier()

# Ability Scores
c.base.str_score = 20
c.base.dex_score = 12
c.base.con_score = 13
c.base.cha_score = 16
# All the others are the default value of 10

# Armor
breastplate = Equipment("Mytheral Breastplate of Speed")
breastplate.AC = 10
breastplate.ACP = -3
c.equipment.append(breastplate)

cr = Equipment("Cloak of Resistance +3")
cr.fort = 3
cr.ref = 3
cr.will = 3
c.equipment.append(cr)

rp = Equipment("Ring of Protection +2")
rp.deflection_bonus = 2
c.equipment.append(rp)

# Weapons
overnbayne = Weapon("Overnbayne",
                        Attack(3, "2d6+3", [19,20], two_handed=True))
c.equipment.main_hand = overnbayne

greatsword = Weapon("Greatsword", Attack(0, "2d6", [19,20], two_handed=True))
c.equipment.append(greatsword)

cmpst_lng_bow = Weapon("+2 Cmpst Lng Bow", Attack(2, "1d8", ranged=True))
c.equipment.append(cmpst_lng_bow)


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


### Possible Buffs
pbl  = []

pa = Buff("Power Attack", -3, +9)
pbl.append(pa)

fd = Buff('Fight Defensively')
fd.atk = -4
fd.AC = +2
pbl.append(fd)

buckler = Buff("Buckler")
buckler.AC = 2
buckler.atk = -1
pbl.append(buckler)

challenge = Buff('Challenge', dmg_mod=9)
challenge.AC = 2
pbl.append(challenge)
challenge2 = Buff('Challenge (Non-target)')
challenge2.AC = -2
pbl.append(challenge2)

charge = Buff("Cavalier's Charge", atk_mod=4)
pbl.append(charge)

pbl.append(Buff("Banner (when charging)", atk_mod=1))

pbl.append(Buff('Flanking',atk_mod=2))

pbl.append(Buff('Bless',atk_mod=1,dmg_mod=0))
bless = Buff('Prayer',atk_mod=1,dmg_mod=1)
bless.ref = 1
bless.fort = 1
bless.will = 1
pbl.append(bless)

haste = Buff("Haste", atk_mod=1)
haste.dodge_bonus = 1
pbl.append(haste)

bulls_strength = Buff("Bull's Strength")
bulls_strength.str_score = 4
pbl.append(bulls_strength)

pbl += \
    [Buff('Sickened',atk_mod=-2,dmg_mod=-2),
     ]

possible_buffs_list = pbl