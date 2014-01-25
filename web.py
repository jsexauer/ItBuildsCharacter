"""
Web server half hosted using Flask

based on:  http://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask
"""
#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
from model import Buff

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

buffs = [Buff('Favored Enemy (Human)',4,4),
         Buff('Favored Enemy (Monstrous Humanoid)',2,2),
         Buff('100 to damage',dmg_mod=95),
         Buff('Online Only',1000,1000)]

@app.route('/IBC/api/v1.0/buffs', methods = ['GET'])
@auth.login_required
def get_all_buffs():
    return jsonify( { 'buffs': map(lambda x: x.makeDict(), buffs) } )

@app.route('/IBC/api/v1.0/buffs/<int:task_id>', methods = ['GET'])
@auth.login_required
def get_buffs(task_id):
    raise NotImplementedError()
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
    return jsonify( { 'task': make_public_task(task[0]) } )

@app.route('/IBC/api/v1.0/buffs', methods = ['POST'])
@auth.login_required
def create_buff():
    raise NotImplementedError()
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': tasks[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    tasks.append(task)
    return jsonify( { 'task': make_public_task(task) } ), 201

@app.route('/IBC/api/v1.0/buffs/<int:task_id>', methods = ['PUT'])
@auth.login_required
def update_buff(task_id):
    raise NotImplementedError()
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != unicode:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not unicode:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify( { 'task': make_public_task(task[0]) } )

@app.route('/IBC/api/v1.0/buffs/<int:task_id>', methods = ['DELETE'])
@auth.login_required
def delete_buff(task_id):
    raise NotImplementedError()
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
    tasks.remove(task[0])
    return jsonify( { 'result': True } )

if __name__ == '__main__':
    app.run(debug = True)
    pass
application = app