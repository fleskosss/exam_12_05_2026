from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.config['SECRET_KEY'] = 'qwjdiuqwudiiiui12$jqj!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    requests = db.relationship('Request', backref='user', lazy=True)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    requests = db.relationship('Request', backref='course', lazy=True)


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def courses():
    all_courses = Course.query.all()
    return render_template('index.html', courses=all_courses)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Неправильный логин или пароль', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/course/<int:course_id>')
def course_page(course_id):

    course = Course.query.get_or_404(course_id)

    requests = Request.query.filter_by(
        course_id=course.id
    ).all()

    return render_template(
        'course.html',
        course=course,
        requests=requests
    )


@app.route('/course/<int:course_id>/create-request', methods=['GET', 'POST'])
@login_required
def create_request(course_id):

    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':

        text = request.form['text']

        new_request = Request(
            text=text,
            user_id=current_user.id,
            course_id=course.id
        )

        db.session.add(new_request)
        db.session.commit()

        return redirect(
            url_for(
                'course_page',
                course_id=course.id
            )
        )

    return render_template(
        'create_request.html',
        course=course
    )


if __name__ == '__main__':

    with app.app_context():

        db.create_all()

        # Проверяем, есть ли уже курсы
        if not Course.query.first():

            courses = [

                Course(
                    title='Python Basics',
                    description='Изучение основ Python'
                ),

                Course(
                    title='Flask Development',
                    description='Создание сайтов на Flask'
                ),

                Course(
                    title='SQL Fundamentals',
                    description='Работа с базами данных'
                )
            ]

            db.session.add_all(courses)
            db.session.commit()

            print('Courses created')

    app.run(debug=True)