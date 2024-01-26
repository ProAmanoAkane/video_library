import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

SERVER_URL = "http://server:5001"


class LoginForm(FlaskForm):
    username = StringField("Username")
    password = PasswordField("Password")
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    username = StringField("Username")
    password = PasswordField("Password")
    submit = SubmitField("Register")


class VideoForm(FlaskForm):
    title = StringField("Title")
    actor1 = StringField("Actor 1")
    actor2 = StringField("Actor 2")
    actor3 = StringField("Actor 3")
    director = StringField("Director")
    genre = StringField("Genre")
    year = IntegerField("Year")
    submit = SubmitField("Submit")


@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    error_message = ""
    if form.validate_on_submit():
        response = requests.get(
            f"{SERVER_URL}/users.json?username={form.username.data}",
            headers={"x-api-key": os.environ["API_KEY"]},
        )
        if response.status_code == 200:
            user = response.json()
            if check_password_hash(user["password"], form.password.data):
                session["username"] = form.username.data
                return redirect(url_for("video_library"))
        error_message = "Mauvais utilisateur ou mot de passe"
    return render_template("login.html", form=form, error_message=error_message)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = {
            "username": form.username.data,
            "password": generate_password_hash(form.password.data),
        }
        response = requests.post(
            f"{SERVER_URL}/users.json",
            json=new_user,
            headers={"x-api-key": os.environ["API_KEY"]},
        )
        if response.status_code == 200:
            return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/library.json", methods=["GET"])
def video_library():
    if "username" not in session:
        return redirect(url_for("login"))
    response = requests.get(
        f'{SERVER_URL}/library/{session["username"]}',
        headers={"x-api-key": os.environ["API_KEY"]},
    )
    if response.status_code == 200:
        data = [value for value in response.json().values()]
        return render_template("video_library.html", movies=data)
    else:
        return f"Error: Unable to fetch data from {SERVER_URL}, status code: {response.status_code}"


@app.route("/add_video", methods=["GET", "POST"])
def add_video():
    if "username" not in session:
        return redirect(url_for("login"))
    form = VideoForm()
    error_message = ""
    if form.validate_on_submit():
        response = requests.get(
            f'{SERVER_URL}/library/{session["username"]}',
            headers={"x-api-key": os.environ["API_KEY"]},
        )
        if response.status_code == 200:
            data = response.json()
            if not form.title.data.lower() in data:
                new_video = {
                    form.title.data.lower(): {
                        "title": form.title.data,
                        "actors": [
                            form.actor1.data,
                            form.actor2.data,
                            form.actor3.data,
                        ],
                        "director": form.director.data,
                        "genre": form.genre.data,
                        "year": form.year.data,
                    }
                }
                response = requests.post(
                    f'{SERVER_URL}/library/{session["username"]}',
                    json=new_video,
                    headers={"x-api-key": os.environ["API_KEY"]},
                )
                if response.status_code == 200:
                    return redirect(url_for("video_library"))
                else:
                    error_message = f"Erreur: Impossible d'ajouter un nouveau film à {SERVER_URL}, code d'état: {response.status_code}"
    return render_template("add_video.html", form=form, error_message=error_message)


@app.route("/delete_video/<title>", methods=["GET"])  # supprimer un film
def delete_video(title):
    if "username" not in session:
        return redirect(url_for("login"))
    response = requests.delete(
        f'{SERVER_URL}/library/{session["username"]}?title={title}',
        headers={"x-api-key": os.environ["API_KEY"]},
    )
    if response.status_code == 200:
        return redirect(url_for("video_library"))
    else:
        return f"Error: Unable to delete movie at {SERVER_URL}, status code: {response.status_code}"


@app.route("/logout")  # logout
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
