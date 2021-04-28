from flask import Flask, render_template, redirect
from flask import request, abort
from forms.loginform import LoginForm
from data import db_session
from data.users import User
from data.notes import Note
from forms.user import RegisterForm
from forms.notes import NoteForm
from flask_login import LoginManager, login_user, login_required
from flask_login import logout_user, current_user


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        notes = db_sess.query(Note).filter(
            (Note.user == current_user) | (Note.is_private != True))
    else:
        notes = db_sess.query(Note).filter(Note.is_private != True)
    return render_template("index.html", notes=notes)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/note',  methods=['GET', 'POST'])
@login_required
def add_news():
    form = NoteForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        note = Note()
        note.title = form.title.data
        note.content = form.content.data
        note.is_private = form.is_private.data
        current_user.notes.append(note)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('notes.html', title='Добавление записи',
                           form=form)


@app.route('/note/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NoteForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        note = db_sess.query(Note).filter(Note.id == id,
                                          Note.user == current_user
                                          ).first()
        if note:
            form.title.data = note.title
            form.content.data = note.content
            form.is_private.data = note.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        note = db_sess.query(Note).filter(Note.id == id,
                                          Note.user == current_user
                                          ).first()
        if note:
            note.title = form.title.data
            note.content = form.content.data
            note.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('notes.html',
                           title='Редактирование записи',
                           form=form
                           )


@app.route('/note_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    note = db_sess.query(Note).filter(Note.id == id,
                                      Note.user == current_user
                                      ).first()
    if note:
        db_sess.delete(note)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


def main():
    db_session.global_init("db/blogs.db")
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
