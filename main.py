#Import Statements-----------------------------------------------------------------------------------------------------------

from flask import Flask, redirect, url_for, render_template, request, session, flash
import random
import math
from datetime import timedelta, datetime
from flask_sqlalchemy import SQLAlchemy


#Config-----------------------------------------------------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "shree"
app.permanent_session_lifetime = timedelta(seconds=30)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///users.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


#DB Init-----------------------------------------------------------------------------------------------------------------------
db = SQLAlchemy(app)


#DB Create Tables--------------------------------------------------------------------------------------------------------------
class appointments(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    first = db.Column(db.String(100))
    last = db.Column(db.String(100))
    mob = db.Column(db.String(10))
    prob = db.Column(db.String(300))
    dateandtime = db.Column(db.DateTime())

    def __init__(self, first, last, mob, prob, dateandtime):
        self.first = first
        self.last = last
        self.mob = mob
        self.prob = prob
        self.dateandtime = dateandtime

class history(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    first = db.Column(db.String(100))
    last = db.Column(db.String(100))
    mob = db.Column(db.String(10))
    prob = db.Column(db.String(300))
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    dateMod = db.Column(db.String(20))
    timeMod = db.Column(db.String(20))
    action = db.Column(db.String(50))

    def __init__(self, first, last, mob, prob, date, time, dateMod, timeMod, action):
        self.first = first
        self.last = last
        self.mob = mob
        self.prob = prob
        self.date = date
        self.time = time
        self.dateMod = dateMod
        self.timeMod = timeMod
        self.action = action


#custom Functions------------------------------------------------------------------------------------------------------------------
def generateOTP():
    OTP = random.uniform(0.1,1)
    OTP *=1000000
    OTP = math.floor(OTP)
    OTP = str(OTP)
    return OTP


#Landing Page----------------------------------------------------------------------------------------------------------------------
@app.route("/")
def lPage():
    return render_template("index.html")

#Booking Page----------------------------------------------------------------------------------------------------------------------
#if method == POST -> Get Mob no -> Check if already in appointments -> if not -> Gen OTP and send -> redirect to otp verification page
#if method == get -> if session already ongoing then redirect to otp verification page(probably closed by mistake) -> if no session exists means render booking template

@app.route("/book", methods = ["GET", "POST"])
def book():
    #Handling POST request
    if request.method == "POST":
        #Get Mob No
        mobNo = request.form["number"]
        found_user = appointments.query.filter_by(mob = mobNo).first()
        if not found_user:
            session.permanent = True
            session["number"] = mobNo
            #Generate Random OTP
            OTP = generateOTP()
            session["otp"] = OTP
            session["tries"]=3
            #redirect for OTP
            return redirect(url_for("otp"))
        else:
            flash("Appointment Already Booked!")
            return redirect(url_for("book"))
    else:
        #if session already ongoing, then redirect to otp verification page
        if "number" in session:
            return redirect(url_for("otp"))
        else:
            return render_template("booking.html")

#OTP verification page---------------------------------------------------------------------------------------------------------------------------------------------
#If method == post -> and session ongoing -> verify otp entered by user -> if correct, go to fill info -> if wrong otp entered, decrease tries. if tries = 0 pop all session and redirect to booking.
#if method == post and no session exist -> this means session timed out while filling otp. so flash 'timed out' and go to booking
#if method == get and session exist -> nornal usecase. just render otp verification page. -> if sesison does not exist -> bad request. redirect to booking.
@app.route("/otp", methods = ["GET", "POST"])
def otp():
    if request.method == "POST":
        if "number" in session:
            otpin = request.form["otpentered"]
            if otpin == session["otp"]:
                return redirect(url_for("fillinfo"))
            elif session["tries"] != 1:
                session["tries"]-=1
                triesLeft = session["tries"]
                flash(f"Wrong OTP Entered. Attempts Left - {triesLeft}")
                return redirect(url_for("otp"))
            else:
                session.pop("number", None)
                session.pop("otp", None)
                session.pop("tries", None)
                flash("3 Wrong Attempts. Please re-register")
                return redirect(url_for("book"))

        else:
            flash("Session Timed out. Please try again.")
            return redirect(url_for("book"))
    
    else:
        if "number" in session:
            return render_template("otp.html", otpee = session["otp"])
        else:
            return redirect(url_for("book"))

#Info filling page--------------------------------------------------------------------------------------------------------------------------------------------------
#if method == post and session ongoing -> request all the parameters and add to DB and render successful page
#if method == post and no session ongoing, it must have timed out while filling out. so flash message and go to booking
#if method == get and session ongoing render actual info filling page with mobile number already in place
# if method == get and no session exists this means bad request. redirect to booking
@app.route("/fillinfo", methods = ["GET", "POST"])
def fillinfo():
    if request.method == "POST":
        if "number" in session:
            first = request.form["first"]
            last = request.form["last"]
            prob = request.form["prob"]
            current = datetime.now()
            patient = appointments(first, last, str(session["number"]), prob, current)
            db.session.add(patient)
            db.session.commit()
            session.pop("number", None)
            session.pop("otp", None)
            session.pop("tries", None)
            return render_template("success.html", f=first, l=last, p=prob)
        else:
            flash("Session Timed out. Please try again.")
            return redirect(url_for("book"))
    else:
        if "number" in session:
            return render_template("fillinfo.html", mob=session["number"])
        else:
            return redirect(url_for("book"))




#Delete Appointment Page-------------------------------------------------------------------------------------------------------------------------------------------------
#Takes in phone number, checks if it is there in data base. if there, create session and verify otp for appointment deletion.
#if phone number not in database give error
#if method is get and session already present redirect to otp verification
#method is get and no active session, normal usecase, render template
@app.route("/deleteappointment", methods=["GET", "POST"])
def delete():
    #Handling POST request
    if request.method == "POST":
        #Get Mob No
        mobNo = request.form["number"]
        found_user = appointments.query.filter_by(mob = mobNo).first()
        if found_user:
            session.permanent = True
            session["number"] = mobNo
            #Generate Random OTP
            OTP = generateOTP()
            session["otp"] = OTP
            session["tries"]=3
            #redirect for OTP
            return redirect(url_for("otpDelete"))
        else:
            flash(f"No appointment found for entered number")
            return redirect(url_for("book"))
    else:
        #if session already ongoing, then redirect to otp verification page
        if "number" in session:
            return redirect(url_for("otpDelete"))
        else:
            return render_template("delete.html")

#Verify otp for Deletion of mobile number
#same as booking otp.
#if otp verified correctly go to confirm delete page.
@app.route("/otpDelete", methods = ["GET", "POST"])
def otpDelete():
    if request.method == "POST":
        if "number" in session:
            otpin = request.form["otpentered"]
            if otpin == session["otp"]:
                return redirect(url_for("confirmDelete"))
            elif session["tries"] != 1:
                session["tries"]-=1
                triesLeft = session["tries"]
                flash(f"Wrong OTP Entered. Attempts Left - {triesLeft}")
                return redirect(url_for("otpDelete"))
            else:
                session.pop("number", None)
                session.pop("otp", None)
                session.pop("tries", None)
                flash("3 Wrong Attempts. Please re-attempt")
                return redirect(url_for("book"))

        else:
            flash("Session Timed out. Please try again.")
            return redirect(url_for("book"))
    
    else:
        if "number" in session:
            return render_template("otpDelete.html", otpee = session["otp"])
        else:
            return redirect(url_for("book"))

#ask whether to confirm delete
#same logic as other forms
#once confirmed, delete from the database
@app.route("/confirmDelete", methods = ["GET", "POST"])
def confirmDelete():
    if request.method == "POST":
        if "number" in session:
            appointments.query.filter_by(mob = session["number"]).delete()
            db.session.commit()
            session.pop("number", None)
            session.pop("otp", None)
            session.pop("tries", None)
            flash("User successfully deleted")
            return redirect(url_for("book"))
        else:
            flash("Session Timed out. Please try again.")
            return redirect(url_for("book"))
    else:
        if "number" in session:
            return render_template("confirmDelete.html")
        else:
            return redirect(url_for("book"))


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)