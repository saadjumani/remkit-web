# http://flask.pocoo.org/docs/patterns/fileuploads/
import os
from flask import Flask, request, redirect, url_for, send_from_directory, jsonify, make_response, render_template, session
from werkzeug.utils import secure_filename
import hashlib
import html
from datetime import datetime
from datetime import date
import random
from tinydb import TinyDB, Query
import json

UPLOAD_FOLDER = 'organizations'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

SESSION_TYPE = 'redis'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = 'organizations'

app.secret_key = "rockstar"



org_path=os.path.join(os.path.normpath(app.root_path),"organizations")

#Make dir template
#Edit the second arg
#os.makedirs(os.path.join(os.path.normpath(org_path,"bomboclat"))

@app.route("/")
def hello():
    return "Front page coming soon! \n for now, please directly use the page links given to you"

@app.route('/static')
def static_prev():
	return "Not allowed"

@app.route('/genKey', methods=['GET', 'POST'])
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

@app.route('/no_shifts_found',methods=['GET', 'POST'])
def no_shifts_found():

	return render_template('not_signed_in.html')

@app.route('/view_shift', methods=['GET', 'POST'])
def view_shift():

	view_folder=request.form['view_folder']

	curr_folder_path=view_folder

	directories=os.listdir(curr_folder_path)
	directories=sorted(directories,reverse=True)
	card_markup=""
	temp=""
	card_markup_base= '''
    	<div class="card">
    	<a href="IMAGE_PATH">
          <img src="IMAGE_PATH" alt="Avatar" style="width:100%">
         </a>
          <div class="container">
            <h4><b>SCREENSHOT_TIME</b></h4>
          </div>
        </div>
	'''

	debugg=str(directories)


	for d in directories:
		pth=os.path.join(curr_folder_path,d)
		if(pth[-3:]=="png"):
			temp=card_markup_base
			temp=temp.replace("SCREENSHOT_TIME",d[11:-11].replace("_",":"))
			#Path needs to start from "organizations/" folder, not "var/
			temp=temp.replace("IMAGE_PATH",pth[27:])
			card_markup=card_markup+"\n"+temp

	return render_template('view_shift.html',card=card_markup)


@app.route('/emp_history',methods=['GET', 'POST'])
def emp_history():

	history_folder=request.form['history_folder']
	org_folder=session['org_folder']

	#curr_folder_path=os.path.join(org_path,org_folder)
	#curr_folder_path=os.path.join(curr_folder_path,history_folder)

	curr_folder_path=history_folder

	directories=os.listdir(curr_folder_path)
	directories=sorted(directories,reverse=True)

	card_markup=""
	temp=""
	card_markup_base= '''
    	<div class="card" style="width: 10rem;">
          <img src="organizations/folder_icon.png" alt="Avatar" style="width:100%">
          <div class="container">
            <h4><b>SHIFT_DATE</b></h4>
	            <form action="OPEN_FOLDER_URL" method=post>
	            	<input type="hidden" name="folder_name" value="OPN_FOLDER">
	            	<button type="submit" class="registerbtn">Open</button>
	            </form>
          </div>
        </div>
	'''
	for d in directories:
		if(os.path.isdir(os.path.join(curr_folder_path,d))):
			temp=card_markup_base
			temp=temp.replace("SHIFT_DATE",d)
			temp=temp.replace("OPEN_FOLDER_URL",url_for('view_shift',_external=True))
			temp=temp.replace("OPN_FOLDER",d)
			card_markup=card_markup+"\n"+temp

	return render_template('emp_history.html', card=card_markup)

@app.route('/org_dashboard', methods=['GET', 'POST'])
def org_dashboard():

	recent_session_url=url_for("view_shift",_external=True)
	recent_session_folder="temp"
	emp_history_url=url_for("emp_history",_external=True)
	emp_history_folder="temp"
	
	org_folder=session['org_folder']
	curr_folder_path = os.path.join(org_path,org_folder)

	temp=""

	directories=os.listdir(curr_folder_path)


	card_markup_base= '''
    	<div class="card">
          <img src="organizations/img_avatar.png" alt="Avatar" style="width:100%">
          <div class="container">
            <h4><b>USER NAME</b></h4>
            <p>Employee</p>
	            <form action="MOST_RECENT_URL" method=post>
	            	<input type="hidden" name="view_folder" value="MST_RECENT">
	            	<button type="submit" class="registerbtn">Most Recent</button>
	            </form>
	           	<form action="EMPLOYEE_HISTORY_URL" method=post>
	            	<input type="hidden" name="history_folder" value="EMP_HISTORY">
	            	<button type="submit" class="registerbtn">History</button>
	            </form>
          </div>
        </div>
	'''
	card_markup =""

	for d in directories:

		emp_history_folder=os.path.join(curr_folder_path,d)
		employee_history_dir_list=os.listdir(emp_history_folder)
		if(len(employee_history_dir_list)>0):
			dir_sorted=sorted(employee_history_dir_list,reverse=True)
			for f in dir_sorted:
				if(os.path.isdir(os.path.join(emp_history_folder,f))):
					recent_session_folder=os.path.join(emp_history_folder,f)
		else:
			recent_session_folder="_NONE"
		temp=card_markup_base
		temp=temp.replace("USER NAME",d)
		temp=temp.replace("MST_RECENT",recent_session_folder)
		temp=temp.replace("MOST_RECENT_URL",recent_session_url)
		temp=temp.replace("EMP_HISTORY",emp_history_folder)
		temp=temp.replace("EMPLOYEE_HISTORY_URL",emp_history_url)
		card_markup = card_markup + "\n"+temp

	return render_template('org_dashboard.html',card=card_markup)

@app.route('/org_login', methods=['POST'])
def org_login():

	email=request.form['email']
	password=request.form['password']

	db=TinyDB(os.path.join(org_path,"db.json"))
	orgs=db.table('organizations')
	org_q=Query()

	if(len(orgs.search(org_q.organization_email==email))>0):
		#Email exists
		if(len(orgs.search(org_q.organization_password==password))>0):

			temp=orgs.search(org_q.organization_email==email)[0]
			org_folder=temp['organization_name']
			session['org_folder']=org_folder
			return redirect(url_for('org_dashboard'))
		else:
			return "unrecognized password"
	else:
		return "Email not registered"



@app.route('/org_login_form', methods=['GET', 'POST'])
def org_login_form():
	login_url=url_for('org_login',_external=True)
	return render_template('org_login.html',org_login_url=login_url)

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

        uploader_n_data=uploader_data.read()
        uploader_m_data=uploader_n_data.decode("utf-8")
        uploader_data_json=json.loads(uploader_m_data)
        employee_id=uploader_data_json['name']
        organization_id=uploader_data_json['org']
        session_date=uploader_data_json['session_date']
        working_time=uploader_data_json['working_time']
        break_time=uploader_data_json['break_time']

        needed_path=os.path.join(org_path,organization_id)
        needed_path=os.path.join(needed_path,employee_id)
        needed_path=os.path.join(needed_path,session_date)

        db=TinyDB(os.path.join(needed_path,"session_data.json"))
        details=db.table('summary')
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        details.insert({'working_time':working_time, 'break_time': break_time})
    return '200'


@app.route('/org_registration_form', methods=['GET', 'POST'])
def org_reg_form():

	reg_url=url_for('register_org',_external=True)

	return render_template('register_organization.html',regurl=reg_url)

@app.route('/emp_reg_form', methods=['GET', 'POST'])
def emp_reg_form():

	req_url=url_for('register_emp',_external=True)
	return render_template('register_employee.html', emp_url=req_url)

@app.route('/img', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['img']
        uploader_data=request.files['json']
        uploader_n_data=uploader_data.read()
        uploader_m_data=uploader_n_data.decode("utf-8")
        uploader_data_json=json.loads(uploader_m_data)
        employee_id=uploader_data_json['name']
        organization_id=uploader_data_json['org']
        session_date=uploader_data_json['session_date']

        needed_path=os.path.join(org_path,organization_id)
        needed_path=os.path.join(needed_path,employee_id)
        needed_path=os.path.join(needed_path,session_date)

        if file and allowed_file(file.filename):
            print ('**found file', file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(needed_path, filename))
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
		path=os.path.join(os.path.normpath(app.root_path), app.config['UPLOAD_FOLDER'])
		path=os.path.join(path,"db.json")
		db=TinyDB(path)
		orgs=db.table('organizations')
		org_q = Query()
		if(orgs.search(org_q.organization_name == org_name)):
			print("An organization with this name already exists")
			return make_response("organization with this name already exists",403)
		
		if(orgs.search(org_q.organization_email==org_email)):
			return make_response("organization with this email already exists",403)
		else:
			if not os.path.exists(os.path.join(os.path.normpath(org_path),org_name)):
				os.makedirs(os.path.join(os.path.normpath(org_path),org_name))
			orgs.insert({
				'organization_name' : org_name,
				'organization_email':org_email,
				'organization_password' : org_encryped_password,
				'organization_registration_key' : org_emp_registration_key 
				})

			print("organization created")

		session['reg_key'] = org_emp_registration_key
		session['emp_reg_url']=url_for('emp_reg_form',_external=True)
		return redirect(url_for('org_registration_success'),code=307)

@app.route('/register_emp',methods=['POST'])
def register_emp():
		emp_id=request.form['employee_id']
		org_emp_registration_key=request.form['reg_key']
		org_emp_pass=request.form['password']
		db=TinyDB(os.path.join(org_path,"db.json"))
		orgs=db.table('organizations')
		org_q=Query()

		if(len(orgs.search(org_q.organization_registration_key==org_emp_registration_key))>0):
			temp_org=orgs.search(org_q.organization_registration_key==org_emp_registration_key)[0]
		else:
			return make_response('invalid regisration key', 401)

		print(temp_org)
		if(temp_org):
			org_name=temp_org['organization_name']
			needed_path = os.path.join(org_path,org_name)
			needed_path=os.path.join(needed_path,emp_id)
			if not os.path.exists(needed_path):
				os.makedirs(needed_path)
				f=open(os.path.join(needed_path,'emno.txt'),"w")
				f.write(org_emp_pass)
				session['org_name']=org_name
				session['emp_id']=emp_id
				return redirect(url_for('emp_registration_success'),code=307)

			else:
				print("user already exists")
				return make_response('user already exists', 403)

@app.route('/auth_emp',methods=['POST'])
def authenticate_emp():
	global org_path
	emp_id=request.form['employee_id']
	org_name=request.form['organization_name']
	emp_password=request.form['password']

	needed_path=os.path.join(org_path,org_name)
	needed_path=os.path.join(needed_path,emp_id)

	if (os.path.exists(needed_path) and org_name!="" and emp_id!=""):
		pwd_f=open(os.path.join(needed_path,'emno.txt'))
		pwd=pwd_f.read()
		if(pwd!=emp_password):
			return make_response('invalid password',403)
		
		datetoday=date.today()

		emp_path=os.path.join(needed_path,str(datetoday))
		if not(os.path.exists(emp_path)):
			os.makedirs(emp_path)
			x=open(os.path.join(emp_path,"session_data.json"),"w")
			x.close()

		db=TinyDB(os.path.join(emp_path,"session_data.json"))
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

        uploader_n_data=uploader_data.read()
        uploader_m_data=uploader_n_data.decode("utf-8")

        uploader_data_json=json.loads(uploader_m_data)
        employee_id=uploader_data_json['name']
        organization_id=uploader_data_json['org']
        session_date=uploader_data_json['session_date']
        current_status=uploader_data_json['current_status']

        needed_path=os.path.join(org_path,organization_id)
        needed_path=os.path.join(needed_path,employee_id)
        needed_path=os.path.join(needed_path,session_date)
        needed_path=os.path.join(needed_path,"session_data.json")

        db=TinyDB(needed_path)
        details=db.table('details')
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        details.insert({'current_status':current_status, 'time': current_time})

    return '200'

if __name__ == "__main__":
    app.run()

