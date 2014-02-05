# Library
import android, operator

class AndroidApp(object):
    def __init__(self, addr_port):
        """Create a full-screen android application"""
        try:
            # Create droid object if we're on the phone
            droid = android.Android()
        except:
            try:
                # Create droid object if we're on computer
                droid=android.Android(('192.168.3.10','36161'))
            except:
                raise RuntimeError("Could not connect to android device")
        self.droid = droid
        self.debug = True
        self._menu = []
        self._events = []
        self._quit = False

    def bind(self, widget_id, func, event_name='click'):
        """Bind func to widget with id widget_id.  If we should
        match various id's, pass lambda which will be true on ids you're
        looking for."""
        assert callable(func)
        assert isinstance(widget_id, basestring) or\
               callable(widget_id) or \
               widget_id is None
        self._events.append( (event_name, widget_id, func) )

    def start(self):
        self._event_loop()

    def quit(self, event=None):
        self._quit = True

    def add_menu_item(self, label, func, icon=None):
        """Add a label with given icon to the option menu
        Icons: http://androiddrawableexplorer.appspot.com/"""
        # See: http://www.mithril.com.au/android/doc/UiFacade.html#addOptionsMenuItem
        self._menu.append(label)
        # Create event
        self.bind(None, func, 'menu_'+label)
        # Add item
        self.droid.addOptionsMenuItem(label,'menu_'+label,None,icon)

    def clear_menu(self):
        """Clear the menu"""
        self._menu = []
        self.droid.clearOptionsMenu()

    def alert_dialog(self,title, message, buttonText='Continue'):
        self.droid.dialogCreateAlert(title, message)
        self.droid.dialogSetPositiveButtonText(buttonText)
        self.droid.dialogShow()
        response = self.droid.dialogGetResponse().result
        return response['which'] == 'positive'

    def _event_loop(self):
        """Process event bound"""
        while not self._quit:
            event = self.droid.eventWait().result
            if self.debug:
                print event

            if event["name"]=="screen" and event["data"]=="destroy":
                # Quit App
                return
            for e in self._events:
                # e[0] = event_name
                # e[1] = widget_id
                # e[2] = func
                event_name = event.get('name', None)
                data = event.get('data',None)
                if data is None:
                    event_id = None
                else:
                    event_id = data.get('id', None)

                # See if e[1] (the widget id) is a lambda.  If not, make one
                if isinstance(e[1], basestring):
                    id_func = lambda x: operator.eq(x, e[1])
                elif callable(e[1]):
                    id_func = e[1]
                elif e[1] is None:
                    id_func = lambda x: operator.is_(x, None)
                else:
                    raise ValueError()

                if event_name == e[0] and id_func(event_id):
                    # Matched to an event, execute binding
                    e[2](event)
        # End event loop
        self.droid.fullDismiss()

