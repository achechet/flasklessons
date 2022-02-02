import os
import sqlite3
from dotenv import load_dotenv
from flask import Flask, render_template, url_for, flash, request, session, redirect, abort, g
from flask.helpers import flash
from werkzeug.utils import redirect
from FDataBase import FDataBase

load_dotenv()
APP_KEY =  os.getenv('APP_KEY')
PORT = os.getenv('PORT')
HOST = os.getenv('HOST')
DATABASE = '/tmp/flsite.db'
app = Flask(__name__)
app.config['SECRET_KEY'] = APP_KEY
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def create_db():
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
        db.commit()
        db.close()

def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db    

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()

@app.route("/")
def index():
    db = get_db()
    dbase = FDataBase(db)
    return render_template('index.html', menu = dbase.getMenu(), title="Главная страница", posts=dbase.getPostAnonce())

@app.route("/about")
def about():
    db = get_db()
    dbase = FDataBase(db)
    return render_template('about.html', title="Страница О нас",  menu = dbase.getMenu())

@app.route("/contact", methods=["POST", "GET"])
def contact():
    db = get_db()
    dbase = FDataBase(db)    
    if request.method == 'POST' :
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
        else:
            flash('Ошибка отправки', category='error')

    return render_template('contact.html', title="Contact",  menu = dbase.getMenu())    

@app.route("/login", methods=["POST", "GET"])
def login():
    db = get_db()
    dbase = FDataBase(db)    
    if 'userLogged' in session:
        return redirect(url_for('profile', username=session['userLogged']))
    elif request.method == 'POST' and request.form['username'] == "alex" and request.form['psw'] =="1234":
        session['userLogged'] = request.form['username']
        return redirect(url_for('profile', username=session['userLogged']))
        
    return render_template('login.html', title="Авторизация",  menu = dbase.getMenu())

@app.errorhandler(404)
def pageNotFound(error):
    db = get_db()
    dbase = FDataBase(db)    
    return render_template('page404.html', title="Страница не найдена",  menu = dbase.getMenu()), 404 


@app.route("/add_post", methods=["POST", "GET"])
def addPost():
    db = get_db()
    dbase = FDataBase(db)
    
    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['post']) > 10:
            res = dbase.addPost(request.form['name'], request.form['post'], request.form['url'] )
            if not res:
                flash('Ошибка добавдения статьи', category='error')
            else:
                flash('Статья успешно добавлена', category='success')
        else:
            flash('Ошибка добавдения статьи', category='error')

    return render_template('add_post.html', title="Добавление статьи", menu = dbase.getMenu() )


@app.route("/post/<alias>")
def showPost(alias):
    db = get_db()
    dbase = FDataBase(db)
    title, post = dbase.getPost(alias)
    if not title:
        abort(404)

    return render_template('post.html', menu=dbase.getMenu(), title=title, post=post)

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
