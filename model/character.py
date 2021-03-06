from copy import copy

from common import *
from attributes import (Attributes, AttributesMeta, _makeMod, _makeModChar,
                        _makeScore, _makeSave)

from warnings import warn

class Race(Attributes):
    pass


class CharacterList(list):
    """Base Class to create all the various lists for a character and ensure
       on apply statements are implemented"""
    def __init__(self, character):
        list.__init__(self)
        self._character = character

    def append(self, other):
        list.append(self, other)
        if hasattr(other, 'on_apply'):
            other.on_apply(self._character)

    def remove(self, item):
        if hasattr(item, 'on_apply'):
            raise NotImplementedError("Unwrapping complex items not done yet")
        list.remove(self, item)

    def pop(self, item):
        raise NotImplementedError("Use remove instead")

    def clear(self):
        for i in self[:]:
            self.remove(i)

class CharacterEquipmentList(CharacterList):
    @property
    def main_hand(self):
        return getattr(self, '_main_hand', None)
    @main_hand.setter
    def main_hand(self, value):
        self._main_hand = value
        if value not in self and value is not None:
            self.append(value)

    @property
    def off_hand(self):
        return getattr(self, '_off_hand', None)
    @off_hand.setter
    def off_hand(self, value):
        self._off_hand = value
        if value not in self and value is not None:
            self.append(value)

class CharacterFeatList(CharacterList):
    pass

class CharacterBuffList(CharacterList):
    pass

class CharacterSkillList(dict):
    def __init__(self, character):
        dict.__init__(self)
        #                name          atr   untrained  ACP
        skill_info = [  ('Acrobatics','dex',  True,     True),
                        ('Appraise','int',True,False),
                        ('Bluff','cha',True,False),
                        ('Climb','str',True,True),
                        ('Craft (XXXX)','int',True,False),
                        ('Diplomacy','cha',True,False),
                        ('Disable Device','dex',False,True),
                        ('Disguise','cha',True,False),
                        ('Escape Artist','dex',True,True),
                        ('Handle Animal','cha',False,False),
                        ('Heal','wis',True,False),
                        ('Intimidate','cha',True,False),
                        ('Knowledge (arcana)','int',False,False),
                        ('Knowledge (dungeoneering)','int',False,False),
                        ('Knowledge (engineering)','int',False,False),
                        ('Knowledge (geography)','int',False,False),
                        ('Knowledge (history)','int',False,False),
                        ('Knowledge (local)','int',False,False),
                        ('Knowledge (nature)','int',False,False),
                        ('Knowledge (nobility)','int',False,False),
                        ('Knowledge (planes)','int',False,False),
                        ('Knowledge (religion)','int',False,False),
                        ('Linguistics','int',False,False),
                        ('Perception','wis',True,False),
                        ('Perform (act)','cha',True,False),
                        ('Profession (XXXXXX)','wis',False,False),
                        ('Ride','dex',True,True),
                        ('Sense Motive','wis',True,False),
                        ('Sleight of Hand','dex',False,True),
                        ('Spellcraft','int',False,False),
                        ('Stealth','dex',True,True),
                        ('Survival','wis',True,False),
                        ('Swim','str',True,True),
                        ('Use Magic Device','cha',False,False),
                    ]

        for s in skill_info:
            args = list(s) + [character,]
            self[s[0]] = Skill(*args)
        self._inDetailMode = False

    def __getitem__(self, key):
        if self._inDetailMode:
            self._inDetailMode = False
            return dict.__getitem__(self,key)
        else:
            return dict.__getitem__(self,key).value

    @property
    def detail(self):
        # Return a version of myself where __getitem__ is just a normal return
        self._inDetailMode = True
        return self


class CharacterMeta(AttributesMeta):
    def __new__(cls, name, bases, attrdict):
        # Ability Modifiers use the 10 minus formula
        for k in Attributes._abilities:
            attrdict[k] = auditable(_makeModChar(k))
        # Ability scores are devrived instead of settable for a character
        _abilities = Attributes._abilities
        for k in _abilities:
            attrdict[k+'_score'] = auditable(_makeScore(k))

        # Saress are devrived instead of settable for a character
        _saves = Attributes._saves
        for k, v in _saves.iteritems():
            attrdict[k] = auditable(_makeSave(k, v))

        return super(CharacterMeta, cls).__new__(cls, name, bases, attrdict)

class Character(Attributes):
    __metaclass__ = CharacterMeta
    def __init__(self):
        self.audit = False
        self.base = Attributes(10)
        self.race = Race()
        self.buffs = CharacterBuffList(self)
        self.equipment = CharacterEquipmentList(self)
        self.feats = CharacterFeatList(self)
        self.size_mod = 0
        self.BAB = 0
        # Alias attack as BAB
        self.atk = self.BAB
        self.lvl = 1
        self.name = "Unknown"
        self.rpg_class = RPGClass()

        self.skills = CharacterSkillList(self)

    @auditable
    def AC(self):
        """Armor Class"""
        base = 10
        equipment, _eqp = has_sum(self.equipment, 'AC')
        buffs, _buffs = has_sum(self.buffs, 'AC')
        dex = self.dex
        natural_armor = self.natural_armor
        deflection_bonus = self.deflection_bonus
        dodge_bonus = self.dodge_bonus
        size_mod = self.size_mod
        return (base + _eqp + dex + natural_armor + deflection_bonus +
                  dodge_bonus + size_mod + _buffs)

    @auditable
    def touch_AC(self):
        base = 10
        dex = self.dex
        deflection_bonus = self.deflection_bonus
        dodge_bonus = self.dodge_bonus
        size_mod = self.size_mod
        return (base + dex + deflection_bonus + dodge_bonus + size_mod)

    @auditable
    def flatfooted_AC(self):
        # Everything except dex
        base = 10
        equipment, _eqp = has_sum(self.equipment, 'AC')
        natural_armor = self.natural_armor
        deflection_bonus = self.deflection_bonus
        dodge_bonus = self.dodge_bonus
        size_mod = self.size_mod
        return (base + _eqp + natural_armor + deflection_bonus +
                  dodge_bonus + size_mod)

    @auditable
    def deflection_bonus(self):
        # Deflection bonuses do not stack
        _formula = "max(buffs, equipment)"
        buffs, _buffs = has_max(self.buffs, 'deflection_bonus')
        equipment, _eqp = has_max(self.equipment, 'deflection_bonus')
        return max(_buffs, _eqp)

    @auditable
    def dodge_bonus(self):
        # Dodge bonus _does_ stack
        buffs, _buffs = has_sum(self.buffs, 'dodge_bonus')
        equipment, _eqp = has_sum(self.equipment, 'dodge_bonus')
        return _buffs + _eqp

    @auditable
    def natural_armor(self):
        _formula = "max(buffs, equipment)"
        buffs, _buffs = has_max(self.buffs, 'natural_armor')
        equipment, _eqp = has_max(self.equipment, 'natural_armor')
        return max(_buffs, _eqp)

    @auditable
    def ACP(self):
        equipment, _eqp = has_sum(self.equipment, 'ACP')
        return _eqp

    @auditable
    def HP(self):
        # Assume we're taking the PFS hp values and always favored class
        _pfs_hp_map = {6: 4, 8:5, 10:6, 12:7, 0:-99999}
        _formula = ("hit_die + (level-1)*hp_per_level + con*level + "
                    "favored_class + feats")
        hit_die = self.rpg_class.hit_die
        hp_per_level = _pfs_hp_map[self.rpg_class.hit_die]
        level = self.lvl
        feats, _feats = has_sum(self.feats, 'HP')
        favored_class = self.lvl
        con = self.con
        return (hit_die + (level-1)*hp_per_level + _feats +
                con*level + favored_class)


    @auditable
    def mh_melee_atk_bonus(self):
        _formula = "For each attack..."
        # Figure out all the attacks
        _a = [self.BAB,]
        while _a[-1] > 0:
            _a.append(_a[-1]-5)
        if self.BAB > 0:
            # At 0 BAB, we'll remove ourselves if we're not careful
            _a = _a[:-1]
        _ans = []
        for _aa in _a:
            self._mh_single_atk__BAB = _aa
            _ans.append(self._mh_single_atk)
        self._mh_single_atk__BAB = None
        return _ans
    @auditable
    def _mh_single_atk(self):
        BAB = self._mh_single_atk__BAB
        str = self.str
        size = self.size_mod
        buffs, _buffs = has_sum(self.buffs, 'atk')

        if self.equipment.off_hand is not None:
            # Apply debuff that affects
            TwoWeaponFighting = -4                         # Assume light weapon
            _twf = -4
            TwoWeaponFightingFeats, _twf2 = has_sum(self.feats, 'twf_mh')
        else:
            _twf = 0
            _twf2 = 0

        return BAB+str+size+_buffs+_twf+_twf2

    @auditable
    def oh_melee_atk_bonus(self):
        _formula = "For each attack..."
        if self.equipment.off_hand is None:
            return []
        # Figure out all the attacks
        _a = [self.BAB,]

        _twf_feat, _twf_sum = has_sum(self.feats, 'twf_oh')
        if len(_twf_feat) == 1:
            _twf_feat = _twf_feat[0]
        else:
            _twf_feat = None

        # Build iteratives (requires Improved TWF (ie, twf_oh2)
        # and Greater TWF (ie, twf_oh3)
        if _twf_feat and getattr(_twf_feat, 'twf_oh2', False):
            _a.append(_a[-1]-5)
        if _twf_feat and getattr(_twf_feat, 'twf_oh3', False):
            _a.append(_a[-1]-5)

        #if self.BAB > 0:
        #    # At 0 BAB, we'll remove ourselves if we're not careful
        #    _a = _a[:-1]
        _ans = []
        for _aa in _a:
            self._oh_single_atk__BAB = _aa
            _ans.append(self._oh_single_atk)
        self._oh_single_atk__BAB = None
        return _ans
    @auditable
    def _oh_single_atk(self):
        BAB = self._oh_single_atk__BAB
        str = self.str
        size = self.size_mod
        buffs, _buffs = has_sum(self.buffs, 'atk')
        # Apply debuff that affects
        TwoWeaponFighting = -8                             # Assume light weapon
        _twf = -8
        TwoWeaponFightingFeats, _twf2 = has_sum(self.feats, 'twf_oh')
        return BAB+str+size+_buffs+_twf+_twf2



    @auditable
    def ranged_atk_bonus(self):
        _formula = "For each attack..."
        # Figure out all the attacks
        _a = [self.BAB,]
        while _a[-1] > 0:
            _a.append(_a[-1]-5)
        if len(_a) > 1:
            _a = _a[:-1]
        _ans = []
        for _aa in _a:
            self._rng_single_atk__BAB = _aa
            _ans.append(self._rng_single_atk)
        self._rng_single_atk__BAB = None
        return _ans
    @auditable
    def _rng_single_atk(self):
        BAB = self._rng_single_atk__BAB
        dex = self.dex
        size = self.size_mod
        buffs, _buffs = has_sum(self.buffs, 'atk')
        return BAB+dex+size+_buffs

    @auditable
    def attacks(self):
        # Values for display
        _formula = "Permuations of"

        _attacks = []
        main_hand = self.equipment.main_hand
        if main_hand is None:
            assert self.equipment.off_hand is None
            # We have no attacks, so create an "unarmed" attack
            main_hand = Weapon("Unarmed Strike",Attack(0,"1d3"))
            return _attacks

        if main_hand.atk.ranged:
            assert self.equipment.off_hand is None
            mh_attacks = self.ranged_atk_bonus
        else:
            mh_attacks = self.mh_melee_atk_bonus

        # Now do the real calculations
        assert isinstance(main_hand, Weapon)
        if main_hand.atk.two_handed:
            assert self.equipment.off_hand is None

        # Main Hand
        for _iter in range(len(mh_attacks)):
            _atk = copy(main_hand.atk)
            _atk.character = self
            _atk.iterative = int(_iter)
            _atk.name = "%s #%d" % (main_hand.name, _iter+1)
            _attacks.append(_atk)

        # Off Hand
        if self.equipment.off_hand is not None:
            off_hand = self.equipment.off_hand
            oh_attacks = self.oh_melee_atk_bonus
            for _iter in range(len(oh_attacks)):
                _atk = copy(off_hand.atk)
                _atk.is_oh = True
                _atk.character = self
                _atk.iterative = int(_iter)
                _atk.name = "%s #%d (OH)" % (off_hand.name, _iter+1)
                _attacks.append(_atk)

        # Create audit objects if necessary
        if self.audit:
            _new_attacks = []
            for _a in _attacks:
                _new_attacks.append(_a._as_audit_object)
            _attacks = _new_attacks

        return _attacks

    @property
    def main_hand(self):
        return self.equipment.main_hand
    @main_hand.setter
    def main_hand(self, new):
        warn("The perfered method of setting a weapon is using "
                "character.equipment.main_hand")
        self.equipment.main_hand = new

    @property
    def off_hand(self):
        return self.equipment.off_hand
    @off_hand.setter
    def off_hand(self, new):
        warn("The perfered method of setting a weapon is using "
                "character.equipment.off_hand")
        self.equipment.off_hand = new

    @property
    def weapons(self):
        ans = filter(lambda x: isinstance(x, Weapon), self.equipment)
        return ans



    @property
    def audit_context(self):
        """Create an auditable context"""
        class AuditContext(object):
            def __enter__(s):
                self.audit = True
            def __exit__(s, type, value, traceback):
                self.audit = False
        return AuditContext()
    #@property
    #def dmg(self):
    #    raise AttributeError("Characters do not have dmg. Use attacks instead.")

from rpg_objects import Weapon, Buff, RPGClass, Skill, Attack