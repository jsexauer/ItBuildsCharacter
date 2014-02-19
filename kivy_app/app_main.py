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
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty,StringProperty,ListProperty
from kivy.event import EventDispatcher
from kivy.metrics import sp as kivy_sp
from kivy.base import EventLoop


from data_model_wrapper import UI_DataModel
from model.audit import AuditResult

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
    update_hooks = []       # Functions to update when new model is loaded

    @classmethod
    def build_character_from_file(cls):
        """Read in a character from a .py file"""
        assert type(cls) is type, "Must call as classmethod"
        # Read in Henri
        filename = this_dir + '..' + os.sep + 'Clement.py'
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
        assert type(cls) is type, "Must call as classmethod"
        # Read Henri from website
        r = urlopen(r"http://genericlifeform.pythonanywhere.com/IBC/api/v1.0/characters/%s"%IBC_id)
        try:
            r = json.load(r)
            IBC_def = r['def']
            success = cls._apply(IBC_def)
        except Exception, e:
            print "UNABLE TO READ WEBSITE: REading from file"
            print e
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
        assert type(cls) is type, "Must call as classmethod"
        cls.c = character
        cls.uic._model = cls.c
        cls.possible_buffs_list = possible_buffs_list

        # Call everyone we're supposed to update when we change everything
        for func in cls.update_hooks:
            func()

        print "Master Character id is: %d" % id(cls.c)

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
        assert type(cls) is type, "Must call as classmethod"
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
        assert type(cls) is type, "Must call as classmethod"
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
            try:
                key = getattr(self, '_audit_prop')
            except KeyError:
                msg = None
                key = self.text
            else:
                msg = c[key]
        PopupAudit(msg, key)

class ScrollableText(BoxLayout):
    text = StringProperty('')
    def go_top(self, *args):
        print "IN GO TOP"
        self.ids.text_input.cursor = (0,-5)
    def go_up(self):
        a = self.ids.text_input.cursor
        pos = (a[0], a[1]-3)
        print pos
        self.ids.text_input.cursor = pos
    def go_down(self):
        a = self.ids.text_input.cursor
        pos = (a[0], a[1]+3)
        self.ids.text_input.cursor = pos

def PopupOk(text, title='', btn_text='Continue', input=None):
    btnclose = Button(text=btn_text, size_hint_y=None, height='50sp')
    content = BoxLayout(orientation='vertical')
    p = Popup(title=title, content=content, size=('300dp', '300dp'),
                size_hint=(None, None))
    content.add_widget(Label(text=text))
    if input is not None:
        ti = TextInput(height='50sp', font_size='50sp', input_type=input)
        content.add_widget(ti)
        def _on_d(*args):
            p.is_visable = False
        p.bind(on_dismiss=_on_d)
        p.is_visable = True

    content.add_widget(btnclose)

    btnclose.bind(on_release=p.dismiss)
    p.open()
    if input is not None:
        def check_closed(*args):
            if  p.is_visable:

            EventLoop.idle()
        return ti.text

def PopupAudit(audit_obj, key):
    def on_close(*args):
        def _on_close(*args):
            Window.rotation = 0
        Clock.schedule_once(_on_close, .25)

    assert isinstance(audit_obj, AuditResult) or audit_obj is None
    if audit_obj is None:
        text = "No audit attribute found for %s" % key
    else:
        text = str(audit_obj)
    btnclose = Button(text='Continue', size_hint_y=None, height='50sp')
    content = BoxLayout(orientation='vertical')
##    lbl = TextInput(text=text, font_size='12sp', auto_indent=True,
##            readonly=True, disabled=True,
##            font_name='fonts'+os.sep+'DroidSansMono.ttf')
    lbl = ScrollableText(text=text)
    content.add_widget(lbl)
    content.add_widget(btnclose)
    p = Popup(title='Audit of "%s"' % key, content=content,
                #size=('300dp', '300dp'),
                size_hint=(.95, .75))
    btnclose.bind(on_release=p.dismiss)
    p.bind(on_open=lbl.go_top)
    # See if this is a pretty long audit, so we will display long ways
    if max([len(a) for a in text.split('\n')]) > 30:
        p.bind(on_dismiss=on_close) and None
        p.size_hint = (.95, .95)
        Window.rotation = 90
    p.open()


class StatsTab(TabbedPanelItem,CDM):
    def __init__(self, **kwargs):
        super(StatsTab, self).__init__(**kwargs)
        #self.c = c                             # Character object
        #self.uic._model = self.c               # Bind it all together!
        print "Stat Chracter id is: %d" % id(self.c)

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
            try:
                idx = weaps_as_text.index(weapon_text)
            except ValueError, e:
                print e
                print weaps_as_text
                return
            wep = self.c.equipment[idx]
        if hand == 'mh':
            self.c.equipment.main_hand = wep
        elif hand == 'oh':
            self.c.equipment.off_hand = wep
        else:
            raise ValueError("Unknown hand %s" % hand)



class AttacksTab(TabbedPanelItem,CDM):
    def __init__(self, **kwargs):
        super(AttacksTab, self).__init__(**kwargs)

        # Bind ourselves to when the attacks update in the uic of the parent
        self.uic.bind(attacks=self.onAttacksUpdated)

        # Bind ourselves to when the model changes
        self.update_hooks.append(self.build_buffs)

        # Build GUI
        self.build_buffs()
        self.build_attacks()

        print "Attack Chracter id is: %d" % id(self.c)



    def build_buffs(self):
        # Buffs
        buffs = self.ids['buffs']
        buffs.clear_widgets()
        buffs.bind(minimum_height=buffs.setter('height'))
        sorted(self.possible_buffs_list, key=lambda x: x.name)
        for b in self.possible_buffs_list:
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

        # Management button
        l = Button(text='Add New Buff...', size_hint=(1, None), height='50sp')
        l.bind(on_press = self.new_buff)
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
            print "Rebuilding all attacks"
            self.build_attacks()
        else:
            print "Same number of attacks, no need to rebuild"
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

    def new_buff(self, button):
        popup = NewBuffPopup(self)
        popup.open()


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

    def on_long_press(self, *args):
        attack = self.c.attacks[self.atkNum]
        with self.c.audit_context:
            assert self.c.audit
            msg = self.c.attacks[self.atkNum]
            PopupAudit(msg, attack.name)

class NewBuffPopup(Popup):
    def __init__(self, parent):
        self._my_parent = parent
        super(NewBuffPopup, self).__init__()
        for child in self.ids.content.children:
            if isinstance(child, NewBuffRow):
                self._make_spinner(child.ids.attr_key)


    def _make_spinner(self, spinner):
        profane = ['audit', 'fromDict', 'id', 'makeDict', 'makeUI', 'name',
                    'ui_id']
        proto = Buff('Prototype')
        z = []
        for a in dir(proto):
            if not a.startswith('_') and a not in profane:
                z.append(a)
        spinner.values.extend(z)

    def add_row(self):
        br = NewBuffRow()
        self._make_spinner(br.ids.attr_key)
        self.height = self.height + kivy_sp(50 + 5)
        self.ids.content.add_widget(br)

    def make_buff(self):
        print "Asked to make buff"
        new_buff = Buff(self.ids.buff_name.text)
        for child in self.ids.content.children:
            if isinstance(child, NewBuffRow):
                key = child.ids.attr_key.text
                if key == '':
                    PopupOk("Please specify an attribute")
                    return
                try:
                    value = int(child.ids.attr_value.text)
                except ValueError:
                    PopupOk("Attribute value must be a number")
                    return
                setattr(new_buff, key, value)
        self._my_parent.possible_buffs_list.append(new_buff)
        self._my_parent.build_buffs()
        self.dismiss()

class NewBuffRow(BoxLayout):
    pass

class CounterRow(BoxLayout):
    current_value = StringProperty('0')
    max_value = StringProperty('100')
    counter_name = StringProperty('Counter')

    def go_rename(self, *args):
        new_name = PopupOk("What would you like to name this counter?",
                            "Counter Name", input='text')
        print "Back from function"
        self.counter_name = new_name

    def go_add_n(self, value=None):
        cv = int(self.current_value)
        mv = int(self.max_value)
        if value is None:
            add_n = PopupOk("How much would you like to add?",
                            self.counter_name, inputer='number')
        else:
            add_n = value
        self.current_value = "%d" % min(cv+add_n, mv)



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
        if CDM._apply(code) == False:
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
        if CDM._apply(code) == False:
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
        if CDM.build_character(self.ids.IBC_id.text):
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

        CDM.build_character()

        #self.console = ConsoleWidget(self)
        tab1 = StatsTab()
        self.add_widget(tab1)
        self.attacks_tab = AttacksTab()
        self.add_widget(self.attacks_tab)
        self.add_widget(CountersTab())
        self.add_widget(SkillsTab())
        self.add_widget(FeatsTab())
        self.add_widget(SpellsTab())
        self.add_widget(CodeTab())


class IBC_App(App):
    def build(self):
        return IBC_tabs(do_default_tab = False)

    def on_pause(self):
        # TODO: Save character data off to cache
        return True

    def on_resume(self):
        pass

    def open_settings(self):
        PopupOk("You want a menu")
        return True

if __name__ == '__main__':
    IBC_App().run()