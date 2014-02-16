"""
Web server half hosted using Flask

based on:  http://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask
"""
#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
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

@app.route('/IBC/api/v1.0/buffs/del/<int:buff_id>',methods = ['GET','POST'])
@auth.login_required
def delete_buff(buff_id):
    buff = filter(lambda t: t['id'] == buff_id, buffs)
    if len(buff) == 0:
        abort(404)
    buffs.remove(buff[0])
    data.sync()
    return jsonify( { 'result': True } ), 201

if __name__ == '__main__':
    app.run(debug = True)
    pass
application = app