from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, User, UserRole
from email.utils import parseaddr
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import and_


application = Flask(__name__)
application.config.from_object(Configuration)

@application.route("/register", methods = ["POST"])
def register():
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    username = request.json.get("username", "")
    password = request.json.get("password", "")
    passwordConfirmation = request.json.get("passwordConfirmation", "")
    role = request.json.get("role", "")

    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0
    emailEmpty = len(email) ==0
    usernameEmpty = len(username) == 0
    passwordEmpty = len(password) == 0
    passwordConfirmationEmpty = len(passwordConfirmation) == 0
    roleEmpty = len(role) == 0


    if(forenameEmpty or surnameEmpty or emailEmpty or usernameEmpty or \
            passwordEmpty or passwordConfirmationEmpty or roleEmpty ):
        return Response ( "All fields required!", status=400)

    result = parseaddr(email)
    if( len(result[1]) == 0):
        return Response ("Email invalid!", status = 400)

    if (role == "tourist"):
        user = User (forename = forename, surname = surname, email = email, username = username, password = password)
        database.session.add(user)
        database.session.commit()
        userRole = UserRole (userId = user.id, roleId=1)
        database.session.add(userRole)
        database.session.commit()

        return Response("Registration successful!", status=200)

    return Response("Waiting dor admin to respond!", status=200)

jwt = JWTManager( application )

@application.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", "")
    password = request.json.get("password", "")

    usernameEmpty = len(username) == 0
    passwordEmpty = len(password) == 0

    if (usernameEmpty or passwordEmpty):
        return Response("All fields required!", status=400)

    user = User.query.filter(and_(User.username == username, User.password == password)).first()
    if( not user):
        return Response("Invalid credentials!", status=400)

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "email": user.email,
        "roles" : [str(role) for role in user.roles]

    }
    accessToken = create_access_token(identity=user.username, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.username, additional_claims=additionalClaims)

    #return Response(accessToken, status=200)
    return jsonify(accessToken = accessToken, refreshToken = refreshToken)

@application.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid!"

@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additonalClaims = {
        "forename" : refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "email": refreshClaims["email"],
        "roles": refreshClaims["roles"]

    }
    return Response( create_access_token(identity= identity, additional_claims=additonalClaims), status = 200)


if(__name__ == "__main__"):
    database.init_app(application)
    application.run(debug=True, port=5000)

