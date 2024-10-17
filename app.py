from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key_here"  # Add a secret key for session management
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///school_management.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Set the login view

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # Add a type column to distinguish between students and teachers

class Student(User):
    __mapper_args__ = {"polymorphic_identity": "student"}
    grades = db.relationship("Grade", backref="student", lazy=True)

class Teacher(User):
    __mapper_args__ = {"polymorphic_identity": "teacher"}
    courses = db.relationship("Course", backref="teacher", lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher.id"), nullable=False)

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grade = db.Column(db.String(5), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        user_type = request.form.get("user_type")
        name = request.form.get("name")

        if User.query.filter_by(username=username).first():
            flash("Username already exists!")
        else:
            user = Student(username=username, name=name) if user_type == "student" else Teacher(username=username, name=name)
            db.session.add(user)
            db.session.commit()
            flash("User  registered successfully!")

        return redirect(url_for("index"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        user = User.query.filter_by(username=username).first()

        if user:
            login_user(user)
            return redirect(url_for("dashboard", username=username))
        else:
            flash("Invalid username!")

    return render_template("login.html")

@app.route("/dashboard/<username>")
@login_required
def dashboard(username):
    user = User.query.filter_by(username=username).first()
    if user.type == "student":
        user_courses = user.grades
    else:
        user_courses = Course.query.filter_by(teacher_id=user.id).all()
    user_messages = Message.query.filter_by(recipient_id=user.id).all()
    return render_template("dashboard.html", user=user, courses=user_courses, messages=user_messages)

@app.route("/add_grade/<username>", methods=["POST"])
@login_required
def add_grade(username):
    grade = request.form.get("grade")
    student = Student.query.filter_by(username=username).first()
    if student:
        new_grade = Grade(grade=grade, student=student)
        db.session.add(new_grade)
        db.session.commit()
        flash("Grade added successfully!")
    else:
        flash("Invalid student username!")

    return redirect(url_for("dashboard", username=username))

@app.route("/create_course", methods=["POST"])
@login_required
def create_course():
    course_name = request.form.get("course_name")
    teacher_username = request.form.get("teacher_username")
    teacher = Teacher.query.filter_by(username=teacher_username).first()

    if teacher:
        new_course = Course(name=course_name, teacher_id=teacher.id)
        db.session.add(new_course)
        db.session.commit()
        flash(f"Course '{course_name}' created successfully!")
    else:
        flash("Invalid teacher username!")

    return