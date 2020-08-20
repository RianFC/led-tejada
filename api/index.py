from flask import Flask, request, url_for, redirect
import flask_login
import random
import string
import db
import re
import requests

#configure sua senha e user

users = {'user': {'password': 'pass'}}

#umas config padrão

a = db.dbc()
a['at'] = ''.join(random.choices(string.hexdigits, k=6))
db.save(a)

app = Flask(__name__)
app.secret_key = 'oi'
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

#configuração do ligin

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return

    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return

    user = User()
    user.id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['password'] == users[email]['password']

    return user

#Aqui é onde retorna a cor
@app.route("/")
def index():
    a = db.dbc()
    print(a)
    return f'''<html><body style="background-color:{a["at"]};"><meta http-equiv="refresh" content="0"><body>{"<br>"*10}<center><h1 class=color>{a["at"]}</h1></center></body></html>'''

#Esta parte serve para fazer a integração com o webhoock
@app.route("/ifttt", methods=['POST'])
def ifttt():
    a = db.dbc()
    color = request.get_data().decode()
    return set(color, a)

#Aqui é igual ao de cima, porém para outros usos
@app.route("/cor", methods=['POST','get'])
def cor():
    a = db.dbc()
    color = request.values.get('q')
    return set(color, a)

#Ao execultar as funçoes de cima ele vêm aqui para processar
#o hex e ver se está correto e logo após manda para a db
def set(color, a):
    if color.lower() in a["saves"]:
        color = a["saves"][color]
    if re.search(r'(?:[0-9a-fA-F]{6})', color):
        color = re.match(r'(?:[0-9a-fA-F]{6})', color.replace('#','')).string
        a["at"] = color
        db.save(a)
        for i in a["users"]:
            key = a["users"][i]["code"]
            print(key)
            print(color)
            r = requests.post('https://maker.ifttt.com/trigger/led/with/key/'+key,
                data={'value1':color})
            print(r.url)
            print(r.text)
        return dict(ok=True, color=color)
    else:
        return dict(ok=False, error='Hex is not valid')

#Esta parte é bem simples, quando usa o /get ele retorna a cor
#que está na hora
@app.route("/get")
def cget():
    a = db.dbc()
    return dict(color=a["at"], ok=True)

#Aqui é para adicionar palavras na db assim sendo mais simples
#trocar a cor por não precisar usar o hex
@app.route('/set', methods=['GET', 'POST'])
def cset():
    if request.method == 'GET':
        return '''
               <form action='set' method='POST'>
                <input type='text' name='n' id='n' placeholder='nome'/>
                <input type='text' name='r' id='r' placeholder='hex'/>
                <input type='submit' name='submit'/>
               </form>
               '''
    a = db.dbc()
    print('1')
    if request.values.get('n') and request.values.get('r'):
        a["aprove"]["colors"][request.values.get('n')] = request.values.get('r')
        db.save(a)
        return dict(ok=True)
    else:
        return dict(ok=False, error='Está faltando algum argumento.')

@app.route('/add')
def add():
    a = db.dbc()
    print(request.values)
    if request.values.get('cd') and request.values.get('em') and request.values.get('nm'):
        a["aprove"]["users"].update({request.values.get('nm'):{
            'code':request.values.get('cd'),
            'email':request.values.get('em')
        }})
        db.save(a)
        return dict(ok=True)
    else:
        return dict(ok=False, error='Está faltando algum(s) argumento(s).')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return '''
               <form action='login' method='POST'>
                <input type='text' name='email' id='email' placeholder='email'/>
                <input type='password' name='password' id='password' placeholder='password'/>
                <input type='submit' name='submit'/>
               </form>
               '''
    print(request.form)
    email = request.form['email']
    if request.form['password'] == users[email]['password']:
        user = User()
        user.id = email
        flask_login.login_user(user)
        return redirect(url_for('protected'))

    return 'Bad login'


@app.route('/protected', methods=['GET', 'POST'])
@flask_login.login_required
def protected():
    a = db.dbc()
    if request.method == 'GET':
        text = '''<h1>Users</h1>\n'''
        for i in a['aprove']['users']:
            text += "<form action='protected' method='POST'>\n"
            text += f" <label>nome: {i}, email: {a['aprove']['users'][i]['email']}  </label>"
            text += f"<button name='a_nome' value={i}>aprove</button>"
            text += f"<button name='r_nome' value={i}>reprove</button>"
            text += '</form>'
        text += '<br><br><br>'
        text += '''<h1>Colors</h1>\n'''
        for i in a['aprove']['colors']:
            text += "<form action='protected' method='POST'>\n"
            text += f" <label>nome: {i}, hex: </label><label style='color:#{a['aprove']['colors'][i]};'>{a['aprove']['colors'][i]}  </label>"
            text += f"<button name='a_color' value={i}>aprove</button>"
            text += f"<button name='r_color' value={i}>reprove</button>"
            text += '</form>'
        return text

    print(request.form)
    print(1)
    if request.form.get('a_nome'):
        b = request.form['a_nome']
        a["users"][b] = a['aprove']['users'][b]
        a['aprove']['users'].pop(b)
        db.save(a)
        return b+' aprovado'
    elif request.form.get('r_nome'):
        b = request.form['r_nome']
        a['aprove']['users'].pop(b)
        db.save(a)
        return b+' reprovado'
    elif request.form.get('a_color'):
        b = request.form.get('a_color')
        a['saves'][b] = a['aprove']['colors'][b]
        a['aprove']['colors'].pop(b)
        db.save(a)
        return f'a cor {b} foi aprovada'
    elif request.form.get('r_color'):
        b = request.form.get('r_color')
        a['aprove']['colors'].pop(b)
        db.save(a)
        return f'a cor {b} foi recusada'

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'

@app.route('/te')
@flask_login.login_required
def protectd():
    return 'Logged in as: ' + flask_login.current_user.id

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'
