
from flask import Flask, redirect, url_for, request, render_template, jsonify, flash, session, logging
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
from flask import Flask, redirect, request, jsonify
from keras.preprocessing import image
import tensorflow as tf
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
import numpy as np
from PIL import Image
from scipy.misc import imsave, imread, imresize
import io
import os
from passlib.hash import sha256_crypt


# Define a flask app

app = Flask(__name__)
app.debug = True
# config my sql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'venusai'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


# Model saved with Keras model.save()

##Load TB model
model = load_model('./models/full_tb_model.h5')
model.summary()
print('Model loaded')


@app.route('/', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')


@app.route('/predict', methods=['GET', 'POST'])
def upload():

    if request.method == 'POST':
        if request.files and 'file' in request.files:
            f = request.files['file']
            basepath = os.path.dirname(__file__)
            file_path = os.path.join(
                basepath, 'uploads', secure_filename(f.filename))
            f.save(file_path)

            # img = Image.open(io.BytesIO(img))
            img = image.load_img(file_path, target_size=(224, 224))
            img = image.img_to_array(img)
            # img = np.asarray(img)/255
            img = np.expand_dims(img, axis=0)

            pred = model.predict(img).tolist()

            response = {
                'predictions': {
                    'Healthy': round(pred[0][0], 3),
                    'TB': round(pred[0][1], 3)
                }
            }

            return str(response)
    return None

    # Register Class
    class RegisterForm(Form):
        name = StringField('Name', [validators.Length(min=1, max=50)])
        email = StringField('Email', validators.Length(min=6, max=25))
        password = PasswordField('Password', [validators.data_required(
        ), validators.EqualTo('confirm', message='Passwords do not match')])
        confirm = PasswordField('Confirm Password')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegisterForm(request.form)
        if request.method == 'POST' and form.validate():
            name = form.name.data
            email = form.email.data
            password = form.username.data

            password = sha256_crypt.encrypt(str(form.password.data))

            cur = mysql.connect.cursor()
            cur.execute("INSERT INTO users(name,email,username,password)VALUES(%S,%S,%S,%S)",
                        (name, email, username, password))
            mysql.connect.commit()
            cur.close()
            flash("You are now registered and can login", "success")

            return redirect(url_for('login'))

    return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', POST])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password_candidate = request.form['password']

            cur = mysql.connection.cursor()
            result = cur.execute(
                "SELECT * FROM users WHERE username =%s", ["username"])

            if result > 0:
                data = cur.fetchone()
                password = data['password']

            # compare passwords
                if sha256_crypt.verify(password_candidate, password):
                    session['logged_in'] = True
                    session['username'] = username

                    flash("You are logged in ", "success")
                    return redirect(url_for('index'))

                else:
                    error = "Invalid Login"
                    return render_template('login.html', error=error)
                cur.close()

            else:
                error = 'Username not found'
                return render_template('login.html', error=error)

    return render_template('login.html')


if __name__ == '__main__':
    # app.run(port=5002, debug=True)

    # Serve the app with gevent

    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()
