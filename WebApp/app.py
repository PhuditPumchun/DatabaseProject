from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from LoginServices import LoginServices
from InstructorDashboardServices import InstructorDashboardServices
from StudentDashboardServices import StudentDashboardServices
from RegistrationServices import RegistrationServices  # [ADDED]
from InstructorEditDashboardServices import InstructorEditDashboardServices

app = Flask(__name__)
# ต้องมี SECRET_KEY สำหรับใช้ session
app.config['SECRET_KEY'] = 'your_super_secret_key_here' 

@app.route('/', methods=['GET'])
@app.route('/login', methods=['GET'])
def login_page():
    # แสดงฟอร์มล็อคอิน (login.html)
    # ใน login.html เราจะใส่ลิงก์ไป /register เพิ่ม
    return render_template('login.html')

# --------------------------
# Login API (AJAX/JS) - ถ้ามีเรียกใช้
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
            # fallback เผื่อ role แปลก (ไม่น่ามี)
            redirect_url = response.get('redirect_url', url_for('login_page'))
            return redirect(redirect_url)
    else:
        # ล็อกอินไม่ผ่าน -> กลับหน้า login
        # (ถ้าอยากแสดง error message สวย ๆ ให้ใช้ flash แล้วโชว์ใน template)
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

# --------------------------
# Student Dashboard (GET)
# --------------------------
@app.route('/student/dashboard', methods=['GET'])
def student_dashboard():
    # session info
    sID = session.get('sID')
    sName = session.get('sName', 'Student')

    if not sID:
        return redirect(url_for('login_page'))

    # NEW: read optional filter
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
            current_day=current_day  # <- pass to template
        )
    else:
        return "Error loading student dashboard data.", 500

# =================================================================
# [ADDED] Register routes
# =================================================================

@app.route('/register', methods=['GET'])
def register_select_role():
    """
    หน้าเลือก role: Student / Instructor
    """
    return render_template('register.html')

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    """
    GET  -> แสดงฟอร์มสมัครนักเรียน
    POST -> รับข้อมูลจากฟอร์มและสมัคร
    """
    if request.method == 'GET':
        return render_template('register_student.html')

    # ถ้าเป็น POST
    name = request.form.get('name')
    username = request.form.get('username')
    password = request.form.get('password')

    result = RegistrationServices.register_student(name, username, password)

    if result.get('success'):
        # สมัครเสร็จ -> กลับหน้า login ให้ลองล็อคอินได้เลย
        return redirect(url_for('login_page'))
    else:
        # สมัครไม่ผ่าน เช่น username ซ้ำ
        # ตรงนี้เราง่าย ๆ: render หน้าเดิมแล้วโชว์ error
        # (ถ้าอยากสวย ใช้ flash แล้วแสดงใน template)
        return render_template(
            'register_student.html',
            error_msg=result.get('message', 'Registration failed.')
        )

@app.route('/register/instructor', methods=['GET'])
def register_instructor_placeholder():
    """
    หน้านี้ยังไม่ทำจริง แต่สร้าง route ไว้ไม่ให้ 404
    """
    return render_template('register_instructor.html')

# --------------------------
# Logout
# --------------------------
@app.route('/logout')
def logout():
    # เคลียร์ session ทั้ง instructor / student
    session.pop('iID', None)
    session.pop('iName', None)
    session.pop('sID', None)
    session.pop('sName', None)
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)
