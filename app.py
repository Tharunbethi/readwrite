from functools import wraps
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from passlib.handlers.sha2_crypt import sha256_crypt
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
import passlib.hash

app = Flask(__name__)
# config mysql
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'tharun'
app.config['MYSQL_DB'] = 'read&write'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# initialize MYSQL

mysql = MySQL(app)

#Articles = Articles()


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')




@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/articles')
def articles():
    cur = mysql.connection.cursor()
    result = cur.execute("select * from articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('articles.html', msg=msg)

    cur.close()
    # create cursor
     #cur = mysql.connection.cursor()

    # get articles
    #result = cur.execute("select * from articles")

    #articles = cur.fetchall()
    #if result > 0:
    #    return render_template('articles.html', articles=articles)
    #else:
    #    msg = 'No articles found'
    #    return render_template('articles.html', msg=msg)
    # close connection
    #cur.close()

# single article
@app.route('/article/<string:id>/')
def article(id):
    cur = mysql.connection.cursor()
    result = cur.execute("select * from articles where id = %s", [id])
    article = cur.fetchone()
    return render_template('article.html', article=article)


# register form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password ', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm password')


# register user
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = mysql.connection.cursor()
        cur.execute("insert into users(name,username,email,password) values(%s, %s , %s , %s)",
                    (name, email, username, password))

        # commit to db
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # cursor creation
        cur = mysql.connection.cursor()

        # get user by username
        result = cur.execute("select * from users where username = %s", [username])
        if result > 0:  # getting cursor password
            data = cur.fetchone()
            password = data['password']

            # compare password
            if sha256_crypt.verify(password_candidate, password):
                # if matcheds
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect((url_for('dashboard')))
                # app.logger.info('PASSWORD MATCHED')
            else:
                error1 = 'Invalid Login'
                return render_template('login.html', error=error1)
            # connection close
            cur.close()

        else:
            error = 'username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# check if user_logged in
"""def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('unauthorized ! Please login', 'danger')
            return redirect(url_for('login'))

    return wrap()"""


# logout
@app.route('/logout')

def logout():
    session.clear()
    flash('You are logged out', 'success')
    return redirect(url_for('login'))


# dashboard
@app.route('/dashboard')
#@is_logged_in
def dashboard():
    # create cursor
    cur =mysql.connection.cursor()

    #get articles
    result = cur.execute("select id,title,author,date from articles")

    articles = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html',msg=msg)
    #close connection
    cur.close()


    #return render_template('dashboard.html')


# article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = StringField('Body', [validators.Length(min=30)])


# Add article
@app.route('/add_article', methods=['GET', 'POST'])
#@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # create cursor
        cur = mysql.connection.cursor()

        # execution
        cur.execute("insert into articles(title,body,author) VALUES (%s , %s , %s)", (title, body , session['username']))

        # commit
        mysql.connection.commit()
        # close
        cur.close()

        flash('Article created', 'success')

        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

# Edit article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
#@is_logged_in
def edit_article(id):
    cur = mysql.connection.cursor()
    result = cur.execute("select * from articles where id = %s", [id])
    article = cur.fetchone()

    form = ArticleForm(request.form)

    #populate article fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # create cursor
        cur = mysql.connection.cursor()

        # execution
        cur.execute("update articles set title=%s,body=%s where id=%s",(title,body,id))
                    #(title,body,author) VALUES (%s , %s , %s)", (title, body , session['username']))

        # commit
        mysql.connection.commit()
        # close
        cur.close()

        flash('Article updated', 'success')

        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)

#delete article
@app.route('/delete_article/<string:id>', methods=['POST'])
def delete_article(id):
    cur = mysql.connection.cursor()
    cur.execute("delete from articles where id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('Article deleted','success')

    return redirect(url_for('dashboard'))





if __name__ == '__main__':
    app.secret_key = 'secret1234'
    app.run(debug=True)
