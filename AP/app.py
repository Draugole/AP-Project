#! /usr/bin/python3.8

from flask import Flask,render_template, redirect, request, url_for, jsonify, json,make_response
from flask_migrate import Migrate
from flask_restful import Api
from flask_jwt_extended import jwt_required, get_jwt_identity, unset_jwt_cookies, unset_access_cookies, unset_refresh_cookies

import time
import requests

from config import Config
from extensions import db, jwt
from models.user import User
from resources.reservation import ReservationListResource, ReservationResource
from resources.workspace import WorkspaceListResource, WorkspaceResource, AllWorkspaces
from resources.user import UserListResource, UserResource, MeResource, Test
from resources.token import TokenResource
from resources.refresh import TokenRefreshResource
from flask_marshmallow import Marshmallow
from models.workspace import Workspace
from models.reservation import Reservation
from models.user import User



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_REFRESH_COOKIE_PATH'] = '/'

    register_extensions(app)
    register_resources(app)

    return app


def register_extensions(app):
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)

def register_resources(app):
    api = Api(app)

    api.add_resource(UserListResource, '/users')
    api.add_resource(Test, '/Test')
    api.add_resource(UserResource, '/users/<string:username>')
    api.add_resource(MeResource, '/me')
    api.add_resource(ReservationListResource, '/reservations')
    api.add_resource(ReservationResource, '/reservations/<int:reservation_id>')
    api.add_resource(WorkspaceListResource, '/workspaces')
    api.add_resource(AllWorkspaces, '/allworkspaces')
    api.add_resource(WorkspaceResource, '/workspaces/<string:name>')
    api.add_resource(TokenResource, '/token')
    api.add_resource(TokenRefreshResource, '/token/refresh')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/test')
    def testi():
        requests.get('http://localhost:5000/Test')
        return render_template('index.html')


    @app.route('/login', methods=['GET', 'POST'])
    def logginIn():

        return render_template('login.html')

    @app.route('/hello',  methods=['GET'])
    @jwt_required
    def hello():
        workspaces= Workspace.query.all()
        user = get_jwt_identity()
        userid = User.get_by_username(user).id
        reservations = Reservation.query.filter_by(reservor=userid).all()
        reser = []
        for reservation in reservations:
            ids = reservation.workspace
            a = Workspace.get_by_id(ids)
            reservation.name = a.name
            reser.append(reservation)
        return render_template('reservations.html', reservations=reservations, workspaces=workspaces)

    @app.route('/reserve',  methods=['POST'])
    @jwt_required
    def reserve():
        data = request.form
        data2 = json.dumps(data)
        data3 = json.loads(data2)
        date = data3["datetime"]
        workspace = data3["workspace"]
        timeend = data3["timeend"]
        timestart = data3["timestart"]

        news = timestart.split(":")[0]
        newe = timeend.split(":")[0]
        print(news)
        if news < "13" or newe > "21":
            resp = make_response(redirect(url_for('hello')))
            return resp
        else:
            datetime = str(date) + "T" + timestart
            datetimeend = str(date) + "T" + timeend
            user = get_jwt_identity()
            print(user)
            userid = User.get_by_username(user).id

            resp = make_response(redirect(url_for('hello')))

            reservation = Reservation(
                reservor=userid,
                datetime=datetime,
                datetimeend=datetimeend,
                workspace=workspace
            )

            reservation.save()
            return resp

    @app.route('/dashboard', methods=['GET'])
    @jwt_required
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/token', methods=['POST'])
    def token():
        return redirect(url_for('index'))

    @app.route('/logout', methods=['POST'])
    def logout():
        resp = jsonify({'logout': True})
        unset_access_cookies(resp)
        unset_refresh_cookies(resp)
        unset_jwt_cookies(resp)
        return redirect(url_for('hello'))

    @app.route('/check', methods=['GET'])
    def check():
        data = request.args.get('jsdata')
        space = request.args.get('space')
        check_list = []
        reservations = Reservation.query.all()
        spaceid = Workspace.get_by_name(space).id
        print(spaceid)
        for reservation in reservations:
            if spaceid == reservation.workspace:
                newdate = str(reservation.datetime).split(" ")[0]
                if newdate == data:
                    d = str(reservation.datetime)
                    d2 = str(reservation.datetimeend)
                    date3 = d + " - " + d2
                    check_list.append(date3)
        if not reservations:
            check_list.append("No reservations")

        return render_template('reservationscheck.html', checklist=check_list)

    @app.route('/admin',  methods=['GET'])
    @jwt_required
    def admin():
        workspaces = Workspace.query.all()
        reservations = Reservation.query.all()
        reser = []
        for reservation in reservations:
            ids = reservation.workspace
            a = Workspace.get_by_id(ids)
            reservation.name = a.name
            reser.append(reservation)
        clients = User.query.all()
        return render_template('admin.html', reservations=reservations, workspaces=workspaces, clients=clients)

if __name__ == '__main__':
    app = create_app()
    app.run()