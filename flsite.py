import os
import sqlite3
from dotenv import load_dotenv
from flask import Flask, render_template, url_for, flash, request, session, redirect, abort, g, make_response
from flask.helpers import flash
from werkzeug.utils import redirect
from FDataBase import FDataBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin
from forms import LoginForm

load_dotenv()
APP_KEY =  os.getenv('APP_KEY')
PORT = os.getenv('PORT')
HOST = os.getenv('HOST')
DATABASE = '/tmp/flsite.db'
MAX_CONTENT_LENGTH = 1024 * 1024
app = Flask(__name__)
app.config['SECRET_KEY'] = APP_KEY
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"

@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    return UserLogin().fromDB(user_id, dbase)

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

dbase = None
@app.before_request
def before_request():
    ### Установление сщединения с БД перед выполнением запроса ###
    global dbase
    db = get_db()
    dbase = FDataBase(db)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()

@app.route("/")
def index():
    return render_template('index.html', menu = dbase.getMenu(), title="Главная страница", posts=dbase.getPostAnonce())

@app.route("/about")
def about():
    return render_template('about.html', title="Страница О нас",  menu = dbase.getMenu())

@app.route("/contact", methods=["POST", "GET"])
def contact():
    if request.method == 'POST' :
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
        else:
            flash('Ошибка отправки', category='error')

    return render_template('contact.html', title="Contact",  menu = dbase.getMenu())    

@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = dbase.getUserByEmail(form.email.data)
        if user and check_password_hash(user['psw'], form.psw.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("profile"))
        
        flash("Неверная пара логин/пароль", "error")   
             
    return render_template('login.html', menu = dbase.getMenu(), title="Авторизация", form=form)    

    # if request.method == 'POST' :
    #    user = dbase.getUserByEmail(request.form['email'])
    #    if user and check_password_hash(user['psw'], request.form['psw']):
    #        userlogin = UserLogin().create(user)
    #        rm = True if request.form.get('remainme') else False
    #        login_user(userlogin, remember=rm)
    #        return redirect(request.args.get("next") or url_for("profile"))
    #    
    #    flash("Неверная пара логин/пароль", "error")
    #    
    # return render_template('login.html', title="Авторизация",  menu = dbase.getMenu())

@app.route("/register", methods=["POST", "GET"])
def register():            
    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['email']) > 4 and len(request.form['psw']) > 4 and request.form['psw'] == request.form['psw2']:
            hash = generate_password_hash(request.form['psw'])
            res = dbase.addUser(request.form['name'], request.form['email'], hash)
            if res:
                flash("Вы успешно зарегистрированы", "success")      
                return redirect(url_for('login'))          
        else:
                flash("Ошибка при добавдении в БД 1", "error")
    else:
            flash("Не верно заполнены поля формы", "error")
    
    return render_template('register.html', title="Регистрация",  menu = dbase.getMenu())    

@app.errorhandler(404)
def pageNotFound(error):
    if 'visits' in session:
        session['visits'] = session.get('visits') + 1
    else:
        session['visits'] = 1
    
    print(f"404 page Число просмотров: {session['visits']}")
    return render_template('page404.html', title="Страница не найдена",  menu = dbase.getMenu()), 404 


@app.route("/add_post", methods=["POST", "GET"])
def addPost():
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
@login_required
def showPost(alias):
    title, post = dbase.getPost(alias)
    if not title:
        abort(404)

    return render_template('post.html', menu=dbase.getMenu(), title=title, post=post)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))

@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html', menu=dbase.getMenu(), title="Профиль")

@app.route("/userava")
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""
    
    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h

@app.route("/upload", methods=['POST', 'GET'])
@login_required
def upload():
        if request.method == 'POST':
            file = request.files['file']
            if file and current_user.verifyExt(file.filename):
                try:
                    img = file.read()
                    res = dbase.updateUserAvatar(img, current_user.get_id())
                    if not res:
                        flash("Ошибка обновления ававтара1", "error")
                    flash("Аватар обновлен", "success")
                except FileNotFoundError as e:
                    flash("Ошибка чтения файла", "error")
            else:
                flash("Ошибка обновления аватара2", "error")
        
        return redirect(url_for('profile'))
        
                
    
# before_first_request & after_request 

@app.teardown_request
def teardown_request(response):
    print("teardown request called")    

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
