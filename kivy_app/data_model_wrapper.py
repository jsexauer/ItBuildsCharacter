"""
Allow the simple creation of kivy UIs for arbitrary python object.  The UI
will automatically update as the underlying python model changes, provided any
function on the UI side use the "update" decorator.
"""

import kivy
kivy.require('1.7.0')

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.event import EventDispatcher
from kivy.lang import Builder


##################
# DATA MODEL SIDE
##################

class DataModel(object):
    def __init__(self):
        self.a = 'This is a'
        self.b = 'This is b'

    @property
    def c(self):
        return self.a + '\nand\n' + self.b

    @property
    def list_d(self):
        return [self.a, self.b]

##################
# BRIDGE
##################

class UI_DataModelMeta(type):
    def __new__(meta, name, bases, dct):
        if '_model_class' not in dct.keys():
            raise AttributeError("UI_DataModel must have _model_class attribute")
        example_model = dct['_model_class']()
        # Create kivy StringProperty objects for all the attributes
        #   in the underlying data model
        added_attributes = []
        for attr in dir(example_model):
            if not attr.startswith('_'):
                ##print "Making attribute %s" % attr
                assert attr not in dir(EventDispatcher())
                if isinstance(getattr(example_model, attr), list):
                    print ">> MAKING LIST FOR %s" % attr
                    dct[attr] = ListProperty(['INIT',])
                else:
                    dct[attr] = StringProperty('INIT')
                added_attributes.append(attr)
        # Let the UI_DataModel know what attributes are from the common model
        dct['_model_attr'] = added_attributes
        return super(UI_DataModelMeta, meta).__new__(meta, name, bases, dct)


class UI_DataModel(EventDispatcher):
    __metaclass__ = UI_DataModelMeta
    _model_class = DataModel
    def __init__(self, parent=None):
        if parent is None:
            parent = self._model_class()
        if not isinstance(parent, self._model_class):
            raise TypeError("Passed data model must be of same type as _model")
        self.__parent = parent
#        print "Making a datamodel with parent's attributes, which are:"
#        print '\t' + str(self._model_attr)
    def __getattribute__(self, key):
#        print ">> Trying to get %s" % key
        if key in ('_model_attr', '__parent', '_model_class', '_model'):
            return object.__getattribute__(self, key)
        elif key in self._model_attr:
#            print "    INTERCEPTED!"
            # Get the value of this key from the common data model
            val = getattr(self.__parent, key)
#            print "  val or %s is %s" % (key, val)
            # Typecase as needed
            if isinstance(val, list):
                # Construct a list of property objects
                val2 = []
                for a in val:
                    # We have to create a whole new UI model for these...
                    #class SubModel(UI_DataModel):
                    #    _model_class = type(a)
                    #val2.append(SubModel(a))
                    val2.append(str(a))
            else:
                val2 = str(val)
            # Invoke kivy's Property setter by setting our attribute
            setattr(self, key, val2)
            # Proceed as normal
            return EventDispatcher.__getattribute__(self, key)
        else:
#            print "    Pushing up to base class"
            return EventDispatcher.__getattribute__(self, key)

    @property
    def _model(self):
        return self.__parent

    @_model.setter
    def _model(self, new_parent):
        if not isinstance(new_parent, self._model_class):
            raise TypeError("Passed data model must be of same type as _model")
        self.__parent = new_parent
        # Update outselves
        self.update(lambda: None)()

    def update(self, func):
        """Decorator to put around any UI function that update the common
           data model"""
        def wrapper(*args, **kwargs):
            # Execute function as normal
            ret = func(*args, **kwargs)
            # Update UI Data Model wrapper
            for attr in self._model_attr:
                getattr(self, attr)
            return ret
        return wrapper


##################
# UI SIDE
##################

Builder.load_string("""
<RootWidget>:
    cols: 2
    Label:
        text: "Attribute a:"
    Label:
        text: root.ui_data_model.a
    Label:
        text: "Attribute b:"
    Label:
        text: root.ui_data_model.b
    Label:
        text: "Attribute c:"
    Label:
        text: root.ui_data_model.c
    Label:
        text: "Attribute list d[0]:"
    Label:
        text: root.ui_data_model.list_d[0]
    Button:
        text: "Make data_model.a longer"
        on_press: root.button_press()
    Button:
        text: "Make data_model.b shorter"
        on_press: root.button_press2()
""")


class RootWidget(GridLayout):
    ui_data_model = UI_DataModel(DataModel())

    def __init__(self, **kwargs):
        GridLayout.__init__(self, **kwargs)
        # Set up out model
        self.data_model = DataModel()
        self.ui_data_model._model = self.data_model

    @ui_data_model.update
    def button_press(self, *args):
        # Make sure you modify the common data model, not the UI's
        #  data model wrapper
        self.data_model.a = 'This is a and it is really long now'
        ##print common_data_model.c
        ##print self.ui_data_model.c
        ##print self.ui_data_model.a

    @ui_data_model.update
    def button_press2(self, *args):
        self.data_model.b = 'B'
        ##print common_data_model.c
        ##print self.ui_data_model.c

class TestApp(App):
    def build(self):
        return RootWidget()

if __name__ == '__main__':
    app = TestApp()
    app.run()