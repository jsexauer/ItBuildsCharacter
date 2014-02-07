# IBC import
from model import Character, Weapon, Attack, DamageRoll, Buff

import os
from copy import copy

# Kivy Imports

import kivy
kivy.require('1.7.0')

from kivy.config import Config
Config.set('graphics', 'width', '540')
Config.set('graphics', 'height', '960')

from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.checkbox import CheckBox
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.properties import ObjectProperty,StringProperty
from kivy.event import EventDispatcher


this_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep
Builder.load_file(this_dir + 'tabs.kv')

class StringObjectProxy(object):
    def __init__(self, parent=Character()):
        self.__parent = parent
    def __getattr__(self, key):
        print "Getting %s" % key
        if key == '__parent':
            return self.__parent
        else:
            val = str(getattr(self.__parent, key))
            print "   returning %s (type: %s)" % (val, type(val))
            return val
    def __getitem__(self, key):
        return str(elf.__parent[key])



global_c = Character()

class UIC_BuilderMeta(type):
    def __new__(meta, name, bases, dct):
        c = Character()     # To find all the attributes
        for attr in dir(c):
            if not attr.startswith('_'):
                print "Making attribute %s" % attr
                dct[attr] = StringProperty('INIT')
        return super(UIC_BuilderMeta, meta).__new__(meta, name, bases, dct)

class UIC_Builder(EventDispatcher):
    __metaclass__ = UIC_BuilderMeta
    def __init__(self):
        #self.__c = Character()
        pass
    def __getattribute__(self, key):
        print ">> Trying to get %s" % key
        if key in dir(EventDispatcher):
            print "    Pushing up to base class"
            return EventDispatcher.__getattribute__(self, key)
        #elif key in ('__c', '_UIC_Builder__c'):
        #    return object.__getattribute__(self, key)
        else:
            print "    INTERCEPTED!"
            val = str(getattr(global_c, key))
            print "  val is %s" % val
            setattr(self, key, val)
            return EventDispatcher.__getattribute__(self, key)



example = UIC_Builder()
print "Hmmm"


class StatsTab(TabbedPanelItem):
    uic = ObjectProperty(UIC_Builder())
    str_test = StringProperty()
    def __init__(self, c, **kwargs):
        super(StatsTab, self).__init__(**kwargs)
        self.c = global_c                             # Character object
        #self.uic.__c = self.c                   # Bind it all together!

        # Build GUI
        self.refresh_gui()

    def on_press(self):
        self.refresh_gui()

    def refresh_gui(self):
        pass
        #for attr in ['str','int','dex','wis','con','cha']:
        #    lbl = self.ids[attr]
        #    lbl.text = attr.capitalize() + ' ' + str(self.c[attr])



    def test_button_press(self):
        print '='*30
        print "UIC.str was: %s" % self.uic.str
        self.c.base.str_score = 25
        print "Str is now: %d" % self.c.str
        print "UIC.str is now: %s" % self.uic.str
        #print "ID of uic.__c is %s" % id(self.uic.__c)
        #print "Type of c is %s" % id(self.c)
        self.refresh_gui()



class AttacksTab(TabbedPanelItem):
    def __init__(self, c, buffs, **kwargs):
        super(AttacksTab, self).__init__(**kwargs)
        self.c = c      # Character object
        self.buffs = buffs

        # Build GUI
        self.refresh_gui()

    def on_press(self):
        self.refresh_gui()

    def refresh_gui(self):
        # Buffs
        buffs = self.ids['buffs']
        buffs.clear_widgets()
        buffs.bind(minimum_height=buffs.setter('height'))
        for b in self.buffs:
##            l = BoxLayout(orientation='horizontal', padding=5,
##                            size_hint=(1, None), height=30, width=320)
##
##            cb = CheckBox(size_hint=(None, None), size=(50,50))
##            cb._buff = b
##            cb.bind(active = self.update_buffs)
##            l.add_widget(cb)
##
##            name = Label(halign='left', size_hint=(None,1), valign='middle')
##            name.bind(texture_size=name.setter('size'))
##            name.text = b.name
##            l.add_widget(name)
            l = ToggleButton(text=b.name, size_hint=(1, None), height=50)
            l._buff = b
            l.bind(on_press = self.update_buffs)

            buffs.add_widget(l)

        self.refresh_attacks()

    def refresh_attacks(self):
        # Attacks
        attacks = self.ids['attacks']
        attacks.clear_widgets()
        attacks.bind(minimum_height=attacks.setter('height'))
        for a in self.c.attacks:
            l = BoxLayout(orientation='horizontal', padding=5,
                            size_hint=(1, None), height=50)

            name = Label()
            name.text = a.name
            name.size_hint = (.5, 1)
            name.halign = 'left'
            l.add_widget(name)

            atk = Label()
            atk.text = '+' + str(a.atk)
            atk.size_hint = (.1, 1)
            l.add_widget(atk)

            dmg = Label()
            dmg.text = str(a.dmg_roll)
            dmg.size_hint = (.2, 1)
            l.add_widget(dmg)

            roll = Button()
            roll.text = "Roll"
            roll._attack = a
            roll.bind(on_press=self.show_roll)
            roll.size_hint = (.2, 1)
            l.add_widget(roll)

            attacks.add_widget(l)

    def update_buffs(self, button):
        if button.state == 'down':
            # Add buff to character buff list
            self.c.buffs.append(button._buff)
        else:
            # Remove buff from character buff list
            self.c.buffs.remove(button._buff)
        self.refresh_attacks()

    def show_roll(self, button):
        attack = button._attack
        text = attack.roll()
        btnclose = Button(text='Continue', size_hint_y=None, height='50sp')
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=text))
        content.add_widget(btnclose)
        p = Popup(title=attack.name, content=content, size=('300dp', '300dp'),
                    size_hint=(None, None))
        btnclose.bind(on_release=p.dismiss)
        p.open()
        print text


class CountersTab(TabbedPanelItem):
    pass

class SkillsTab(TabbedPanelItem):
    pass

class FeatsTab(TabbedPanelItem):
    pass

class SpellsTab(TabbedPanelItem):
    pass



class IBC_tabs(TabbedPanel):
    def __init__(self, **kwargs):
        super(IBC_tabs, self).__init__(**kwargs)

        self.build_character()

        #self.console = ConsoleWidget(self)
        tab1 = StatsTab(self.c)
        self.add_widget(tab1)
        tab2 = AttacksTab(self.c, self.possible_buffs_list)
        self.add_widget(tab2)
        self.add_widget(CountersTab())
        self.add_widget(SkillsTab())
        self.add_widget(FeatsTab())
        self.add_widget(SpellsTab())

    def build_character(self):
        """Construct a character to play with"""
        ########
        # BUILD HENRI
        #######
        c = Character()
        c.base.str_score = 19
        c.base.dex_score = 12
        c.base.con_score = 13
        c.base.cha_score = 14

        c.BAB = 16

        greatsword = Weapon("Greatsword",
                      Attack(atk=+0, dmg_roll=DamageRoll.fromString("2d6"),
                             crit_range=[19,20], crit_mult=2, two_handed=True))
        #c.equipment.main_hand = greatsword

        # Add in dual-wield for testing
        tidewater_cutless = Weapon("Tidewater Cuttless +1",
                      Attack(atk=+1, dmg_roll=DamageRoll.fromString("1d6+1"),
                             crit_range=[18,19,20], crit_mult=2))
        c.equipment.main_hand = tidewater_cutless
        masterwork_handaxe = Weapon("Masterwork Handaxe",
                              Attack(atk=1, dmg_roll=DamageRoll.fromString("1d6"),
                                     crit_range=[20,], crit_mult=3))

        c.equipment.off_hand = masterwork_handaxe

        self.c = c

        # Buffs
        self.possible_buffs_list = \
            [Buff('Favored Enemy (Human)',4,4),
             Buff('Favored Enemy (Monstrous Humanoid)',2,2),
             Buff('Bless',atk_mod=1),
             Buff('Prayer',atk_mod=1,dmg_mod=1),
             Buff('Sickened',atk_mod=-2,dmg_mod=-2)]*10


class IBC_App(App):
    def build(self):
        return IBC_tabs(do_default_tab = False)

if __name__ == '__main__':
    IBC_App().run()