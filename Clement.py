############################################################################
# Clement
# Level 6 Ranger
############################################################################

# Detect if we're already inside IBC and thus, all of this has been
#   provided for us
if 'Character' not in locals().keys():
    from model import (Character, RPGClass, Equipment, Weapon, Attack,
                       Buff, Feat, auditable)

class Ranger(RPGClass):
    def __init__(self):
        super(Ranger, self).__init__()
        self.hit_die = 10
        self.fort = 5       # TODO: Scale will level
        self.ref = 5
        self.will = 2

c = Character()
c.name = 'Clement'
c.lvl = 6
c.BAB = 6
c.rpg_class = Ranger()

# Ability Scores
c.base.str_score = 19
c.base.dex_score = 16
c.base.con_score = 14
# All the others are the default value of 10

# Armor
breastplate = Equipment("Mithral Chain Shirt +2")
breastplate.AC = 6
breastplate.ACP = 0
c.equipment.append(breastplate)

cr = Equipment("Ammulute of Natural Armor +2")
cr.natural_armor = 2
c.equipment.append(cr)

# Weapons
wep1 = Weapon("+1 Tidewater Cutless",
                        Attack(1, "1d6+1", [18,19,20]))
c.equipment.main_hand = wep1

wep2 = Weapon("+1 Keen Mwk Handaxe", Attack(1, "1d6+1", [19,20], 3))
c.equipment.off_hand = wep2

wep3 = Weapon("+1 Vindictive Harpoon", Attack(1, "1d8+1", ranged=True))
c.equipment.append(wep3)

wep4 = Weapon("Battleaxe", Attack(0, "1d8", [20], 3))
c.equipment.append(wep4)

# Feats
twf = Feat("Two Weapon Fighting")
twf.twf_mh = +2
twf.twf_oh = +6
c.feats.append(twf)

resilient = Feat("Resilient")
resilient.fort = 1
resilient.twf_mh = 0
resilient.twf_oh = 0
c.feats.append(resilient)

### Possible Buffs
pbl  =  [Buff('Favored Enemy (Human)',4,4),
             Buff('Favored Enemy (Monstrous Humanoid)',2,2),
             Buff('Bless',atk_mod=1),
             Buff('Prayer',atk_mod=1,dmg_mod=1),
             Buff('Sickened',atk_mod=-2,dmg_mod=-2)]

bulls_strength = Buff("Bull's Strength")
bulls_strength.str_score = 4
pbl.append(bulls_strength)

pbl.append(Buff('Bless',atk_mod=1,dmg_mod=0))
bless = Buff('Prayer',atk_mod=1,dmg_mod=1)
bless.ref = 1
bless.fort = 1
bless.will = 1
pbl.append(bless)

pbl += \
    [Buff('Sickened',atk_mod=-2,dmg_mod=-2),
     Buff('Flanking',atk_mod=2)]

possible_buffs_list = pbl

#c.audit = True
print c.attacks
