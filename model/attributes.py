from common import *



def _makeModChar(_attr):
    def _calcModChar(self):
        _formula = '(score-10)/2'
        score = self[_attr+'_score']
        return (score - 10) // 2
    return _calcModChar

def _makeMod(_attr):
    def _calcMod(self):
        _formula = '(score)/2'
        score = self[_attr+'_score']
        return (score) // 2
    return _calcMod

def _makeScore(_attr):
    _attr_score = _attr+'_score'
    def _calcAttrScore(self):
        base = self.base[_attr_score]
        racial = self.race[_attr_score]
        buffs, _buffs = has_sum(self.buffs, _attr_score)
        equipment, _eqp = has_sum(self.equipment, _attr_score)
        return (base + racial + _buffs + _eqp)
    return _calcAttrScore

def _makeSave(_save, _attr):
    def _calcSave(self):
        base = self.base[_save]
        locals()[_attr] = self[_attr]   # Con/Ref/Dex modifier
        buffs, _buffs = has_sum(self.buffs, _save)
        equipment, _eqp = has_sum(self.equipment, _save)
        rpg_class = self.rpg_class[_save]
        return base + locals()[_attr] + _buffs + _eqp + rpg_class
    return _calcSave


class AttributesMeta(type):
    def __new__(cls, name, bases, attrdict):
        _abilities = attrdict.get('_abilities', {})
        for k in _abilities:
            attrdict[k] = auditable(_makeMod(k))

        _scores = attrdict.get('_scores', {})
        for k in _scores:
            attrdict[k] = 0

        _saves = attrdict.get('_saves', {})
        for k, v in _saves.iteritems():
            attrdict[k] = 0

        return super(AttributesMeta, cls).__new__(cls, name, bases, attrdict)

class Attributes(Struct):
    __metaclass__ = AttributesMeta
    _abilities = ['str', 'dex', 'con', 'int', 'wis', 'cha']
    _scores = ['HP', 'AC', 'natural_armor', 'deflection_bonus', 'dodge_bonus',
               'atk', 'dmg_roll', 'ACP']
    _saves = {'fort': 'con',
              'ref':  'dex',
              'will': 'wis'
             }

    def __init__(self, default_value=0):
        for k in self._abilities:
            self[k+'_score'] = default_value
        skills = ['Acrobatics','Appraise','Bluff','Climb','Craft (XXXX)',
                'Diplomacy','Disable Device','Disguise','Escape Artist',
                'Handle Animal','Heal','Intimidate','Knowledge (arcana)',
                'Knowledge (dungeoneering)','Knowledge (engineering)',
                'Knowledge (geography)','Knowledge (history)',
                'Knowledge (local)','Knowledge (nature)','Knowledge (nobility)',
                'Knowledge (planes)','Knowledge (religion)','Linguistics',
                'Perception','Perform (act)','Profession (XXXX)',
                'Ride','Sense Motive','Sleight of Hand','Spellcraft',
                'Stealth','Survival','Swim','Use Magic Device',
                ]
        self.skills = {}
        for s in skills:
            self.skills[s] = 0

        self.audit = False

    def __add__(self, other):
        assert isinstance(other, Attributes)
        added = Attributes()
        for attr in self._abilities:
            added[attr+'_score'] = self[attr+'_score'] + other[attr+'_score']
        return added

    def __str__(self):
        # Display only non-zero values of self
        s = []
        profanity = ()
        for k in dir(self):
            if k in profanity: continue
            v = getattr(self, k)
            if type(v) is int and v != 0:
                s.append("{0:s}: {1:+d}".format(k,v))
        if len(s) == 0:
            return ''
        else:
            return '(%s)' % ', '.join(s)

