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
from kivy.uix.checkbox import CheckBox
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.lang import Builder


this_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep
Builder.load_file(this_dir + 'tabs.kv')




class StatsTab(TabbedPanelItem):
    def __init__(self, c, **kwargs):
        super(StatsTab, self).__init__(**kwargs)
        self.c = c      # Character object

        # Build GUI
        self.refresh_gui()

    def on_press(self):
        self.refresh_gui()

    def refresh_gui(self):
        for attr in ['str','int','dex','wis','con','cha']:
            lbl = self.ids[attr]
            lbl.text = attr.capitalize() + ' ' + str(self.c[attr])



    def test_button_press(self):
        self.c.base.str_score = 25
        print "c id is %s" % id(self.c)
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
        print id(buffs)
        for b in self.buffs:
            l = BoxLayout(orientation='horizontal', padding=5,
                            size_hint=(1, None), height=30)

            cb = CheckBox(size_hint=(None, 1), width=30)
            l.add_widget(cb)

            name = Label(halign='left', size_hint=(None,1), valign='middle')
            name.bind(texture_size=name.setter('size'))
            name.text = b.name
            l.add_widget(name)

            buffs.add_widget(l)

        # Attacks
        attacks = self.ids['attacks']
        attacks.clear_widgets()

        for a in self.c.attacks:
            l = BoxLayout(orientation='horizontal', padding=5,
                            size_hint=(1, None), height=50)

            name = Label()
            name.text = a.name
            l.add_widget(name)

            atk = Label()
            atk.text = '+' + str(a.atk)
            l.add_widget(atk)

            dmg = Label()
            dmg.text = str(a.dmg_roll)
            l.add_widget(dmg)

            roll = Button()
            roll.text = "Roll"
            roll._attack = a
            roll.bind(on_press=self.show_roll)
            l.add_widget(roll)

            attacks.add_widget(l)






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



class IBC_tabs(TabbedPanel):
    def __init__(self, **kwargs):
        super(IBC_tabs, self).__init__(**kwargs)

        self.build_character()

        #self.console = ConsoleWidget(self)
        tab1 = StatsTab(self.c)
        self.add_widget(tab1)
        tab2 = AttacksTab(self.c, self.possible_buffs_list)
        self.add_widget(tab2)

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

        c.BAB = 11

        greatsword = Weapon("Greatsword",
                      Attack(atk=+0, dmg_roll=DamageRoll.fromString("2d6"),
                             crit_range=[19,20], crit_mult=2, two_handed=True))
        c.equipment.main_hand = greatsword
        attacks = c.attacks

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