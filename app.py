from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import psycopg2

app = Flask(__name__)

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
app.config['UPLOAD_FOLDER'] = 'uploaded_images'
app.config['MAX_CONTENT_PATH'] = 10000000

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

    def __init__(self, text):
        self.text = text


@app.route('/')
def index():
    mycursor.execute("SELECT * FROM posts")
    posts = mycursor.fetchall()
    return render_template('home.html', posts=posts)


@app.route('/submit_text', methods=['POST'])
def submit_text():
    if request.method == 'POST':
        text = request.form['text']
        if text == "":
            return redirect('/')
        else:
            data = Feed(text)
            db.session.add(data)
            db.session.commit()
            return redirect('/')

        ############rideshare#################################################


@app.route('/rideshare_form')
def request_ride():
    requests = int(request.args.get('req_type'))
    return render_template('ride.html', request_=requests)


@app.route('/display_rides')
def rides():
    mycursor.execute("SELECT * FROM rideshare")
    rides = mycursor.fetchall()
    requests = int(request.args.get('req_type'))
    return render_template('rides.html', rides=rides, requests=requests)


@app.route('/submit_ride', methods=['POST'])
def submit_ride():
    if request.method == 'POST':
        name = request.form["name"]
        start = request.form["start"]
        end = request.form["end"]
        date = request.form["date"]
        print(date, type(date))

        time = request.form["time"]
        print(time, type(time))

        no_of_people = int(request.form["no_of_people"]) if request.form["no_of_people"] != "" else 0
        try:
            request_ = request.form["request"]
            request_ = 1
        except:
            request_ = request.form["offer"]
            request_ = 0

        phone_number = (request.form["phone_number"]).replace("-", "")
        # print(customer,dealer,rating,comment)
        if name == "" or start == "" or end == "" or date == "" or time == "" or no_of_people == 0 or phone_number == "":
            return render_template('ride.html', message="Please enter the empty fields")
        if db.session.query(RideShare).filter(RideShare.phone_number == phone_number).count() == 0:
            data = RideShare(name, start, end, date, time, request_, phone_number, no_of_people)
            db.session.add(data)
            db.session.commit()
            return redirect('/')
        return render_template('ride.html', message="You have already submitted a request")


#######################################rideshare####################################
#######################################request_book################################


@app.route('/share_book')
def share_book():
    return render_template('book.html', request_=False)


@app.route('/display_books')
def books():
    mycursor.execute("SELECT * FROM bookshare")
    books = mycursor.fetchall()
    return render_template('books.html', books=books)


@app.route('/submit_book', methods=['POST'])
def submit_book():
    if request.method == 'POST':
        name = request.form["name"]
        author = request.form["author"]
        contact_details = request.form["contact"]
        description = request.form["description"]
        # print(date, type(date))
        # print(time, type(time))
        try:
            request_ = request.form["request"]
            request_ = 1
        except:
            request_ = request.form["offer"]
            request_ = 0
        # print(customer,dealer,rating,comment)
        if name == "" or author == "" or contact_details == "":
            return render_template('book.html', message="Please enter the empty fields", request=request_)
        else:
            data = BookShare(name, author, contact_details, description)
            db.session.add(data)
            db.session.commit()
            return redirect('/')


if __name__ == "__main__":
    try:
        app.run(host="150.243.211.234", port=8000)
    except:
        app.run()
