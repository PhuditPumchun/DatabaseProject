from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from LoginServices import LoginServices
from InstructorDashboardServices import InstructorDashboardServices
from StudentDashboardServices import StudentDashboardServices
from RegistrationServices import RegistrationServices  # [ADDED]
from InstructorEditDashboardServices import InstructorEditDashboardServices
from StudentClassDetailServices import StudentClassDetailServices
from StudentProfileServices import StudentProfileServices

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_here' 

# --------------------------
# Login Page
# --------------------------
@app.route('/', methods=['GET'])
@app.route('/login', methods=['GET'])
def login_page():
    """แสดงฟอร์มล็อกอิน (login.html)"""
    # ใน login.html สามารถมีลิงก์ไป /register ได้
    return render_template('login.html')

# --------------------------
# Login API (AJAX/JS)
# --------------------------
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() if request.get_json() else request.form
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    response, status_code = LoginServices.authenticate(username, password, role)
    return jsonify(response), status_code

# --------------------------
# Login Form handler (POST)
# --------------------------
@app.route('/login', methods=['POST'])
def handle_login_form():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    response, status_code = LoginServices.authenticate(username, password, role)

    if response.get('success'):
        if role == 'instructor':
            session['iID'] = response.get('iID')
            session['iName'] = response.get('iName')
            return redirect(url_for('instructor_dashboard'))

        elif role == 'student':
            session['sID'] = response.get('sID')
            session['sName'] = response.get('sName')
            return redirect(url_for('student_dashboard'))

        else:
            redirect_url = response.get('redirect_url', url_for('login_page'))
            return redirect(redirect_url)
    else:
        return redirect(url_for('login_page'))

# --------------------------
# Instructor Dashboard (GET)
# --------------------------
@app.route('/instructor/dashboard', methods=['GET'])
def instructor_dashboard():
    iID = session.get('iID')
    iName = session.get('iName', 'Instructor')

    if not iID:
        return redirect(url_for('login_page'))

    dashboard_data = InstructorDashboardServices.get_dashboard_data(iID)

    if dashboard_data:
        return render_template(
            'instructor_dashboard.html',
            instructor_name=iName,
            data=dashboard_data
        )
    else:
        return "Error loading dashboard data.", 500
    
@app.route('/instructor/edit', methods=['GET'])
def instructor_edit_dashboard():
    iID = session.get('iID')
    iName = session.get('iName', 'Instructor')

    if not iID:
        return redirect(url_for('login_page'))

    current_data = InstructorDashboardServices.get_dashboard_data(iID)

    if current_data:
        return render_template(
            'instructorEditDashboard.html', 
            instructor_name=iName,
            data=current_data
        )
    else:
        return "Error loading data for editing.", 500

@app.route('/instructor/update', methods=['POST'])
def update_instructor():
    iID = session.get('iID')
    if not iID:
        return redirect(url_for('login_page'))

    tID        = request.form.get('tID', type=int)
    iName      = request.form.get('iName')
    tName      = request.form.get('tName')
    address    = request.form.get('address')
    mediaID     = request.form.get('mediaID', type=int)
    profile_url = request.form.get('profile_url') or None
    reward_url  = request.form.get('reward_url')  or None
    video_url   = request.form.get('video_url')   or None

    success = InstructorEditDashboardServices.update_data(
        iID=iID,
        tID=tID,
        iName=iName,
        tName=tName,
        address=address,
        mediaID=mediaID,
        profile_url=profile_url,
        reward_url=reward_url,
        video_url=video_url,
    )

    if success and iName:
        session['iName'] = iName

    return redirect(url_for('instructor_dashboard'))

# --------------------------
# Student Dashboard (GET)
# --------------------------
@app.route('/student/dashboard', methods=['GET'])
def student_dashboard():
    sID = session.get('sID')
    sName = session.get('sName', 'Student')

    if not sID:
        return redirect(url_for('login_page'))

    current_day = request.args.get('day', default="", type=str)

    dashboard_data = StudentDashboardServices.get_dashboard_data(
        sID,
        filter_day=current_day
    )

    if dashboard_data:
        return render_template(
            'student_dashboard.html',
            student_name=sName,
            data=dashboard_data,
            current_day=current_day
        )
    else:
        return "Error loading student dashboard data.", 500
    
@app.route('/student/class/<int:cID>', methods=['GET'])
def student_class_detail(cID):
    sID = session.get('sID')
    sName = session.get('sName')
    
    if not sID:
        return redirect(url_for('login_page'))
        
    class_detail = StudentClassDetailServices.get_class_detail(cID, sID)
    
    if class_detail:
        return render_template(
            'student_class_detail.html',
            student_name=sName,
            detail=class_detail
        )
    return f"Class ID {cID} not found or data error.", 404

# --------------------------
# Student Profile (GET)
# --------------------------
@app.route('/student/profile', methods=['GET'])
def student_profile():
    sID = session.get('sID')
    sName = session.get('sName')

    if not sID: 
        return redirect(url_for('login_page'))

    profile_data = StudentProfileServices.get_full_profile(sID)
    payment_history = StudentProfileServices.get_payment_history(sID)

    if profile_data and profile_data['profile']:
        return render_template(
            'student_profile.html',
            student_name=sName,
            profile=profile_data['profile'],
            enrolled_classes=profile_data['enrolled_classes'],
            payment_history=payment_history
        )
    return "Error loading student profile data.", 500

# --------------------------
# Student Edit Profile (GET)
# --------------------------
@app.route('/student/profile/edit', methods=['GET'])
def student_edit_profile():
    sID = session.get('sID')
    sName = session.get('sName')
    if not sID:
        return redirect(url_for('login_page'))

    profile_data = StudentProfileServices.get_full_profile(sID)
    payment_history = StudentProfileServices.get_payment_history(sID)

    if profile_data and profile_data['profile']:
        return render_template(
            'student_profile.html',
            student_name=sName,
            profile=profile_data['profile'],
            enrolled_classes=profile_data['enrolled_classes'],
            payment_history=payment_history,
            edit_mode=True
        )
    return "Error loading student profile for edit.", 500

# ==== Student Account (Edit form submit) ====
@app.route('/student/profile/update-account', methods=['POST'])
def student_update_account():
    cur_sid = session.get('sID')
    if not cur_sid:
        return redirect(url_for('login_page'))

    sName     = request.form.get('sName')
    sUsername = request.form.get('sUsername')
    new_sid   = request.form.get('new_sID', type=int)

    ok = StudentProfileServices.update_account(
        sID=cur_sid,
        new_sID=new_sid,
        sName=sName,
        sUsername=sUsername
    )

    if ok and new_sid:
        session['sID'] = new_sid
    if ok and sName:
        session['sName'] = sName

    return redirect(url_for('student_profile'))

# --------------------------
# Register
# --------------------------
@app.route('/register', methods=['GET'])
def register_select_role():
    return render_template('register.html')

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'GET':
        return render_template('register_student.html')

    name = request.form.get('name')
    username = request.form.get('username')
    password = request.form.get('password')

    result = RegistrationServices.register_student(name, username, password)

    if result.get('success'):
        return redirect(url_for('login_page'))
    else:
        return render_template(
            'register_student.html',
            error_msg=result.get('message', 'Registration failed.')
        )

@app.route('/register/instructor', methods=['GET'])
def register_instructor_placeholder():
    return render_template('register_instructor.html')

# --------------------------
# Logout
# --------------------------
@app.route('/logout')
def logout():
    session.pop('iID', None)
    session.pop('iName', None)
    session.pop('sID', None)
    session.pop('sName', None)
    return redirect(url_for('login_page'))

@app.route('/student/profile/update', methods=['POST'])
def student_update_profile():
    sID = session.get('sID')
    if not sID:
        return redirect(url_for('login_page'))

    sName = request.form.get('sName')
    sUsername = request.form.get('sUsername')
    sPassword = request.form.get('sPassword')  # optional

    ok = StudentProfileServices.update_profile(
        sID=sID,
        sName=sName,
        sUsername=sUsername,
        sPassword=sPassword
    )

    if ok and sName:
        session['sName'] = sName  # อัปเดตชื่อบน navbar/หัวหน้าเพจ

    return redirect(url_for('student_profile'))


# --------------------------
# Run Flask App
# --------------------------
if __name__ == '__main__':
    app.run(debug=True)

