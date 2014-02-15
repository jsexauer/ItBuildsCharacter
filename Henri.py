##############################################################################
# Henri
# Level 5 Cavalier
##############################################################################

from model import Character, RPGClass, Equipment, Weapon, Attack, Buff

class Cavalier(RPGClass):
    def __init__(self):
        super(Cavalier, self).__init__()
        self.hit_die = 8
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

# Weapons
feybane_greatsword = Weapon("+2 Feybane Greatsword",
                        Attack(2, "2d6+2", [19,20], two_handed=True))
c.equipment.main_hand = feybane_greatsword

greatsword = Weapon("Greatsword", Attack(0, "2d6", [19,20], two_handed=True))
c.equipment.append(greatsword)

cmpst_lng_bow = Weapon("+2 Cmpst Lng Bow", Attack(2, "1d8", ranged=True))
c.equipment.append(cmpst_lng_bow)




### Possible Buffs
pbl  = []


bulls_strength = Buff("Bull's Strength")
bulls_strength.str_score = 4
pbl.append(bulls_strength)

pbl.append(Buff('Bless',atk_mod=1,dmg_mod=0))
bless = Buff('Prayer',atk_mod=1,dmg_mod=1)
bless.ref = 1
bless.fort = 1
bless.will = 1
pbl.append(bless)

challenge = Buff('Challenge', dmg_mod=5)
challenge.AC = 1
pbl.append(challenge)
challenge2 = Buff('Challenge (Non-target)')
challenge2.AC = -2
pbl.append(challenge2)

charge = Buff("Cavalier's Charge", atk_mod=4)
pbl.append(charge)

pbl.append(Buff("Broken (weapon)", atk_mod=-2, dmg_mod=-2))

buckler = Buff("Buckler")
buckler.AC = 1
buckler.atk = -1
pbl.append(buckler)

pbl += \
    [Buff('Sickened',atk_mod=-2,dmg_mod=-2),
     Buff('Flanking',atk_mod=2)]

possible_buffs_list = pbl