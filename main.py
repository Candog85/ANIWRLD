from flask import Flask, render_template, request, redirect, flash
import pymysql
from dynaconf import Dynaconf

app = Flask(__name__)

conf = Dynaconf(
    settings_file=['settings.toml']
)

app.secret_key = conf.secret_key


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

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM `Product`;")

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
