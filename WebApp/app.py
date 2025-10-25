# app.py (อัปเดต)
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Flask
from LoginServices import LoginServices
from InstructorDashboardServices import InstructorDashboardServices
from StudentDashboardServices import StudentDashboardServices  # [ADDED]
from InstructorEditDashboardServices import InstructorEditDashboardServices

app = Flask(__name__)
# ต้องมี SECRET_KEY สำหรับใช้ session
app.config['SECRET_KEY'] = 'your_super_secret_key_here' 

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

    if response.get('success'):
        if role == 'instructor':
            # เก็บ iID/iName ไว้ใน Session สำหรับ Instructor Dashboard
            session['iID'] = response.get('iID')
            session['iName'] = response.get('iName')
            
            # ไปหน้า instructor dashboard
            return redirect(url_for('instructor_dashboard'))

        elif role == 'student':   # [ADDED]
            # เก็บ sID/sName ไว้ใน Session สำหรับ Student Dashboard
            session['sID'] = response.get('sID')
            session['sName'] = response.get('sName')

            # ไปหน้า student dashboard
            return redirect(url_for('student_dashboard'))

        else:
            # fallback: ถ้ามี redirect_url อื่น
            redirect_url = response.get('redirect_url')
            return redirect(redirect_url)

    else:
        # ล็อกอินล้มเหลว: กลับ login (จริงๆ ควร flash error)
        return redirect(url_for('login_page'))


# ----------------------------------------------------
# Instructor Dashboard (เหมือนเดิม)
# ----------------------------------------------------
@app.route('/instructor/dashboard', methods=['GET'])
def instructor_dashboard():
    iID = session.get('iID')
    iName = session.get('iName', 'Instructor')

    if not iID:
        return redirect(url_for('login_page'))

    # ดึงข้อมูลทั้งหมดจาก Service เดิม
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

# ----------------------------------------------------
# [ADDED] Student Dashboard ใหม่
# ----------------------------------------------------
@app.route('/student/dashboard', methods=['GET'])
def student_dashboard():
    sID = session.get('sID')
    sName = session.get('sName', 'Student')

    if not sID:
        return redirect(url_for('login_page'))

    # ดึงข้อมูลหน้า dashboard ของนักเรียน
    dashboard_data = StudentDashboardServices.get_dashboard_data(sID)

    if dashboard_data:
        return render_template(
            'student_dashboard.html',
            student_name=sName,
            data=dashboard_data
        )
    else:
        return "Error loading student dashboard data.", 500

# ----------------------------------------------------
# Logout (แก้เล็กน้อย ให้เคลียร์ของ student ด้วย)
# ----------------------------------------------------
@app.route('/logout')
def logout():
    """ล้างข้อมูล session และ Redirect ไปยังหน้า Login"""
    
    # ลบตัวแปร instructor/student ออกจาก session
    session.pop('iID', None) 
    session.pop('iName', None) 
    session.pop('sID', None)      # [ADDED]
    session.pop('sName', None)    # [ADDED]
    
    # กลับหน้า login
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)
