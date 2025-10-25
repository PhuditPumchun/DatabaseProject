# app.py (อัปเดต)

from flask import Flask, render_template, request, jsonify, redirect, url_for, session  # เดิม
from LoginServices import LoginServices
from InstructorDashboardServices import InstructorDashboardServices
from StudentDashboardServices import StudentDashboardServices  # [ADDED]

app = Flask(__name__)
# ตั้งค่า SECRET_KEY สำหรับการใช้งาน Session (จำเป็น)
app.config['SECRET_KEY'] = 'your_super_secret_key_here' 

# ----------------------------------------------------
# หน้า Login (GET) เหมือนเดิม
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

# ----------------------------------------------------
# API Login (AJAX/JS) ยังใช้เหมือนเดิม
# ----------------------------------------------------
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
