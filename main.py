from flask import Flask, render_template, request, redirect, flash
import pymysql
from dynaconf import Dynaconf
import flask_login

app = Flask(__name__)

conf = Dynaconf(
    settings_file=['settings.toml']
)

app.secret_key = conf.secret_key

login_manager = flask_login.LoginManager()
login_manager.init_app(app)


class User:
    is_authenticated = True
    is_anonymous = False
    is_active = True

    def __init__(self, user_id, username, email, full_name):
        self.id = user_id
        self.username = username
        self.email = email
        self.full_name = full_name

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `Customer` WHERE `ID` = {user_id}")
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result is not None:
        return User(result['ID'], result['username'], result['email'], result['full_name'])



def connect_db():
    conn = pymysql.connect(
        host="10.100.34.80",
        database="kchapman_ANIWRLD",
        user='kchapman',
        password=conf.password,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

    return conn


@app.route("/")
def index():
    return render_template("homepage.html.jinja")


@app.route("/browse")
def browse():

    query=request.args.get('query')

    conn = connect_db()

    cursor = conn.cursor()

    if query is None:
        cursor.execute("SELECT * FROM `Product`;")
    else:
        cursor.execute(f"SELECT * FROM `Product` WHERE `product_name` LIKE '%{query}%';")

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("browse.html.jinja", products=results)


@app.route("/product/<product_id>")
def product_page(product_id):

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(
        f"SELECT * FROM `Product` WHERE `product_id` = {product_id};")

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("product.html.jinja", product=result)


@app.route("/signup", methods=["POST", "GET"])
def signup_page():

    if request.method == "POST":
        full_name = request.form['full_name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Confirmed password does not match")
            return render_template("signup.html.jinja")

        conn = connect_db()

        cursor = conn.cursor()

        try:
            cursor.execute(f"""

                INSERT INTO `Customer`
                    (`full_name`, `username`, `password`, `email`, `phone`, `address`)
                VALUES
                    ('{full_name}', '{username}', '{password}', '{email}', '{phone}', '{address}');
            """)

        except pymysql.err.IntegrityError:
            flash("Your email/username already", 'error')

        else:
            return redirect("/signin")

        finally:
            cursor.close()
            conn.close()

    return render_template("signup.html.jinja")

@app.route("/signin", methods=["POST", "GET"])
def signin_page():

    if request.method=='POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn=connect_db()
        cursor=conn.cursor()

        cursor.execute(f"SELECT * FROM `Customer` WHERE `username` = '{username}'")
        result=cursor.fetchone()

        if (result is None): 
            flash("Incorrect Username or Password")
        elif (result['password']!=password):
            flash("Incorrect Username or Password")
        else:
            user = User(result['ID'], result['username'], result['email'], result['full_name'])
            flask_login.login_user(user)
            return redirect('/')




    return render_template("signin.html.jinja")

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect('/')