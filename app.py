import numpy as np
import pandas as pd
from flask import Flask, request,render_template,redirect,flash,url_for
from sklearn.metrics import roc_auc_score,accuracy_score,mean_squared_error
import pickle
import os
import urllib.request
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re


app = Flask(__name__)

app.secret_key = 'your secret key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'vimesh'
app.config['MYSQL_DB'] = 'hackathon'


# Intialize MySQL
mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])
def login():
    msg = 'Welcome'
    render_template('login_page.html',msg=msg)
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'user_name' in request.form and 'user_password' in request.form:
        # Create variables for easy access
        username = request.form['user_name']
        password = request.form['user_password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE user_name = %s AND user_password = %s', (username, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in database
        if account and account['user_id']!=1:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['user_name'] = account['user_name']
            #cursor.execute('UPDATE users SET last_login = current_timestamp() WHERE user_id=%s',(account['user_id']))
            # Redirect to home page
            return render_template('homepage.html') 
        elif account and account['user_id']==1:
        # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['user_name'] = account['user_name']
            #cursor.execute('UPDATE users SET last_login = current_timestamp() WHERE user_id=4')
            # Redirect to home page
            return render_template('homepage_admin.html')
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('login_page.html', msg=msg)

@app.route('/logout', methods=['POST'])
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   msg='You are logged out'
   return redirect(url_for('login'))

@app.route('/main', methods=['POST'])
def login_post():
    
    return render_template('homepage.html')

hack_id_1 = 1

@app.route('/classification', methods=['POST'])
def hackathon_1():
    global hack_id_1
    hack_id_1= request.form['hack_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM `hackathon`.`hackathon_list` where hack_id = %s', [hack_id_1])
    result = cursor.fetchall()
    count=0
    cursor1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor1.execute('INSERT INTO `hackathon`.`participation_list` (`hack_id`,`user_name`,`date_participated`) VALUES (%s,%s,current_time())', (hack_id_1,session['user_name']))
    mysql.connection.commit()
    cursor2 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor2.execute('update  hackathon_list set `num_participants` = %s where hack_id= %s', (count+1,hack_id_1))
    mysql.connection.commit()
    count+=1
    return render_template('hackathon_1.html',hack_id_1=result, content_type='application/json')

@app.route('/classification')
def upload_form():
    return render_template('hackathon_1.html')

UPLOAD_FOLDER = './uploads'
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['csv'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            count=0
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_file.csv'))
            flash('File successfully uploaded')
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('select answer_key, datasets from hackathon_list where hack_id=%s',[hack_id_1])
            files=cursor.fetchone()
            input_file=pd.read_csv('./uploads/uploaded_file.csv')
            answer_key=pd.read_csv(files['answer_key'])
            result_acc=accuracy_score(answer_key.iloc[:,1],input_file.iloc[:,1].dropna())
            count+=1
            cur = mysql.connection.cursor()
            cur.execute('''INSERT INTO hackathon_logs (`user_name`, `Accuracy_Score`,`Number_of_Submissions`,`Timestamp`,`hack_id`) VALUES(%s,%s,%s,current_timestamp(),%s)''',(session['user_name'],result_acc,count,hack_id_1))
            mysql.connection.commit()
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('select user_name, max(Accuracy_Score) as Accuracy_Score ,sum(Number_of_Submissions) as Submissions, max(`Timestamp`) as Time_Stamp from hackathon.hackathon_logs  where hack_id= %s group by user_name order by Accuracy_Score desc, Time_Stamp asc',[hack_id_1])
            result = cursor.fetchall()
            return render_template('hackathon_1.html',result_acc=result_acc)
            return render_template('hackathon_1.html',result=result, content_type='application/json')
        else:
            flash('Allowed file type is csv only')
            return redirect(request.url)

@app.route('/leader_board', methods=['POST'])
def leader_board():
    global hack_id_1
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('select user_name, max(Accuracy_Score) as Accuracy_Score ,sum(Number_of_Submissions) as Submissions, max(`Timestamp`) as Time_Stamp from hackathon.hackathon_logs  where hack_id= %s group by user_name order by Accuracy_Score desc, Time_Stamp asc',[hack_id_1])
    result = cursor.fetchall()
    return render_template('hackathon_1.html',result=result, content_type='application/json')

@app.route('/hackathon_list_admin', methods=['POST'])
def hackathon_list_admin():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM `hackathon`.`hackathon_list`')
    result = cursor.fetchall()
    return render_template('homepage_admin.html',result=result, content_type='application/json')
    
@app.route('/hackathon_list', methods=['POST'])
def hackathon_list():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM `hackathon`.`hackathon_list`')
    result = cursor.fetchall()
    return render_template('homepage.html',result=result, content_type='application/json')

@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        answer_key = request.form['answer_key']
        datasets = request.form['Datasets']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''INSERT INTO `hackathon_list` (`hackathon_title`,`hackathon_problem`,`date_created`,`answer_key`,`datasets`) VALUES (%s,%s,current_time(),%s,%s)''',(title,content,answer_key,datasets))
        mysql.connection.commit()
        return render_template('homepage_admin.html')    

@app.route('/delete_hackathon' ,methods=['POST'])
def delete_hackathon():
    global hack_id_1
    hack_id_1= request.form['hack_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM hackathon_list WHERE hack_id = %s', [hack_id_1])
    mysql.connection.commit()
    return render_template('homepage_admin.html')    

if __name__ == "__main__":
    app.run(debug=True)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
