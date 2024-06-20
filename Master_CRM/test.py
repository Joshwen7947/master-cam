from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['username'] = username
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid Username or Password!")
        return render_template('index.html', error='Invalid username or password.')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template('index.html', error='Username already exists.')
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        session['user_id'] = new_user.id
        return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        user_id = session['user_id']
        tasks = Todo.query.filter_by(user_id=user_id).order_by(Todo.date_created).all()
        return render_template('dashboard.html', username=session['username'], tasks=tasks)
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/', methods=["POST"])
def add_task():
    if request.method == "POST":
        task_content = request.form['content']
        user_id = session['user_id']
        new_task = Todo(content=task_content, user_id=user_id)
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(f"Error:{e}")
            flash("Failed to add task.")
            return redirect(url_for('dashboard'))

@app.route("/delete/<int:id>")
def delete_task(id:int):
    task_to_delete = Todo.query.get_or_404(id)
    if task_to_delete.user_id != session.get('user_id'):
        flash("You don't have permission to delete this task.")
        return redirect(url_for('dashboard'))
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect(url_for('dashboard'))
    except Exception as e:
        return f"Error:{e}"

@app.route("/update/<int:id>", methods=["GET","POST"])
def update_task(id:int):
    task = Todo.query.get_or_404(id)
    if task.user_id != session.get('user_id'):
        flash("You don't have permission to update this task.")
        return redirect(url_for('dashboard'))
    if request.method == "POST":
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(f"ERROR:{e}")
            flash("Failed to update task.")
            return redirect(url_for('dashboard'))
    else:
        return render_template("update.html", task=task)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
