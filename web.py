"""
Web server half hosted using Flask

based on:  http://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask
"""
#!flask/bin/python
from flask import (Flask, jsonify, abort, request, make_response, url_for,
                    flash, get_flashed_messages)
from model import Buff, DamageRoll
from persistentDictionary import PersistentDict
import shelve, os

app = Flask(__name__, static_url_path = "")

##############################################################################
# Disable authetication for now
#from flask.ext.httpauth import HTTPBasicAuth
#auth = HTTPBasicAuth()

class nullClass(object):
    pass
auth = nullClass()
nullWrap = lambda x: x
auth.login_required = nullWrap      # Disable login for now
auth.get_password = nullWrap
auth.error_handler = nullWrap
##############################################################################

##################
# Data Loading
##################

#buffs = [Buff('Favored Enemy (Human)',4,4),
#         Buff('Favored Enemy (Monstrous Humanoid)',2,2),
#         Buff('100 to damage',dmg_mod=95),
#         Buff('Online Only',1000,1000)]
per_path = os.path.dirname(os.path.realpath(__file__))+os.sep+"data.dat"
data = PersistentDict(per_path)
try:
    characters = data['characters']
except KeyError:
    data['characters'] = []
    characters = data['characters']
try:
    char_counters = data['char_counters']
except KeyError:
    data['char_counters'] = []
    char_counters = data['char_counters']
    # Add a blank set of counters for all existing characters
    for c in characters:
        char_counters.append([])

##################
# Webpages
##################
@app.route('/IBC/characters/<int:char_id>', methods = ['GET'])
def show_characters(char_id):
    code = characters[char_id]
    flash_messages = get_flashed_messages()
    counters = char_counters[char_id]
    html = """
    <html>
    <body>
    <h1>Character #%(char_id)d</h1>
    %(flash_messages)s
    <h3>Counters</h3>
    %(counters)s
    <h3>Character Definition (ie, Code)</h3>
    <form method='POST'>
    <textarea rows=50 cols=80 name="code">%(code)s</textarea>
    <br />
    <input type="Submit">
    </form>
    </body>
    </html>
    """
    return html % locals()
@app.route('/IBC/characters/<int:char_id>', methods = ['POST'])
def edit_characters(char_id):
    characters[char_id] = request.form['code']
    data.sync()
    flash("Character code updated successfully")
    return show_characters(char_id)

##################
# API
##################

####
# CHARACTERS
####
@app.route('/IBC/api/v1.0/characters', methods = ['GET'])
@auth.login_required
def get_all_characters():
    return jsonify( { 'NotYetImplemented': True } )

@app.route('/IBC/api/v1.0/characters/<int:id>', methods = ['GET'])
@auth.login_required
def get_characters(id):
    try:
        ch = characters[id]
    except Exception, e:
        return jsonify( {'error': str(e)} )
    #if len(ch) == 0:
    #    abort(404)
    return jsonify({'def': ch, 'id': id})

@app.route('/IBC/api/v1.0/characters', methods = ['POST'])
@auth.login_required
def create_character():
    try:
        characters.append(request.json['def'])
    except Exception, e:
        return jsonify( {'error': str(e)} )
    data.sync()
    return jsonify( { 'new_character_id': len(characters)-1} ), 201

@app.route('/IBC/api/v1.0/characters/<int:id>', methods = ['POST'])
@auth.login_required
def update_character(id):
    success = True
    try:
        characters[id] = request.json['def']
    except IndexError:
        success = False
    data.sync()
    return jsonify( { 'success': success } ), 201

####
# COUNTERS
####
@app.route('/IBC/api/v1.0/characters/<int:char_id>/counters', methods = ['GET'])
@auth.login_required
def get_all_counters(char_id):
    try:
        counters = char_counters[char_id]
    except Exception, e:
        return jsonify( {'error': str(e)} )
    #if len(ch) == 0:
    #    abort(404)
    return jsonify({n:c for n,c in enumerate(counters)})

@app.route('/IBC/api/v1.0/characters/<int:char_id>/counters', methods = ['POST'])
@auth.login_required
def create_counter(char_id):
    try:
        expected = ['name', 'max_value']
        for k in expected:
            assert k in request.json.keys()
        assert len(expected) == len(request.json)
        char_counters[char_id].append(request.json)
    except Exception, e:
        return jsonify( {'error': str(e)} )
    data.sync()
    return jsonify( { 'new_counter_id': len(char_counters[char_id])-1} ), 201

@app.route('/IBC/api/v1.0/characters/<int:char_id>/counters/<int:count_id>', methods = ['PUT'])
@auth.login_required
def edit_counter(char_id, count_id):
    try:
        char_counters[char_id][count_id].update(request.json)
    except Exception, e:
        return jsonify( {'error': str(e)} )
    data.sync()
    return jsonify( char_counters[char_id][count_id] )
@app.route('/IBC/api/v1.0/characters/<int:char_id>/counters/<int:count_id>', methods = ['GET'])
@auth.login_required
def get_counter(char_id, count_id):
    try:
        counter = char_counters[char_id][count_id]
    except Exception, e:
        return jsonify( {'error': str(e)} )
    data.sync()
    return jsonify( counter )
@app.route('/IBC/api/v1.0/characters/<int:char_id>/counters/<int:count_id>', methods = ['DELETE'])
@auth.login_required
def get_counter(char_id, count_id):
    try:
        counter = char_counters[char_id].pop(count_id)
    except Exception, e:
        return jsonify( {'error': str(e)} )
    data.sync()
    return jsonify( counter )


##@app.route('/IBC/api/v1.0/buffs/del/<int:buff_id>',methods = ['GET','POST'])
##@auth.login_required
##def delete_buff(buff_id):
##    buff = filter(lambda t: t['id'] == buff_id, buffs)
##    if len(buff) == 0:
##        abort(404)
##    buffs.remove(buff[0])
##    data.sync()
##    return jsonify( { 'result': True } ), 201

##################
# Authentication and Error Handelers
##################

app.secret_key = '\xcf(d\x7f\x18\xef\x81\x16C\xdeT\xd4x\x0b\xb3\xf0\x8d\xcf2;\xdd\x05>\xbd'

@auth.get_password
def get_password(username):
    if username == 'miguel':
        return 'python'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify( { 'error': 'Unauthorized access' } ), 403)
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify( { 'error': 'Bad request' } ), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

if __name__ == '__main__':
    app.run(debug = True)
    pass
application = app