import json
from urllib2 import Request, urlopen
from popups import PopupOk


class WebAPIInterfaceMixin(object):
    """Implements web api"""
    api_url = r"http://genericlifeform.pythonanywhere.com/IBC/api/v1.0/"
    #api_url = r"http://localhost:5000/IBC/api/v1.0/"

    def _build_request(self, url, data, request_type='POST'):
        if url.startswith('http:'):
            raise ValueError("Pass relative url, not absolute url")
        url = self.api_url + url
        s = "Unable to post new data to website"

        try:
            payload = json.dumps(data)
            header = {'Content-Type': 'application/json'}
            print url
            print '=' * 20
            print payload
            req = Request(url, payload, header)
            req.get_method = lambda: request_type
            response = urlopen(req)
            print response
            if response.getcode() == 201:
                return json.loads(response.read())
            else:
                s += 'SERVER ERROR:\n'+response.read()
        except Exception, e:
            s += '\nERROR: \n' + str(e)
            print str(e)

        # If we actually get down here, show a posting error
        PopupOk(s, "Posting Error")
        return {}

class WebAPICharacterMixin(WebAPIInterfaceMixin):
    def web_new_character(self, code):
        url = r"characters"
        data = {'def': code}
        response = self._build_request(url, data)
        new_id = response.get('new_character_id', None)
        if new_id is not None:
            PopupOk("Character now on website with id %s" % new_id)
        else:
            PopupOk("Post successful? but bad response %s" % response)

    def web_save_character(self, code, id):
        """Save a character definition out to the web"""
        url = "characters/%s" % id
        response = self._build_request(url, {'def': code})
        if response is not None:
            success = response.get('success', False)
        else:
            success = False
        if success:
            PopupOk("Character applied and saved successfully.",
                    "New Character Definition Loaded")
        else:
            PopupOk(
                "Character applied \n however did not save: \n%s." % response,
                "New Character Definition Loaded")
    @classmethod
    def web_load_character(cls, id):
        url = cls.api_url + r"characters/%s" % id
        response = urlopen(url)
        return json.load(response)

class WebAPICounterMixin(WebAPIInterfaceMixin):
    def __init__(self, web_char_id=None, web_counter_id=None):
        self.web_char_id = web_char_id
        self.web_counter_id = web_counter_id

    def web_counter_put(self):
        assert self.web_counter_id is not None
        assert self.web_char_id is not None
        url = r"characters/%d/counters/%d" % (self.web_char_id,
                                              self.web_counter_id)

        data = self._build_data()
        response = self._build_request(url, data, request_type='PUT')
        if response is not None:
            error = response.get('error', False)
        else:
            error = 'Request is none'
        if error:
            PopupOk(
                "Counter Value not saved to web: \n%s." % response,
                "New Character Definition Loaded")


    def web_counter_get(self):
        assert self.web_counter_id is not None
        assert self.web_char_id is not None
        url = self.api_url + r"characters/%s/counters/%d" % (self.web_char_id,
                                              self.web_counter_id)
        response = urlopen(url)
        data = json.load(response)
        response.close()
        [setattr(self, k, str(v)) for k,v in data.iteritems()]
        print "My [%d] current value is %s" % (id(self), self.current_value)

    def web_counter_new(self):
        assert self.web_counter_id is None
        assert self.web_char_id is not None
        url = r"characters/%d/counters" % self.web_char_id
        data = self._build_data()
        response = self._build_request(url, data)
        new_id = response.get('new_counter_id', None)
        if new_id is None:
            PopupOk("Unable to create counter on web:\n %s" % response)
        else:
            self.web_counter_id = new_id

    def web_counter_get_all(self):
        assert self.web_char_id is not None
        url = self.api_url + r"characters/%s/counters" % self.web_char_id
        response = urlopen(url)
        data = json.load(response)
        response.close()
        return data

    def web_counter_delete(self):
        assert self.web_counter_id is not None
        assert self.web_char_id is not None
        url = r"characters/%s/counters/%d" % (self.web_char_id,
                                              self.web_counter_id)
        self._build_request(url, {}, 'DELETE')

    def _build_data(self):
        data = {'max_value': self.max_value,
                'current_value': self.current_value,
                'counter_name': self.counter_name}
        print "My [%d] current value is %s _build_data" % (id(self), self.current_value)
        return data
