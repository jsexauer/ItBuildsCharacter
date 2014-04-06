# Test Model (to be run with nose)
from math import floor

from nose.tools import assert_equals

from model import (Character, Equipment, Weapon, Attack, DamageRoll,
                    Buff, Feat, auditable, AuditResult)



class Wardrobe(object):
    """Set of sample test equipment"""
    def __init__(self):
        ### Armor
        self.chain_shirt = Equipment('Chain Shirt')
        self.chain_shirt.AC = 6
        self.full_plate = Equipment('Full Plate')
        self.full_plate.AC = 9
        self.full_plate.ACP = -6
        self.amulate = Equipment('Amulate of Natural Armor')
        self.amulate.natural_armor = 2
        self.buckler = Equipment('Buckler')
        self.buckler.AC = 1
        self.buckler.ACP = -1
        self.buckler.atk = -1

        ### Buffs
        self.greater_natural_armor_buff = Buff('Greater Natural Armor Buff')
        self.greater_natural_armor_buff.natural_armor = 4
        self.dodge_buff = Buff('Generic Dodge Buff')
        self.dodge_buff.dodge_bonus = 2
        self.greater_dodge_buff = Buff('Greater Dodge Buff')
        self.greater_dodge_buff.dodge_bonus = 4
        self.defl_buff = Buff('Generic Deflection Bonus')
        self.defl_buff.deflection_bonus = 2
        self.greater_defl_buff = Buff('Greater Deflection Bonus')
        self.greater_defl_buff.deflection_bonus = 4
        self.dex_buff = Buff('Generic Dex Buff')
        self.dex_buff.dex_score = 2

class TestCharacter(object):

    @classmethod
    def setUpAll(cls):
        cls.w = Wardrobe()

    def setUp(self):
        self.c = Character()
        self.attribute_under_test = None

        self.c.rpg_class.hit_die = 8

    def assertAttr(self, expected, attr_under_test=None):
        """Test attribute under test matches expected.  Default's to the
        class's attribute_under_test but can be optionally specified"""
        if attr_under_test is None:
            assert self.attribute_under_test is not None, \
                         "Set attribute_under_test before using assertAttr"
            attr_under_test = self.attribute_under_test

        a = getattr(self.c, attr_under_test)

        try:
            assert_equals(a, expected)
        except AssertionError, e:
            new_msg = e.message
            with self.c.audit_context:
                new_msg += '\nAttribute Audit:\n%s' % \
                             getattr(self.c, attr_under_test)
            raise AssertionError(new_msg)

 ########### DEFENSIVE ATTRIBUTES ############################################
    def test_AC(self):
        self.attribute_under_test = 'AC'

        # Starting AC should be 10
        self.assertAttr(10)

        # Negative Dex modifier (-1)
        self.c.base.dex_score = 8
        self.assertAttr(9)

        # Add chain shirt (+6)
        self.c.equipment.append(self.w.chain_shirt)
        self.assertAttr(15)

        # Natural armor (+2)
        self.c.equipment.append(self.w.amulate)
        self.assertAttr(17)

        # Dodge Bonus (+2)
        self.c.buffs.append(self.w.dodge_buff)
        self.assertAttr(19)

        # Deflection Bonus (+2)
        self.c.buffs.append(self.w.defl_buff)
        self.assertAttr(21)

        # Dex Bonus from buff (+2 dex -> +1 AC)
        self.c.buffs.append(self.w.dex_buff)
        self.assertAttr(22)

        # Remove amulate (-2)
        self.c.equipment.remove(self.w.amulate)
        self.assertAttr(20)

        # Remove buffs (-5)
        self.c.buffs.clear()
        self.assertAttr(15)

    def test_AC_stacking_dodge(self):
        self.attribute_under_test = 'AC'

        self.assertAttr(10)

        # Dodge bonuses **DO** stack
        self.c.buffs.append(self.w.dodge_buff)
        self.assertAttr(12)
        self.assertAttr(2, 'dodge_bonus')

        self.c.buffs.append(self.w.greater_dodge_buff)
        self.assertAttr(16)
        self.assertAttr(6, 'dodge_bonus')

    def test_AC_stacking_defl(self):
        self.attribute_under_test = 'AC'

        self.assertAttr(10)

        # Deflection bonuses do not stack (takes bigger)
        self.c.buffs.append(self.w.defl_buff)
        self.assertAttr(12)
        self.assertAttr(2, 'deflection_bonus')

        self.c.buffs.append(self.w.greater_defl_buff)
        self.assertAttr(14)
        self.assertAttr(4, 'deflection_bonus')

    def test_AC_stacking_natural_armor(self):
        self.attribute_under_test = 'AC'

        self.assertAttr(10)

        # Natural Armor bonuses do not stack (takes bigger)
        self.c.equipment.append(self.w.amulate)
        self.assertAttr(12)
        self.assertAttr(2, 'natural_armor')

        self.c.buffs.append(self.w.greater_natural_armor_buff)
        self.assertAttr(14)
        self.assertAttr(4, 'natural_armor')

    def test_dodge_bonus(self):
        self.attribute_under_test = 'dodge_bonus'

        self.assertAttr(0)

        self.c.equipment.append(self.w.chain_shirt)
        self.assertAttr(0)

        self.c.equipment.append(self.w.amulate)
        self.assertAttr(0)

        self.c.buffs.append(self.w.dex_buff)
        self.assertAttr(0)

        self.c.buffs.append(self.w.defl_buff)
        self.assertAttr(0)

        self.c.buffs.append(self.w.dodge_buff)
        self.assertAttr(2)

        self.c.buffs.clear()
        self.assertAttr(0)

    def test_defl_bonus(self):
        self.attribute_under_test = 'deflection_bonus'

        self.assertAttr(0)

        self.c.equipment.append(self.w.chain_shirt)
        self.assertAttr(0)

        self.c.equipment.append(self.w.amulate)
        self.assertAttr(0)

        self.c.buffs.append(self.w.dex_buff)
        self.assertAttr(0)

        self.c.buffs.append(self.w.defl_buff)
        self.assertAttr(2)

        self.c.buffs.append(self.w.dodge_buff)
        self.assertAttr(2)

        self.c.buffs.clear()
        self.assertAttr(0)

    def test_natural_armor_bonus(self):
        self.attribute_under_test = 'natural_armor'

        self.assertAttr(0)

        self.c.equipment.append(self.w.chain_shirt)
        self.assertAttr(0)

        self.c.equipment.append(self.w.amulate)
        self.assertAttr(2)

        self.c.buffs.append(self.w.dex_buff)
        self.assertAttr(2)

        self.c.buffs.append(self.w.defl_buff)
        self.assertAttr(2)

        self.c.buffs.append(self.w.dodge_buff)
        self.assertAttr(2)

        self.c.buffs.clear()
        self.assertAttr(2)

        self.c.equipment.clear()
        self.assertAttr(0)

    def test_ACP(self):
        self.attribute_under_test = 'ACP'

        self.assertAttr(0)

        self.c.equipment.append(self.w.full_plate)
        self.assertAttr(-6)

        self.c.equipment.append(self.w.buckler)
        self.assertAttr(-7)

        self.c.equipment.remove(self.w.full_plate)
        self.assertAttr(-1)


    def check_HP_per_level(self, func, inital_hp, hp_per_lvl):
        """Used by several test generator functions"""
        self.attribute_under_test = 'HP'

        # Apply function which modifies character in some way
        func(self.c)

        self.assertAttr(inital_hp)

        # Run us through the first five levels
        for lvl in xrange(1,5):
            self.c.lvl = lvl+1
            self.assertAttr(inital_hp + lvl*hp_per_lvl)

    def test_HP_per_level_generator(self):

        hit_dice_combos = {
            # Hit Die: HP per level
            6:  4,
            8:  5,
            10: 6,
            12: 7,
        }

        for hd, hplvl in hit_dice_combos.iteritems():
            inithp = hd + 1     # +1 for favored class
            hplvl += 1          # +1 for favored class
            def _vary_hitdie(c):
                c.rpg_class.hit_die = hd
            yield self.check_HP_per_level, _vary_hitdie, inithp, hplvl

    def test_HP_with_con_generator(self):

        # Assume 8 hit die character (defined in setup)

        con_combos = {
            # Con: HP per level (6 for 8 hit die (5 + 1 for fav class); then mod for con)
            8:  6-1,
            9:  6-1,
            10: 6+0,
            11: 6+0,
            12: 6+1,
            13: 6+1,
            18: 6+4,
        }

        for con, hplvl in con_combos.iteritems():
            inithp = 9 + int((con-10)/2)       # 8 + 1 (fav class) + con_mod
            def _vary_con(c):
                c.base.con_score = con
            yield self.check_HP_per_level, _vary_con, inithp, hplvl


 ########### OFFESNIVE ATTRIBUTES ############################################
    def test_mh_melee_atk_bonus(self):
        assert False

    def test_oh_melee_atk_bonus(self):
        assert False

    def test_ranged_atk_bonus(self):
        assert False

    def test_attacks(self):
        assert False

    def test_weapons(self):
        assert False















###############################################################################
'''
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
'''