# Test Model
from model import (Character, Equipment, Weapon, Attack, DamageRoll,
                    Buff, Feat, auditable)

def assert_audit(audit_obj, true_value, msg=''):
    """Helper function to help asserting when value object abound"""
    if msg == '':
        msg = "Calculated value of %s <> %s" % (audit_obj.value, true_value)
    assert audit_obj.value == true_value, msg

c = Character()
c.audit = True
c.base.str_score = 19
c.base.dex_score = 16
c.base.con_score = 14
c.BAB = 5
c.base.fort = 4
c.base.ref = 4
c.base.will = 1
print "Fort: ", c.fort
assert_audit(c.fort, 6)

print "AC no armor:", c.AC
assert_audit(c.AC, 13)

chain_shirt = Equipment('Chain Shirt')
chain_shirt.AC = 6
c.equipment.append(chain_shirt)
amulate = Equipment('Amulate of Natural Armor')
amulate.natural_armor = 2
c.equipment.append(amulate)
print "AC with armor: ", c.AC
assert_audit(c.AC, 21)

print "Ranged atk bonus: ", c.ranged_atk_bonus
assert_audit(c.ranged_atk_bonus, [8])
tidewater_cutless = Weapon("Tidewater Cuttless +1",
                      Attack(atk=+1, dmg_roll=DamageRoll.fromString("1d6+1"),
                             crit_range=[18,19,20], crit_mult=2))
c.equipment.main_hand = tidewater_cutless
masterwork_handaxe = Weapon("Masterwork Handaxe",
                      Attack(atk=1, dmg_roll=DamageRoll.fromString("1d6"),
                             crit_range=[20,], crit_mult=3))
print "Attacks (no OH): ", c.attacks
assert_audit(c.attacks, [Attack(atk=10, dmg_roll=DamageRoll.fromString("1d6+5"),
                             crit_range=[18,19,20], crit_mult=2)])

c.equipment.off_hand = masterwork_handaxe
print "Attacks (with OH no feats): ", c.attacks
assert_audit(c.attacks, [Attack(atk=6, dmg_roll=DamageRoll.fromString("1d6+5"),
                             crit_range=[18,19,20], crit_mult=2),
                         Attack(atk=2, dmg_roll=DamageRoll.fromString("1d6+4"),
                             crit_range=[20,], crit_mult=3), ])


twf = Feat("Two Weapon Fighting")
twf.twf_mh = +2
twf.twf_oh = +6
c.feats.append(twf)

print "Attacks (with OH and feats): ", c.attacks
assert_audit(c.attacks, [Attack(atk=8, dmg_roll=DamageRoll.fromString("1d6+5"),
                             crit_range=[18,19,20], crit_mult=2),
                         Attack(atk=8, dmg_roll=DamageRoll.fromString("1d6+4"),
                             crit_range=[20,], crit_mult=3), ])


haste = Buff("Haste")
def apply_haste(character):
    class HasteWrap(object):
        def __init__(self, orig_atk_bonus):
            self.orig_atk_bonus = orig_atk_bonus
        def __call__(self, _child_self):
            _formula = 'Haste adds extra attack at full BAB'
            base_attacks = self.orig_atk_bonus
            haste_attack = base_attacks[0]
            return base_attacks + [haste_attack]
        func_name = "HasteWrap (class)" # Needed for auditable
    # Apply to only MH
    character.mh_melee_atk_bonus = auditable(HasteWrap(character.mh_melee_atk_bonus))
    character.ranged_atk_bonus = auditable(HasteWrap(character.ranged_atk_bonus))
#haste.on_apply = apply_haste
haste.atk = 1
haste.dodge_bonus = 1
haste.ref = 1
c.buffs.append(haste)

assert_audit(c.ref, 8)
assert_audit(c.AC, 22)

print "Hasted Melee Attacks: ", c.attacks


assert_audit(c.attacks, [Attack(atk=9, dmg_roll=DamageRoll.fromString("1d6+5"),
                             crit_range=[18,19,20], crit_mult=2),
                         #Attack(atk=9, dmg_roll=DamageRoll.fromString("1d6+5"),
                         #    crit_range=[18,19,20], crit_mult=2), # Hasted MH
                         Attack(atk=9, dmg_roll=DamageRoll.fromString("1d6+4"),
                             crit_range=[20,], crit_mult=3), ]) # OH should not be hasted
