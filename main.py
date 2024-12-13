from flask import Flask, render_template
import pymysql
from dynaconf import Dynaconf

app = Flask(__name__)

conf = Dynaconf(
    settings_file=['settings.toml']
)

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
    
    conn=connect_db()
    
    cursor=conn.cursor()
    
    cursor.execute("SELECT * FROM `Product`;")
    
    results=cursor.fetchall()

    cursor.close()
    conn.close()
    
    return render_template("browse.html.jinja", products=results)

@app.route("/product/<product_id>")
def product_page(product_id):

    conn=connect_db()
    
    cursor=conn.cursor()

    cursor.execute(f"SELECT * FROM `Product` WHERE `product_id` = {product_id};")

    result=cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("product.html.jinja", product=result)