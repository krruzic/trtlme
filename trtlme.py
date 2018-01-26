from datetime import datetime, timedelta
import json
import traceback
import os
from flask import Flask, render_template, flash, session, redirect, url_for, request, abort
from flask_sqlalchemy import SQLAlchemy
import requests

from utils import get_payment_id, row2dict, get_price

app = Flask(__name__, static_url_path='/static')
app.config.from_object(os.environ['APP_SETTINGS'])


db = SQLAlchemy(app)
application = app

from models import User, Payment

@app.route("/")
def index():
    """ renders the main welcome page """
    return render_template("index.html")

@app.route("/payment", methods=["POST"])
def post_payment():
    """ processes form input for url registration """
    content = request.form
    exists = db.session.query(User.id).filter_by(url=content["url"]).scalar() is not None
    if exists:
        row = User.query.filter(User.url == content["url"]).first()
        result = row2dict(row)
        return json.dumps({
            'status':'Fail',
            'reason':'This URL has already been registered',
            'data':result['address']}), 500
    else:
        pay_id = get_payment_id()
        try:
            user = User(
                address=content["address"],
                payment_id=pay_id,
                url=content["url"],
                message=content["message"],
                turtlehash=content["hash"],
                price=get_price(content["url"])
            )
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            app.logger.info(traceback.format_exc())
            return json.dumps({
                'status':'Fail',
                'reason':'Your transaction could not be processed'}), 500

        return json.dumps({
            'status':'Success',
            'payment_id': pay_id,
            'price': get_price(content["url"])}), 200

@app.route("/u/<user_url>")
def userpage(user_url):
    """ renders the shareable URL, checks if the page has been paid for """
    exists = db.session.query(User.id).filter_by(url=user_url).scalar()
    if exists is not None:
        user = row2dict(User.query.filter(User.url == user_url).first())
        paid = db.session.query(Payment.id).filter_by(payment_id=user["payment_id"]).scalar()
        user.pop('payment_id', None)
        if paid is not None:
            return render_template("user.html", user=user)
        return render_template("waiting.html", user=user)
    return abort(404)

@app.route("/u/<user_url>/edit")
def edit_page(user_url):
    """ renders the user edit page """
    pay_id = request.cookies.get('sessiontoken')
    if pay_id is not None:
        exists = User.query.filter_by(payment_id=pay_id).exists().scalar()
        if exists is not None:
            user = row2dict(User.query.filter(payment_id == pay_id).first())
            return render_template("edit.html", user=user)
        return json.dumps({
            'status':'Fail',
            'reason':'Invalid user authentication'}), 500
    return render_template("login.html")

@app.route("/login", methods=['POST'])
def login():
    """ verifies user payment_id and logs them in for editing """
    real = db.session.query(User.id).filter_by(payment_id=request.form["payment_id"]).scalar()
    paid = db.session.query(Payment.id).filter_by(payment_id=request.form["payment_id"]).scalar()

    if real is not None and paid is not None:
        resp = redirect(url_for("edit"))
        resp.set_cookie('sessiontoken', request.form["payment_id"])
        return json.dumps({
            'status':'Success',
            'data':'Login succeeded'}), 200
    if real is None:
        return json.dumps({
            'status':'Fail',
            'reason':"Payment ID doesn't exist!"}), 500
    if paid is None:
        user = row2dict(User.query.filter(payment_id == request.form["payment_id"]).first())
        return json.dumps({
            'status':'Fail',
            'reason':"Payment ID hasn't been paid",
            'price':user["price"]}), 500
