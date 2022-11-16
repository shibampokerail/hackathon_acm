from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
# from werkzeug.utils import secure_filename
import psycopg2
import os

app = Flask(__name__)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["2000 per day", "1000 per hour"],
    storage_uri="memory://",
)

CORS(app, support_credentials=True)

DEVELOPMENT = 'dev'
PRODUCTION = 'prod'

ENV = DEVELOPMENT

conn = psycopg2.connect(database="share_db", user="postgres",
                        password="12345", host="localhost")
# print("connected to the database")
# print("unable to connect to the database")
mycursor = conn.cursor()

if ENV == DEVELOPMENT:
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:12345@localhost/share_db'
else:
    # remote appdatabase uri
    app.config['SQLALCHEMY_DATABASE_URI'] = ''
    app.debug = False

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = 'uploaded_files'
if not os.path.exists('uploaded_files'):
    os.mkdir('uploaded_files')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_PATH'] = 30 * 1000 * 1000  # 30mb


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def file_upload(filerequest, name: str):
    if 'file' not in filerequest.files:
        flash('No file part')
        return redirect(filerequest.url)

    print(filerequest.files)
    file = filerequest.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(filerequest.url)
    if file and allowed_file(file.filename):
        # filename = secure_filename(file.filename)
        filename = name + "." + file.filename.rsplit('.', 1)[1].lower()
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('file', name=filename))


db = SQLAlchemy(app)


class RideShare(db.Model):
    __tablename__ = 'rideshare'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    start = db.Column(db.String(200))
    end = db.Column(db.String(200))
    date = db.Column(db.String(12))
    time = db.Column(db.String(12))
    request = db.Column(db.Integer)  # 0 for request 1 for offer
    phone_number = db.Column(db.String(200))
    no_of_people = db.Column(db.Integer)

    def __init__(self, name, start, end, date, time, request, phone_number, no_of_people):
        self.name = name
        self.start = start
        self.end = end
        self.date = date
        self.time = time
        self.request = request
        self.phone_number = phone_number
        self.no_of_people = no_of_people


class nearby_events(db.Model):
    __tablename__ = 'rideshare'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    start = db.Column(db.String(200))
    end = db.Column(db.String(200))
    date = db.Column(db.String(12))
    time = db.Column(db.String(12))

    def __init__(self, name, start, end, date, time, request, phone_number, no_of_people):
        self.name = name
        self.start = start
        self.end = end
        self.date = date
        self.time = time


class BookShare(db.Model):
    __tablename__ = 'bookshare'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    author = db.Column(db.String(200))
    contact_details = db.Column(db.String(200))
    description = db.Column(db.String(200))

    def __init__(self, name, author, contact_details, description):
        self.name = name
        self.author = author
        self.contact_details = contact_details
        self.description = description


class Feed(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200))
    name = db.Column(db.String(200))

    def __init__(self, text, name):
        self.text = text
        self.name = name


class NotesShare(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    user_name = db.Column(db.String(200))
    description = db.Column(db.String(200))
    course = db.Column(db.String(200))
    downloads = db.Column(db.Integer)

    def __init__(self, name, user_name, description, course, downloads):
        self.name = name
        self.user_name = user_name
        self.description = description
        self.course = course
        self.downloads = downloads


@app.route('/')
@cross_origin(supports_credentials=True)
def index():
    mycursor.execute("SELECT * FROM posts")
    posts = mycursor.fetchall()
    if request.args.get("show_webpage") == "1":
        return render_template('home.html', posts=posts)

    allowed_types = ["png", "jpg", "jpeg", "gif", "heif", "heic"]
    for i in posts:
        for type in allowed_types:
            uploaded_images = Path(f"/uploaded_files/feed_{i[0]}.{type}")
            if uploaded_images.exists():
                file_path = f"/uploaded_files/feed_{i[0]}.{type}"
                posts.append(file_path)
                break

    return posts


@app.route('/submit_text', methods=['POST'])
@cross_origin(supports_credentials=True)
def submit_text():
    if request.method == 'POST':
        text = request.json['text']
        name = request.json['name']
        # print(text)
        # text = request.form['text']
        if "file" in request.files:
            file_upload(request, "feed_" + str(db.session.query(Feed.id > 0).count()))

        if text == "":
            return {"error": "Empty Text field"}
        if name == "":
            return {"error": "Empty name field"}
        else:
            data = Feed(text, name)
            db.session.add(data)
            db.session.commit()
            return {"message": "Success"}


############rideshare#################################################


@app.route('/rideshare_form')
@cross_origin(supports_credentials=True)
def request_ride():
    requests = int(request.args.get('req_type'))
    return render_template('ride.html', request_=requests)


# returns available rides from database
@app.route('/display_rides')
@cross_origin(supports_credentials=True)
def rides():
    mycursor.execute("SELECT * FROM rideshare")
    rides = mycursor.fetchall()
    requests = int(request.args.get('req_type'))
    return {"rides": rides, "request_type": requests}


# stores submitted files from the json to db
@app.route('/submit_ride', methods=['POST'])
@cross_origin(supports_credentials=True)
def submit_ride():
    if request.method == 'POST':
        name = request.json["name"]
        start = request.json["start"]
        end = request.json["end"]
        date = request.json["date"]
        # print(date, type(date))
        time = request.json["time"]
        # print(time, type(time))

        no_of_people = int(request.json["no_of_people"]) if request.json["no_of_people"] != "" else 0
        try:
            request_ = request.json["request"]
            request_ = 1
        except:
            request_ = request.json["offer"]
            request_ = 0

        phone_number = (request.json["phone_number"]).replace("-", "")
        # print(customer,dealer,rating,comment)
        if name == "" or start == "" or end == "" or date == "" or time == "" or no_of_people == 0 or phone_number == "":
            return {"message": "One or more empty fields"}
        if db.session.query(RideShare).filter(RideShare.phone_number == phone_number).count() == 0:
            data = RideShare(name, start, end, date, time, request_, phone_number, no_of_people)
            db.session.add(data)
            db.session.commit()
            return {"message": "success"}
        return {"message": "Already submitted"}


#######################################rideshare####################################
#######################################request_book################################


@app.route('/share_book')
@cross_origin(supports_credentials=True)
def share_book():
    return render_template('book.html', request_=False)


@app.route('/display_books')
@cross_origin(supports_credentials=True)
def books():
    mycursor.execute("SELECT * FROM bookshare")
    all_books = mycursor.fetchall()
    books = []
    for i in all_books:
        books.append({"name": i[1], "author": i[2], "contact": i[3], "description": i[4]})
    return books


@app.route('/submit_book', methods=['POST'])
@cross_origin(supports_credentials=True)
def submit_book():
    if request.method == 'POST':
        name = request.json["name"]
        author = request.json["author"]
        contact_details = request.json["contact"]
        description = request.json["description"]
        # print(date, type(date))
        # print(time, type(time))
        try:
            request_ = request.json["request"]
            request_ = 1
        except:
            request_ = request.json["offer"]
            request_ = 0
        # print(customer,dealer,rating,comment)
        if name == "" or author == "" or contact_details == "":
            return {"message": "one or more empty fields"}
        else:
            data = BookShare(name, author, contact_details, description)
            db.session.add(data)
            db.session.commit()
            return {"message": "success"}


##################################books-end#########################################################
##################################noteshare#########################################################
@app.route('/share_note', methods=['POST', 'GET'])
@cross_origin(supports_credentials=True)
@limiter.limit('50 per day')
def share_notes():
    if request.method == 'POST':
        name = request.form["name"]
        user_name = request.form["username"]
        description = request.form["description"]
        course = request.form["course"]
        downloads = request.form["downloads"]
        check = [name, user_name, course, description, downloads]
        if "" in check:
            return {"message": "one or more empty fields: name,username,course,description,downloads,file"}
        else:
            data = NotesShare(name, user_name, description, course, downloads)
            db.session.add(data)
            db.session.commit()
            file_upload(request, str(db.session.query(NotesShare.id > 0).count()))
            return {"message": "success"}


@app.route('/display_notes')
@cross_origin(supports_credentials=True)
def notes():
    mycursor.execute("SELECT * FROM notes")
    all_notes = mycursor.fetchall()

    return all_notes


@app.route('/upload_note', methods=['POST', 'GET'])
@cross_origin(supports_credentials=True)
def file():
    return render_template("success.html")


#################################noteshare-end###################################################
@app.route('/submit_file', methods=['POST', 'GET'])
@cross_origin(supports_credentials=True)
@limiter.limit('50 per day')
def file_submit():
    if request.method == 'POST':
        # check if the post request has the file part
        return file_upload(request, "cat02")


if __name__ == "__main__":
    try:
        app.run(host="150.243.207.105", port=8000)
    except:
        app.run()
