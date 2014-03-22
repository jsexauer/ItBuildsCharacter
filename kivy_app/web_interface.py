import json
from urllib2 import Request, urlopen
from popups import PopupOk


class WebAPIMixin(object):
    def __init__(self):
        """Implements web api"""
        self.api_url = r"http://genericlifeform.pythonanywhere.com/IBC/api/v1.0"
        if not self.api_url.endswith(r'/'):
            self.api_url += r'/'

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
        url = r"characters/%s" % id
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

    def _build_request(self, url, data, request_type='POST'):
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
        except Exception, e:
            s += '\nERROR: ' + str(e)

        # If we actually get down here, show a posting error
        PopupOk(s, "Posting Error")
