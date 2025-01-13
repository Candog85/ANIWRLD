from flask import Flask, render_template, request, redirect, flash, abort
import pymysql
from dynaconf import Dynaconf
import flask_login
from datetime import datetime

app = Flask(__name__)

conf = Dynaconf(
    settings_file=['settings.toml']
)

app.secret_key = conf.secret_key

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = ('/login')


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

    query = request.args.get('query')

    conn = connect_db()

    cursor = conn.cursor()

    if query is None:
        cursor.execute("SELECT * FROM `Product`;")
    else:
        cursor.execute(
            f"SELECT * FROM `Product` WHERE `product_name` LIKE '%{query}%';")

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

    if result is None:
        abort(404)

    cursor.close()
    conn.close()

    return render_template("product.html.jinja", product=result)


@app.route("/signup", methods=["POST", "GET"])
def signup_page():

    if flask_login.current_user.is_authenicated:
        return redirect('/')

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
                    ('{full_name}', '{username}', '{password}',
                     '{email}', '{phone}', '{address}');
            """)

        except pymysql.err.IntegrityError:
            flash("Your email/username already", 'error')

        else:
            return redirect("/login")

        finally:
            cursor.close()
            conn.close()

    return render_template("signup.html.jinja")


@app.route("/login", methods=["POST", "GET"])
def login_page():

    if flask_login.current_user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT * FROM `Customer` WHERE `username` = '{username}'")
        result = cursor.fetchone()

        if result is None:
            flash("Incorrect Username or Password")
        elif result['password'] != password:
            flash("Incorrect Username or Password")
        else:
            user = User(result['ID'], result['username'],
                        result['email'], result['full_name'])
            flask_login.login_user(user)
            return redirect('/')

    return render_template("login.html.jinja")


@app.route('/logout')
@flask_login.login_required
def logout():

    flask_login.logout_user()
    return redirect('/')


@app.route('/cart')
@flask_login.login_required
def cart():

    conn = connect_db()
    cursor = conn.cursor()

    customer_id = flask_login.current_user.id

    cursor.execute(f"""

    SELECT `product_name`, `price`, `image_dir`, `quantity`, `Cart`.`id` 
    FROM `Cart` 
    JOIN `Product` 
    ON `Cart`.`product_id` = `Product`.`product_id` 
    WHERE `customer_id`= {customer_id}

    """)

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    total = 0
    for item in results:
        total += (item['price']*item['quantity'])

    return render_template("cart.html.jinja", products=results, total=total)


@app.route('/product/<product_id>/cart', methods=["POST"])
@flask_login.login_required
def add_cart(product_id):

    quantity = request.form['quantity']
    customer_id = flask_login.current_user.id

    conn = connect_db()
    cursor = conn.cursor()

    request.path

    cursor.execute(f"""
    
    INSERT INTO `Cart` (`customer_id`, `product_id`, `quantity`)
    VALUES ('{customer_id}', '{product_id}', '{quantity}')
    ON DUPLICATE KEY UPDATE
    `quantity`=`quantity`+{quantity}
    """)

    cursor.close()
    conn.close()

    return redirect('/cart')


@app.route('/cart/<id>/remove', methods=["POST", "GET"])
@flask_login.login_required
def remove_item(id):

    conn = connect_db()
    cursor = conn.cursor()

    request.path

    cursor.execute(f"""
    
    DELETE FROM `Cart`
    WHERE `id` = {id}
    """)

    cursor.close()
    conn.close()

    flash("Item removed successfully")
    return redirect("/cart")


@app.route('/cart/<id>/update', methods=["POST", "GET"])
@flask_login.login_required
def update_quantity(id):

    conn = connect_db()
    cursor = conn.cursor()

    quantity = request.form['quantity']

    cursor.execute(f"""
    
    UPDATE `Cart`
    SET `quantity`= {quantity}
    WHERE `id` = {id}

    """)

    cursor.close()
    conn.close()

    flash("Item Updated Succesfully")
    return redirect("/cart")


@app.route('/checkout', methods=["POST", "GET"])
@flask_login.login_required
def checkout():

    customer_id = flask_login.current_user.id

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f'SELECT * FROM `Cart`')

    cart = cursor.fetchall()

    cursor.execute(f"""
    
    INSERT INTO `Sale` (`customer_id`, `status`)
    VALUES ('{customer_id}', 'pending')

    """)

    for product in cart:
        
        cursor.execute(f"""
        
        INSERT INTO `SaleProduct` (`sale_id`, `product_id`, `quantity`)
        VALUES ('{cursor.lastrowid}', '{product['product_id']}', '{product['quantity']}')
        """)

    cursor.execute(f"""
    
    DELETE FROM `Cart` WHERE `customer_id` = "{customer_id}";
    """)

    cursor.close()
    conn.close()

    return render_template("checkout.html.jinja", cart=cart)

@app.route('/product/<product_id>/review', methods=["POST", "GET"])
@flask_login.login_required
def review(product_id):
    
    customer_id=flask_login.current_user.id
    review_score=request.form['rating']
    review_text=request.form['review']
    
    conn=connect_db()
    cursor=conn.cursor()
    

    
    cursor.execute(f"""
    
    INSERT INTO `Review` (`product_id`, `customer_id`, `review_txt`, `rating`)
    VALUES ('{product_id}', '{customer_id}', '{review_text}', '{review_score}')
    """)
    
    return redirect('')