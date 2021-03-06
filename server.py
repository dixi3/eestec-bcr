from flask import Flask, request, redirect, url_for, render_template, jsonify, session
import pymysql
import os
import random
import string
import subprocess
from werkzeug.utils import secure_filename
from passporteye import read_mrz
import re

app = Flask(__name__)

UPLOAD_FOLDER = './upload'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
uploaded = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)
def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
class Database:
	def __init__(self):
		host = "127.0.0.1"
		user = "userdb"
		password = "password"
		db = "bcrdb"
		self.con = pymysql.connect(host=host, user=user, password=password, db=db, cursorclass=pymysql.cursors.
								   DictCursor)
		self.cur = self.con.cursor()
	def list_users(self):
		self.cur.execute("SELECT id, name, password FROM users LIMIT 50")
		result = self.cur.fetchall()
		return result
	def list_clienti(self):
		self.cur.execute("SELECT id, name, surname, birth, mrz, resend, resendcode FROM clienti LIMIT 50")
		result = self.cur.fetchall()
		return result
	# DA STIU SQL INJECTION + PAROLA VIZIBILA	
	def login_query(self, name, password):
		self.cur.execute("SELECT id FROM users WHERE NAME=%s AND PASSWORD=%s;",( name, password))

		result = self.cur.fetchall()
		return result

	def update_resend(self, resend_link, idcode):
		self.cur.execute("UPDATE clienti SET resendcode = %s WHERE id= %s;",(resend_link, idcode) )
		self.con.commit()
		result = self.cur.fetchall()    
		return result
	
	def query_resend(self,resendcode):
		self.cur.execute("SELECT id FROM clienti WHERE resendcode=%s;",str(resendcode))
		result = self.cur.fetchall()
		return result

	def query_mrz(self, mrzcode):
		self.cur.execute("SELECT id FROM clienti WHERE mrz=%s;", str(mrzcode))
		result = self.cur.fetchall()
		return result
	def update_client(self, name, surname, birth, idcode):
		self.cur.execute("UPDATE clienti SET name =%s , surname=%s, birth=%s  WHERE id= %s;",(name, surname, birth, idcode) )
		self.con.commit()
		result = self.cur.fetchall()    
		return result

	def update_send_final(self, idcode):
		self.cur.execute("UPDATE clienti SET resendcode = NULL WHERE id= %s ", idcode )
		self.con.commit()
		result = self.cur.fetchall()    
		return result

@app.route('/', methods=['GET', 'POST'])
def get():
	if 'username' in session:
		#username = session['username']

		db = Database()
		result = db.list_clienti()

		resid = ""
		#for res in result:
		#    resid = res["id"] 
		#for res in result:
		#    print(res["mrz"])
		if request.method == 'POST':
			idcode = request.form.get('mess')
			print(idcode[0])
			resendcode=''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
			print(resendcode)
			#resend_link=url_for('get') resendcode
			response =  db.update_resend(str(resendcode), str(idcode[0]))
			print(response)
			result = db.list_clienti()
			#for res in result:
		#    resid = res["id"]
			return render_template("tables.html", clienti= result, user=session['username'])
		return render_template("tables.html", clienti= result, user=session['username'])
	else:
		return redirect(url_for('login'))

a = ["Andrei", "Ioana", "Adelin"]



@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		#data = request.form['email']
		#res = ""
		email = request.form.get('email')
		password = request.form.get('password')
		db = Database()
		result = db.login_query(email,password)
		if len(result) == 0:
			error= "No user found with this credentials"
			return render_template("login.html", error= error)
		else:
			session['username'] = email
			return redirect(url_for('get'))
	return render_template("login.html")


@app.route('/tables', methods=['GET'])
def tables():
	return redirect(url_for('get'))

@app.route('/results')
def results():
	if uploaded:
		return '''
			<!doctype html>
			<h1>Upload an image first</h1>'''
	else:	
		path = request.args.get('path')
		resendcode = request.args.get('resendcode')
		name = request.args.get('name')
		surname = request.args.get('surname')
		birth = request.args.get('birth')
		if path != "":
			ret=["not yet"]
			print(path)
			#subprocess.check_output(['bash', '-c', 'export '])
			#output = ""
			#try:
			#	output = subprocess.check_output(['bash', '-c', 'mrz ' + path])
			#except subprocess.CalledProcessError as e:
			#	raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
			#output = output.decode('utf-8')
			#os.putenv("TESSDATA_PREFIX", "/home/")
			mrz = read_mrz(path)
			#mrzcode =int(filter(str.isdigit,mrz[1]))
			#print(mrz)
			#arr = mrz.split(',')
			#l1 = arr[0].split(' ')
			#l2 = arr[1].split(' ')
			mrzcode = str(re.search(r'\d+', str(mrz.to_dict().get('number'))).group(0))
			db = Database()
			resmrz = db.query_mrz(mrzcode)
			resresend = db.query_resend(resendcode)
			resid1=""
			resid2=""
			if(len(resmrz) != 0):
				for resmrzi in resmrz:
					resid1 = resmrzi["id"]
			else:
				return render_template("fail.html")

			if(len(resresend) != 0):
				for resresendi in resresend:
					resid2 = resresendi["id"]
			else:
				return render_template("fail.html")#"resend code expired"

			if(resid1 == resid2):
				db.update_client(name,surname,birth, resid1)
				db.update_send_final(resid1)
				return render_template("succes.html")#"changed data"
			else:
				return render_template("fail.html")#"not your link"

			print(mrzcode)
			#return render_template('result.html', pat1=l1[0] , pat2=l2[0] ,scor1=l1[1] , scor2=l2[1] )
			return str(mrzcode)

		return '''
				 <!doctype html>
				 <h1>UPLOADED BUT</h1>'''

@app.route('/link/<code>', methods= ['GET', 'POST'])
def link(code):
	if request.method == 'POST':
		#file = request.files.get('file')
		if 'file' not in request.files:
		#	#flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		print(str(request.files.get('file')))
		# if user does not select file, browser also
		# submit a empty part without filename
		if file.filename == '':
			#flash('No selected file')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
			uploaded = True
			print(request.form.get('name'))
			return redirect(url_for('results', path=path, resendcode= code, name = request.form.get('name'), surname = request.form.get('surname'), birth = request.form.get('birth')))
	return render_template("form.html", code=code)

# @app.route('/form', methods=['GET'])
# def form():
# 	return render_template("form.html")

@app.route('/index', methods=['GET'])
def index():
	if 'username' in session:
		return render_template("index.html")
	else:
		return redirect(url_for('login'))


# @app.route('/fail', methods=['GET'])
# def fail():
#	return render_template("fail.html")

@app.route('/success', methods=['GET'])
def success():
	return render_template("succes.html")