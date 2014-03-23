# Kivy Imports

import kivy
from model import AuditResult

kivy.require('1.7.0')

from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')


from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.properties import ObjectProperty,StringProperty,ListProperty
from kivy.clock import Clock
from kivy.base import EventLoop

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


def PopupOk(text, title='', btn_text='Continue', input=None, callback=None):
    btnclose = Button(text=btn_text, size_hint_y=None, height='50sp')
    content = BoxLayout(orientation='vertical')
    p = Popup(title=title, content=content, size=('300dp', '300dp'),
                size_hint=(None, None))
    content.add_widget(Label(text=text))
    if input is not None:
        assert callback is not None
        ti = TextInput(height='50sp', font_size='30sp', input_type=input,
                        multiline=False, size_hint_y = None)
        content.add_widget(ti)
        def _callback(*args):
            if ti.text == '':
                callback(None)
            else:
                callback(ti.text)
        p.bind(on_dismiss=_callback)
        p.is_visable = True

    content.add_widget(btnclose)

    btnclose.bind(on_release=p.dismiss)
    p.open()
    if input is not None:
        while not p.is_visable:
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
