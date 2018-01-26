from flask import Flask, render_template, flash, session, redirect, url_for, request, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timedelta
from logging.handlers import RotatingFileHandler
import requests
import json
import os
import binascii
import logging
import traceback

app = Flask(__name__, static_url_path='/static')
app.config.from_object(os.environ['APP_SETTINGS'])

formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')

handler = RotatingFileHandler('trtlme.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)

app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.info("App Started!")

db = SQLAlchemy(app)
application = app

from models import User,Payment


def get_payment_id():
    random_32_bytes = os.urandom(32)
    payment_id = "".join(map(chr, binascii.hexlify(random_32_bytes)))

    return '5d79873986852300d941bff65287bc7e2fce4dc2abc6bf8064965db1263e7a28'

def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))

    return d

def get_price(url):
    if len(url) == 1:
        return 500000000
    if len(url) == 2:
        return 40000000
    if len(url) == 3:
        return 30000000
    if len(url) <= 6:
        return 200000
    if len(url) <= 10:
        return 100000
    return 50000

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/payment", methods=["POST"])
def post_payment():
    content = request.form
    exists = db.session.query(User.id).filter_by(address=content["address"]).scalar() is not None
    if exists:
        row = User.query.filter(User.address == content["address"]).first()
        result = row2dict(row)
        return json.dumps({'status':'Fail',
            'reason':'This address has already registered a URL',
            'data':result['url']}),500
    else:
        pay_id = get_payment_id()
        try:
            user = User(address = content["address"],
                payment_id = pay_id,
                url=content["url"],
                message = content["message"],
                turtlehash = content["hash"],
                price = get_price(content["url"])
            )
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            app.logger.info(traceback.format_exc())
            return json.dumps({'status':'Fail',
                'reason':'Your transaction could not be processed'}),500
        return json.dumps({'status':'Success',
            'payment_id': pay_id,
            'price': get_price(content["url"]),
            'data':'Awesome! Your page will be ready at <a href="{url}">{url}</a> upon payment!'.format(url=content['url'])}),200

@app.route("/u/<user_url>")
def userpage(user_url):
    exists = db.session.query(User.id).filter_by(url=user_url).scalar() is not None
    if exists:
        user = row2dict(User.query.filter(User.url==user_url).first())
        paid = db.session.query(Payment.id).filter_by(payment_id=user["payment_id"]).scalar() is not None
        user.pop('payment_id', None)
        if paid:
            return render_template("user.html",user=user)
        else:
            return render_template("waiting.html",user=user)
    return abort(404)

@app.route("/u/<user_url>/edit")
def edit_page(user_url):
    pay_id = request.cookies.get('sessiontoken')
    if pay_id is not None:
        exists = User.query.filter_by(payment_id=pay_id).exists().scalar() is not None
        if exists:
            user = row2dict(User.query.filter(payment_id==pay_id).first())
            return render_template("edit.html",user=user)
        else:
            return json.dumps({'status':'Fail',
                'reason':'Invalid user authentication'}),500
    return render_template("login.html")

@app.route("/login", methods=['POST'])
def login():
    exists = db.session.query(User.id).filter_by(payment_id=request.form["payment_id"]).scalar() is not None
    paid = db.session.query(Payment.id).filter_by(payment_id=request.form["payment_id"]).scalar() is not None

    if real and paid:
        resp = redirect(url_for("edit"))
        resp.set_cookie('sessiontoken', request.form["payment_id"])
        return json.dumps({'status':'Success',
            'data':'Login succeeded'}),200
    if not real: 
        return json.dumps({'status':'Fail',
            'reason':"Payment ID doesn't exist!"}),500
    if not paid:
        user = row2dict(User.query.filter(payment_id==request.form["payment_id"]).first())
        return json.dumps({'status':'Fail',
            'reason':"Payment ID hasn't been paid",
            'price':user["price"]}),500
