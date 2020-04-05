# http://flask.pocoo.org/docs/patterns/fileuploads/
import os
from flask import Flask, request, redirect, url_for, send_from_directory, jsonify, make_response, render_template, session
import flask
from werkzeug import secure_filename
import hashlib
import html
from datetime import datetime
from datetime import date
import random
from tinydb import TinyDB, Query
import json

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

SESSION_TYPE = 'redis'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "rockstar"

#Session(app)


if not os.path.exists('organizations'):
    os.makedirs('organizations')

def generate_key():
	key=''
	i=16
	while i>0:
		key=key+str(random.randrange(0,9))
		i=i-1
	return key

def allowed_file(filename):
  # this has changed from the original example because the original did not work for me
    return filename[-3:].lower() in ALLOWED_EXTENSIONS

@app.route('/org_dashboard', methods=['GET', 'POST'])
def org_dashboard():
	return render_template('org_dashboard.html')



@app.route('/org_registration_success', methods=['GET', 'POST'])
def org_registration_success():

	reg_key=session['reg_key']
	emp_reg_url=session['emp_reg_url']

	keyVals = {
	'key': reg_key,
	'emp_reg_url':emp_reg_url
	}
	return render_template('org_registration_success.html', key=keyVals['key'],emp_signup_url=keyVals['emp_reg_url'])

@app.route('/emp_registration_success', methods=['GET', 'POST'])
def emp_registration_success():

	employee_name=session['emp_id']
	organization_name=session['org_name']

	return render_template('emp_registration_success.html',org_name=organization_name,emp_id=employee_name)

@app.route('/emp_work_summary', methods=['GET', 'POST'])
def emp_work_summary():
    if request.method == 'POST':
        uploader_data=request.files['json']
        uploader_data_json=json.load(uploader_data)
        uploader_data=uploader_data.decode("utf-8")
        employee_id=uploader_data_json['name']
        organization_id=uploader_data_json['org']
        session_date=uploader_data_json['session_date']
        working_time=uploader_data_json['working_time']
        break_time=uploader_data_json['break_time']

        db=TinyDB("organizations\\"+organization_id+"\\"+employee_id+"\\"+session_date+ "\\session_data.json")
        details=db.table('summary')
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        details.insert({'working_time':working_time, 'break_time': break_time})
    return '200'

@app.route('/org_registration_form', methods=['GET', 'POST'])
def org_reg_form():
	return render_template('register_organization.html')

@app.route('/emp_reg_form', methods=['GET', 'POST'])
def emp_reg_form():
	return render_template('register_employee.html')

@app.route('/img', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['img']
        uploader_data=request.files['json']
        uploader_data_json=json.load(uploader_data)
        employee_id=uploader_data_json['name']
        organization_id=uploader_data_json['org']
        session_date=uploader_data_json['session_date']
        if file and allowed_file(file.filename):
            print ('**found file', file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join("organizations\\"+organization_id+"\\"+employee_id+"\\"+session_date, filename))
            return "200"
            # for browser, add 'redirect' function on top of 'url_for'
            #return url_for('uploaded_file',
            #                        filename=filename)
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/register_org',methods=['POST'])
def register_org():
	if request.method == 'POST':
		org_name=request.form['name']
		org_email=request.form['email']
		org_encryped_password=request.form['password']
		org_emp_registration_key=generate_key()

		db=TinyDB("db.json")
		orgs=db.table('organizations')
		org_q = Query()
		if(orgs.search(org_q.organization_name == org_name)):
			print("An organization with this name already exists")
			return make_response("organization with this name already exists",403)
		
		if(orgs.search(org_q.organization_email==org_email)):
			return make_response("organization with this name already exists",403)

		else:
			orgs.insert({
				'organization_name' : org_name,
				'organization_password' : org_encryped_password,
				'organization_registration_key' : org_emp_registration_key 
				})

			if not os.path.exists('organizations\\'+org_name):
				os.makedirs('organizations\\'+org_name)
			
			print("organization created")

		session['reg_key'] = org_emp_registration_key
		session['emp_reg_url']=url_for('emp_reg_form',_external=True)
		return redirect(url_for('org_registration_success'),code=307)

@app.route('/register_emp',methods=['POST'])
def register_emp():
		emp_id=request.form['employee_id']
		org_emp_registration_key=request.form['reg_key']
		org_emp_pass=request.form['password']
		db=TinyDB("db.json")
		orgs=db.table('organizations')
		org_q=Query()

		if(len(orgs.search(org_q.organization_registration_key==org_emp_registration_key))>0):
			temp_org=orgs.search(org_q.organization_registration_key==org_emp_registration_key)[0]
		else:
			return make_response('invalid regisration key', 401)

		print(temp_org)
		if(temp_org):
			org_name=temp_org['organization_name']
			if not os.path.exists('organizations\\'+org_name+'\\'+emp_id):
				os.makedirs('organizations\\'+org_name+'\\'+emp_id)
				f=open('organizations\\'+org_name+'\\'+emp_id+'\\emno.txt',"w")
				f.write(org_emp_pass)
				session['org_name']=org_name
				session['emp_id']=emp_id
				return redirect(url_for('emp_registration_success'),code=307)

			else:
				print("user already exists")
				return make_response('user already exists', 403)

@app.route('/auth_emp',methods=['POST'])
def authenticate_emp():
	emp_id=request.form['employee_id']
	org_name=request.form['organization_name']
	emp_password=request.form['password']

	if (os.path.exists('organizations\\'+org_name+'\\'+emp_id) and org_name!="" and emp_id!=""):
		pwd_f=open('organizations\\'+org_name+'\\'+emp_id+"\\emno.txt")
		pwd=pwd_f.read()
		if(pwd!=emp_password):
			return make_response('invalid password',403)
		datetoday=date.today()
		emp_path='organizations\\'+org_name+'\\'+emp_id+"\\"+str(datetoday)
		if not(os.path.exists(emp_path)):
			os.makedirs(emp_path)

		db=TinyDB(emp_path+"\\session_data.json")
		updates=db.table('details')

		now = datetime.now()
		current_time = now.strftime("%H:%M:%S")

		updates.insert({'Log-in time': current_time})
		
		return jsonify(curr_date =str(datetoday))
	else:
		return make_response('invalid employee ID or organization name',400)

@app.route('/status_update', methods=['GET', 'POST'])
def updateStatus():
    if request.method == 'POST':
        uploader_data=request.files['json']
        uploader_data=uploader_data.decode("utf-8")
        uploader_data_json=json.load(uploader_data)

        employee_id=uploader_data_json['name']
        organization_id=uploader_data_json['org']
        session_date=uploader_data_json['session_date']
        current_status=uploader_data_json['current_status']

        db=TinyDB("organizations\\"+organization_id+"\\"+employee_id+"\\"+session_date+ "\\session_data.json")
        details=db.table('details')
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        details.insert({'current_status':current_status, 'time': current_time})
    return '200'

if __name__ == '__main__':
	app.run(debug=True)

