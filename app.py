from flask import Flask, redirect, url_for, render_template, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import *
from oauth import OAuthSignIn

app = Flask(__name__)
db = SQLAlchemy(app)
admin = Admin(app)
lm = LoginManager(app)
lm.login_view = 'index'
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quester.db'
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': '1063270763802788',
        'secret': '054c11ffb1a9f29fba3157a305b691cd'
    },
    'twitter': {
        'id': '73SF0RGxn2qJOUwPTbEAxAfJs',
        'secret': 'bBfeyq01hodLQNe4uvymqaAeDMTGgKWaI1nTV49ReqlCFu208h'
    }
}


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)
    img = db.Column(db.String(256), nullable=True)
    rating = db.Column(db.Integer, default=0)
    quests = db.relationship('Quest')


class Quest(UserMixin, db.Model):
    __tablename__ = "quests"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64), nullable=False)
    transport = db.Column(db.String(64), nullable=False)
    map_url = db.Column(db.Text, nullable=False)
    dots = db.Column(db.Text, nullable=False)
    pictures = db.Column(db.Text, nullable=False)
    done = db.Column(db.Boolean, nullable=True, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Quest, db.session))


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/contact')
def contact():
    return render_template("contact.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/quest", methods=["POST"])
def make_quest():
    type = request.form.get('quest_type')
    transport = request.form.get('quest_transport')
    start_street = request.form.get('street')
    return type + " " + transport + " " + start_street


# Authorize routes
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email, img = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email, img=img)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
