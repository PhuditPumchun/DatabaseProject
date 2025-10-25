# app.py

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from LoginServices import LoginServices
from InstructorDashboardServices import InstructorDashboardServices
# แก้ไข: เปลี่ยนชื่อคลาสที่ Import ให้เป็น InstructorEditDashboardServices
from InstructorEditDashboardServices import InstructorEditDashboardServices

app = Flask(__name__)
# ต้องมี SECRET_KEY สำหรับใช้ session
app.config['SECRET_KEY'] = 'your_super_secret_key_here' 

# ----------------------------------------------------
# A. Login & API Routes
# ----------------------------------------------------
@app.route('/', methods=['GET'])
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() if request.get_json() else request.form
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    response, status_code = LoginServices.authenticate(username, password, role)
    return jsonify(response), status_code

@app.route('/login', methods=['POST'])
def handle_login_form():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    response, status_code = LoginServices.authenticate(username, password, role)

    if response.get('success') and role == 'instructor':
        session['iID'] = response.get('iID')
        session['iName'] = response.get('iName')
        return redirect(url_for('instructor_dashboard'))
    elif response.get('success') and role == 'student':
        # สำหรับ Student (ถ้า implement)
        return redirect("https://www.youtube.com/watch?v=u_c1tRmj7E4")
    else:
        # ล็อกอินล้มเหลว
        return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.pop('iID', None) 
    session.pop('iName', None) 
    return redirect(url_for('login_page'))


# ----------------------------------------------------
# B. Instructor Dashboard Routes
# ----------------------------------------------------
@app.route('/instructor/dashboard', methods=['GET'])
def instructor_dashboard():
    iID = session.get('iID')
    iName = session.get('iName', 'Instructor')

    if not iID:
        return redirect(url_for('login_page'))

    dashboard_data = InstructorDashboardServices.get_dashboard_data(iID)

    if dashboard_data:
        return render_template('instructor_dashboard.html', 
                                instructor_name=iName,
                                data=dashboard_data)
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
        return render_template('instructorEditDashboard.html', 
                                instructor_name=iName,
                                data=current_data)
    else:
        return "Error loading data for editing.", 500

@app.route('/instructor/update', methods=['POST'])
def update_instructor():
    iID = session.get('iID')
    
    if not iID:
        return redirect(url_for('login_page'))

    # รับค่าจากฟอร์ม
    tID = request.form.get('tID', type=int)
    iName = request.form.get('iName')
    tName = request.form.get('tName')
    address = request.form.get('address')
    
    # เรียกใช้ Service ที่ถูกต้อง
    success = InstructorEditDashboardServices.update_data(
        iID=iID,
        tID=tID,
        iName=iName,
        tName=tName,
        address=address
    )
    
    if success:
        session['iName'] = iName # อัปเดตชื่อใน Session
    # else:
        # flash('Update failed!', 'danger')

    return redirect(url_for('instructor_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)