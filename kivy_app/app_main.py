############################################################################
# NOTE: DO NOT RUN THIS FILE DIRECTLY
#   Run main.py in the IBC base directory
############################################################################
# IBC import
from model import Character, Weapon, Attack, DamageRoll, Buff

import os
import imp
import time
import textwrap
import json
from urllib2 import urlopen, Request
from copy import copy

# Kivy Imports

import kivy
kivy.require('1.7.0')

from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')

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
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty,StringProperty,ListProperty
from kivy.event import EventDispatcher


from data_model_wrapper import UI_DataModel

this_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep
Builder.load_file(this_dir + 'tabs.kv')



class CharacterUIWrapper(UI_DataModel):
    _model_class = Character


class CDM(object):
    """Character Data Mixin Object (to share character data across all classes
    and tabs that make up the application)"""
    c = Character()
    uic = CharacterUIWrapper()
    possible_buffs_list = []
    IBC_def = []
    IBC_id = []

    @classmethod
    def build_character_from_file(cls):
        """Read in a character from a .py file"""
        # Read in Henri
        filename = this_dir + '..' + os.sep + 'Henri.py'
        char_def = imp.load_source('char_def', filename)
        c = char_def.c
        pbl = char_def.possible_buffs_list

        # Put him in the code editor
        with open(filename) as f:
            cls.IBC_def.append(f.read())

        # Set Henri as the system-wide character
        cls.set_character(c, pbl)
    @classmethod
    def build_character(cls, IBC_id=0):
        # Read Henri from website
        r = urlopen(r"http://genericlifeform.pythonanywhere.com/IBC/api/v1.0/characters/%s"%IBC_id)
        r = json.load(r)
        try:
            IBC_def = r['def']
            success = cls._apply(IBC_def)
        except Exception, e:
            print "UNABLE TO READ WEBSITE: REading from file"
            cls.build_character_from_file()
            cls.IBC_id.append(-1)
        else:
            if not success:
                print ">>>>>>>APPLY DID NOT WORK!<<<<<<"
            else:
                cls.IBC_id.append(r['id'])
                return True


    @classmethod
    def set_character(cls, character, possible_buffs_list):
        cls.c = character
        cls.uic._model = cls.c
        cls.possible_buffs_list = possible_buffs_list

    def _build_post(self, url, data):
        """Create a JSON paylod of dictionary and post"""

        s = "Unable to post new data to website"

        try:
            payload = json.dumps(data)
            header = {'Content-Type': 'application/json'}
            print url
            print '='*20
            print payload
            req = Request(url, payload, header)
            response = urlopen(req)
            print response
            if response.getcode() == 201:
                return json.loads(response.read())
        except Exception, e:
            s += '\nERROR: ' + str(e)
        PopupOk(s, "Posting Error")

    @classmethod
    def _apply(cls, code):
        # Set up exectuion environment
        from model import *
        env = locals().copy()

        ptitle = "Invalid Character Definition"
        try:
            exec(code, env)
        except Exception, e:
            PopupOk("Unable to run code:\n%s\nCode was not saved"%e, ptitle)
            return False
        c = env.get('c', None)
        pbl = env.get('possible_buffs_list', None)
        if c is None:
            PopupOk("Unable to find a character.  Must be saved in "
                    "varialbe 'c'\nCode was not saved"%e, ptitle)
            return False
        if pbl is None:
            PopupOk("Unable to find a possible_buffs_list.  Must be saved in "
                    "varialbe 'possible_buffs_list'\nCode was not saved"%e,
                    ptitle)
            return False

        # Update the character
        cls.set_character(c, pbl)
        cls.IBC_def.append(code)
        return True

    @classmethod
    def build_character_default(cls):
        """Construct a character to play with"""
        ########
        # BUILD HENRI (sort of)
        #######
        c = Character()
        c.base.str_score = 19
        c.base.dex_score = 12
        c.base.con_score = 13
        c.base.cha_score = 14

        c.BAB = 5

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

        cls.c = c

        # Buffs
        cls.possible_buffs_list = \
            [Buff('Favored Enemy (Human)',4,4),
             Buff('Favored Enemy (Monstrous Humanoid)',2,2),
             Buff('Bless',atk_mod=1),
             Buff('Prayer',atk_mod=1,dmg_mod=1),
             Buff('Sickened',atk_mod=-2,dmg_mod=-2)]

        bulls_strength = Buff("Bull's Strength")
        bulls_strength.str_score = 4
        cls.possible_buffs_list.append(bulls_strength)

        # Update UIC Model
        cls.uic._model = cls.c

class SubGridLayout(GridLayout):
    pass
##    def __init__(self, **kwargs):
##        if len(self.children) > 0:
##            # Set height to be the height of all my children
##            h = self.children[0].height*(len(self.children)/self.cols)
##        else:
##            h = 0
##        kwargs['height'] = h
##        super(SubGridLayout, self).__init__(**kwargs)

class AbilityScoreLabel(Label):
    pass


class AbilityScore(AbilityScoreLabel, Button):
    def on_long_press(self, *args, **kwargs):
        # Find the character object
        c = self.get_root_window().children[0].c
        with c.audit_context:
            key = getattr(self, '_audit_prop', None)
            if key is None:
                msg = "Unable to audit.  No Audit property found."
            else:
                msg = str(c[key])
        PopupAudit(msg, key)


def PopupOk(text, title='', btn_text='Continue'):
    btnclose = Button(text=btn_text, size_hint_y=None, height='50sp')
    content = BoxLayout(orientation='vertical')
    content.add_widget(Label(text=text))
    content.add_widget(btnclose)
    p = Popup(title=title, content=content, size=('300dp', '300dp'),
                size_hint=(None, None))
    btnclose.bind(on_release=p.dismiss)
    p.open()

def PopupAudit(text, key):
    btnclose = Button(text='Continue', size_hint_y=None, height='50sp')
    content = BoxLayout(orientation='vertical')
    lbl = TextInput(text=text, font_size='12sp', auto_indent=True,
            readonly=True, disabled=True,
            font_name='fonts'+os.sep+'DroidSansMono.ttf')
    content.add_widget(lbl)
    content.add_widget(btnclose)
    p = Popup(title='Audit of "%s"' % key, content=content,
                #size=('300dp', '300dp'),
                size_hint=(.95, .75))
    btnclose.bind(on_release=p.dismiss)
    p.open()
    #PopupOk(text, "Audit of %s" % key)


class StatsTab(TabbedPanelItem,CDM):
    def __init__(self, c, **kwargs):
        super(StatsTab, self).__init__(**kwargs)
        self.c = c                             # Character object
        self.uic._model = self.c               # Bind it all together!

    @CDM.uic.update
    def test_button_press(self):
        #print '='*30
        #print "UIC.str was: %s" % self.uic.str
        self.c.base.str_score = 25
        #print "Str is now: %d" % self.c.str
        #print "UIC.str is now: %s" % self.uic.str

    @CDM.uic.update
    def update_weapon(self, hand, weapon_text):
        # Find the weapon that matches the text past
        if weapon_text == 'None':
            wep = None
        else:
            weaps_as_text = [str(a) for a in self.c.equipment]
            idx = weaps_as_text.index(weapon_text)
            wep = self.c.equipment[idx]
        if hand == 'mh':
            self.c.equipment.main_hand = wep
        elif hand == 'oh':
            self.c.equipment.off_hand = wep
        else:
            raise ValueError("Unknown hand %s" % hand)



class AttacksTab(TabbedPanelItem,CDM):
    def __init__(self, c, buffs, **kwargs):
        super(AttacksTab, self).__init__(**kwargs)
        self.c = c      # Character object
        self.uic._model = self.c               # Bind it all together!
        self.buffs = buffs

        # Bind ourselves to when the attacks update in the uic of the parent
        self.uic.bind(attacks=self.onAttacksUpdated)

        # Build GUI
        self.build_buffs()
        self.build_attacks()



    def build_buffs(self):
        # Buffs
        buffs = self.ids['buffs']
        buffs.clear_widgets()
        buffs.bind(minimum_height=buffs.setter('height'))
        pbl = sorted(self.buffs, key=lambda x: x.name)
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
            l = ToggleButton(text=b.name, size_hint=(1, None), height='50sp')
            l._buff = b
            l.bind(on_press = self.update_buffs)

            buffs.add_widget(l)


    def build_attacks(self):
        # Attacks
        attacks = self.ids['attacks']
        attacks.clear_widgets()
        attacks.bind(minimum_height=attacks.setter('height'))
        self.attack_labels = []

        for n, a in enumerate(self.c.attacks):
            attacks.add_widget(AttackRow(n, self.c, self.uic))

    def onAttacksUpdated(self, *args):
        if len(self.ids['attacks'].children) != len(self.c.attacks):
            #print "Rebuilding all attacks"
            self.build_attacks()
        else:
            #print "Same number of attacks, no need to rebuild"
            #print self.uic.attacks
            pass


    @CDM.uic.update
    def update_buffs(self, button):
        if button.state == 'down':
            # Add buff to character buff list
            self.c.buffs.append(button._buff)
        else:
            # Remove buff from character buff list
            self.c.buffs.remove(button._buff)

class AttackRow(BoxLayout):
    def __init__(self, atkNum, character, parent_uic):
        super(AttackRow, self).__init__()
        self.c = character
        self.atkNum = atkNum
        self.parent_uic = parent_uic

        # Bind ourselves to when the attacks update in the uic of the parent
        parent_uic.bind(attacks=self.onAttacksUpdated)

        # Do inital population
        self.onAttacksUpdated()

    def onAttacksUpdated(self, *args):
        # Update atk and dmg values
        #print "Updating an attack row: %s" % str(args)
        try:
            attack = self.c.attacks[self.atkNum]
        except IndexError:
            # We must be a left over row.  Unbind us
            print "Cleaning up a binding"
            self.parent_uic.unbind(attacks=self.onAttacksUpdated)
            return

        self.ids['name'].text = attack.name
        self.ids['atk'].text = '+' + str(attack.atk)
        self.ids['dmg'].text = str(attack.dmg_roll)

    def show_roll(self):
        attack = self.c.attacks[self.atkNum]
        text = attack.roll()
        PopupOk(text, attack.name)
        print text

    def on_long_press(self, *args):
        attack = self.c.attacks[self.atkNum]
        with self.c.audit_context:
            assert self.c.audit
            msg = str(self.c.attacks[self.atkNum])
        PopupAudit(msg, attack.name)
        print "Trying to audit an attack"

class CountersTab(TabbedPanelItem):
    pass

class SkillsTab(TabbedPanelItem):
    pass

class FeatsTab(TabbedPanelItem):
    pass

class SpellsTab(TabbedPanelItem):
    pass

class CodeTab(TabbedPanelItem, CDM):

    def save_and_apply(self):
        code = self.ids.code.text
        if self._apply(code) == False:
            return

        # Save it off
        url = r"http://genericlifeform.pythonanywhere.com/IBC/api/v1.0/characters/%s"%self.IBC_id[-1]
        response = self._build_post(url, {'def': code})
        if response is not None:
            success = response.get('success', False)
        else:
            success = False
        if success:
            PopupOk("Character applied and saved successfully.",
                    "New Character Definiton Loaded")
        else:
            PopupOk("Character applied \n however did not save: \n%s." % response,
                    "New Character Definiton Loaded")

    def new_and_apply(self):
        code = self.ids.code.text
        if self._apply(code) == False:
            return

        url = r"http://genericlifeform.pythonanywhere.com/IBC/api/v1.0/characters"
        data = {'def': code}
        response = self._build_post(url, data)
        new_id = response.get('new_character_id', None)
        if new_id is not None:
            PopupOk("Character now on website with id %s" % new_id)
        else:
            PopupOk("Post successful? but bad response %s" % response)

    def open_IBC(self):
        if self.build_character(self.ids.IBC_id.text):
            self.on_press() # Update us
            PopupOk("Loaded new character successfully")
        else:
            PopupOk("Unable to load character with that id")

    def on_press(self, *args):
        # Update the code widget
        self.ids.code.text = self.IBC_def[-1]
        self.ids.IBC_id.text = str(self.IBC_id[-1])
        assert len(self.IBC_def) == len(self.IBC_id)

class IBC_tabs(TabbedPanel, CDM):
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
        self.add_widget(CodeTab())


class IBC_App(App):
    def build(self):
        return IBC_tabs(do_default_tab = False)

if __name__ == '__main__':
    IBC_App().run()