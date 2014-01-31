# Test Model
from model import Character, Equipment, Weapon, Attack, DamageRoll, Buff, auditable

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

c.base.fort = 4
c.base.ref = 4
c.base.will = 1
print "Fort: ", c.fort

haste = Buff("Haste")
def apply_haste(character):
    def _haste_wrapper(attack_bonuses):
        _formula = 'Haste adds extra attack at full BAB'
        return attack_bonuses + [attack_bonuses[0]]
    character.melee_atk_bonus = auditable(_haste_wrapper(character.melee_atk_bonus))
    character.ranged_atk_bonus = auditable(_haste_wrapper(character.ranged_atk_bonus))
haste.on_apply = apply_haste

c.buffs.append(haste)
print "Hasted Melee Atk Bonus: ", c.melee_atk_bonus