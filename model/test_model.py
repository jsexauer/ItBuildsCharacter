# Test Model


from model import (Character, Equipment, Weapon, Attack, DamageRoll,
                    Buff, Feat, auditable, AuditResult)

def assert_audit(audit_obj, true_value, msg=''):
    """Helper function to help asserting when value object abound"""
    if not isinstance(audit_obj, AuditResult):
        raise TypeError("First argument must be an AuditResult")
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

print "Climb skill: ", c.skills['Climb']
assert_audit(c.skills['Climb'], 4)

c.skills.detail['Climb'].ranks = 1
print "Climb skill with rank: ", c.skills['Climb']
assert_audit(c.skills['Climb'], 5)


c.rpg_class.skills['Climb'] = 3     # Make a class skill
print "Climb skill with class skill: ", c.skills['Climb']
assert_audit(c.skills['Climb'], 8)

chain_shirt.ACP = -2    # for testing only
print "Acrobatics (check ACP): ", c.skills['Acrobatics']
assert_audit(c.skills['Acrobatics'], 1)
chain_shirt.ACP = 0

c.rpg_class.hit_die = 10
c.lvl = 5
print "Hit Points: ", c.HP
assert_audit(c.HP, 49)

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

print "Hit Points (with toughness): ", c.HP
assert_audit(c.HP, 49+5)







########
# BUILD HENRI
#######
c = Character()
c.audit = True
c.base.str_score = 19
c.base.dex_score = 12
c.base.con_score = 13
c.base.cha_score = 14

c.BAB = 5

greatsword = Weapon("Greatsword",
                      Attack(atk=+0, dmg_roll=DamageRoll.fromString("2d6"),
                             crit_range=[19,20], crit_mult=2, two_handed=True))
c.equipment.main_hand = greatsword
attacks = c.attacks
