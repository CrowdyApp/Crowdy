from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import json
import sys
import random
# import populartimes
import datetime
from theater import theater
from flask_mongoengine import MongoEngine, Document
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, Length, InputRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

labels = [
    '6am', '7am', '8am', '9am',
    '10am', '11am', '12pm', '1pm',
    '2pm', '3pm', '4pm', '5pm', '6pm', '7pm', '8pm', '9pm',
    '10pm', '11pm', '12am', '1am', '2am', '3am', '4am', '5am'
]

colors = [
	"#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA",
	"#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
	"#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]

app.config['MONGODB_SETTINGS'] = {
	'db': 'crowdy',
	'host': 'mongodb://schan2023:crowdyapp123@ds027748.mlab.com:27748/crowdy'
}

db = MongoEngine(app)
app.config['SECRET_KEY'] = 'CEN3031'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#Homepage
@app.route('/')
def index():
	return render_template('/index.html')

class Theater(db.EmbeddedDocument):
    theaterName = db.StringField()
    theaterAddress = db.StringField()

class Movie(db.EmbeddedDocument):
    movieName = db.StringField()
    movieDescription = db.StringField()
    poster = db.StringField()

class User(UserMixin, db.Document):
    meta = {'collection': 'users'}
    name = db.StringField()
    email = db.StringField(max_length=30)
    password = db.StringField()
    location = db.StringField()
    favorites = db.ListField(db.EmbeddedDocumentField(Movie))
    theaters = db.ListField(db.EmbeddedDocumentField(Theater))

@login_manager.user_loader
def load_user(user_id):
	return User.objects(pk=user_id).first()

#FORMS
class RegForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(max=30)])
    email = StringField('Email',  validators=[InputRequired(), Email(message='Invalid email'), Length(max=30)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=1, max=20)])
    location = StringField('Location',  validators=[InputRequired(), Length(max=30)])

class LogForm(FlaskForm):
	email = StringField('Email',  validators=[InputRequired(), Email(message='Invalid email'), Length(max=30)])
	password = PasswordField('Password', validators=[InputRequired(), Length(min=1, max=20)])

#Register user
@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegForm()
	if request.method == 'POST':
		if form.validate():
			existing_user = User.objects(email=form.email.data).first()
			if existing_user is None:
				hashpass = generate_password_hash(form.password.data, method='sha256')
				user = User(form.name.data,form.email.data,hashpass,form.location.data).save()
				login_user(user)
				return redirect(url_for('dashboard'))
	return render_template('register.html', form=form)

#User login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated == True:
		return redirect(url_for('dashboard'))
	form = LogForm()
	if request.method == 'POST':
		if form.validate():
			check_user = User.objects(email=form.email.data).first()
			if check_user:
				if check_password_hash(check_user['password'], form.password.data):
					login_user(check_user)
					return redirect(url_for('dashboard'))
	return render_template('login.html', form=form)

#User logout
@app.route('/logout', methods = ['GET'])
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

#Retrieves all theaters by location and radius
@app.route('/dashboard', methods = ['POST', 'GET'])
@login_required
def dashboard():
    location = None
    keyword = None

    if request.method == 'POST':
        if request.form.get('inputLocation') and request.form.get('inputTheater'):
            location = request.form.get('inputLocation')
            keyword = request.form.get('inputTheater')
        else:
            if request.form.get('inputLocation'):
                location = request.form.get('inputLocation')
            else:
                location = current_user.location
            if request.form.get('inputTheater'):
                keyword = request.form.get('inputTheater')
    else:
        location = current_user.location
        keyword=''

    radius = 35000
    #Converts location string to longitude and latitude radiusString
    geocodeUrl = "https://maps.googleapis.com/maps/api/geocode/json"
    paramsGeocode = dict(
    	address=location,
    	key='AIzaSyBBABVNXk90RVdvQqgDanDifw-bgMGeONI'
    )
    resp = requests.get(url=geocodeUrl, params=paramsGeocode).content
    respParse = json.loads(resp)
    lng = str(respParse["results"][0]["geometry"]["location"]["lng"])
    lat = str(respParse["results"][0]["geometry"]["location"]["lat"])

    userLocationDict = dict(
        latitude=lat,
        longitude=lng
    )
    #Finds movie theaters based on longitude and latitude and radius
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = dict(
    	location=lat + ',' + lng,
    	radius=radius,
    	type='movie_theater',
    	key='AIzaSyBBABVNXk90RVdvQqgDanDifw-bgMGeONI',
        keyword=keyword
    )
    data = requests.get(url=url, params=params).content
    parseData = json.loads(data)
    list = []

    for item in parseData["results"]:
        tempT = theater()
        tempT.name = item["name"]
        tempT.address = item["vicinity"]
        tempT.place_id = item["place_id"]
        tempT.lat = item["geometry"]["location"]["lat"]
        tempT.lng = item["geometry"]["location"]["lng"]
        list.append(tempT)

    return render_template('display_theaters.html', list=list, userLocationDict=userLocationDict, name=current_user.name)

@app.route('/pop', methods=['GET', 'POST'])
def pop():
    if request.method == 'POST':
        day = datetime.datetime.now()
        select = (str(request.form.get('place')))

    res = [0, 0, 0, 0, 0, 0, 0, 0, 26, 35]
    for j in range(9):
        res.append(random.randint(38, 43))

    res.append(33)
    res.append(28)

    day = day.strftime("%A")
    if day == 'Monday':
        curr = 0
    if day == 'Tuesday':
        curr = 1
    if day == 'Wednesday':
        curr = 2
    if day == 'Thursday':
        curr = 3
    if day == 'Friday':
        curr = 4
    if day == 'Saturday':
        curr = 5
    if day == 'Sunday':
        curr = 6

    bar_labels=labels
    return render_template('popular_times.html', title='Popular Times', max=50, labels=bar_labels, times=res)

@login_required
@app.route('/user', methods=['GET'])
def userProfile():
    return render_template('user_profile.html', user=current_user)

@app.route('/movies')
def moviesPage():
    movies = []
    movie1 = Movie("firstmovie", "last", "poster")
    movie2 = Movie("secondmovie", "third", "poster2")
    movies.append(movie1)
    movies.append(movie2)
    return render_template('movies.html', movies=movies)

@app.route('/fave-theaters', methods=['POST'])
def fave_theater():
    if request.method == 'POST':
        name = (str(request.form.get('nameInput')))
        address = (str(request.form.get('addressInput')))

    current_theaters = current_user.theaters
    newTheater = Theater(name, address)
    current_theaters.append(newTheater)
    current_user.theaters = current_theaters
    current_user.save()
    return redirect(url_for('dashboard'))

@app.route('/fave-movies', methods=['POST'])
def fave_movie():
    if request.method == 'POST':
        name = (str(request.form.get('nameInput')))
        description = (str(request.form.get('descriptionInput')))
        poster = (str(request.form.get('posterInput')))

    current_favorites = current_user.favorites
    newMovie= Movie(name, description, poster)
    current_favorites.append(newMovie)
    current_user.favorites = current_favorites
    current_user.save()
    return redirect(url_for('moviesPage'))

if __name__ == '__main__':
    app.run(debug = True)
