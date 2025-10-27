from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from LoginServices import LoginServices
from InstructorDashboardServices import InstructorDashboardServices
from StudentDashboardServices import StudentDashboardServices
from RegistrationServices import RegistrationServices  # [ADDED]
from InstructorEditDashboardServices import InstructorEditDashboardServices
from StudentClassDetailServices import StudentClassDetailServices
from StudentEnrollmentServices import StudentEnrollmentServices
from StudentPaymentServices import StudentPaymentServices
from StudentProfileServices import StudentProfileServices
from RegistrationServices import RegistrationServices

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
    # Route นี้ใช้สำหรับแสดงหน้าหลักของ Dashboard
    iID = session.get('iID')
    iName = session.get('iName', 'Instructor')
    if not iID: return redirect(url_for('login_page'))
    
    # NOTE: ต้องมั่นใจว่า get_dashboard_data ดึง sID ของ Instructor มาด้วย
    dashboard_data = InstructorDashboardServices.get_dashboard_data(iID)
    
    if dashboard_data:
        return render_template('instructor_dashboard.html', instructor_name=iName, data=dashboard_data)
    return "Error loading instructor dashboard data.", 500

@app.route('/instructor/edit', methods=['GET'])
def instructor_edit_dashboard():
    # Route นี้ใช้แสดงหน้าฟอร์มสำหรับแก้ไข
    iID = session.get('iID')
    iName = session.get('iName', 'Instructor')

    if not iID: return redirect(url_for('login_page'))
    
    current_data = InstructorDashboardServices.get_dashboard_data(iID)
    
    # **ดึง Subject List สำหรับ Dropdown**
    subject_list = InstructorDashboardServices.get_subject_list()

    if current_data:
        return render_template(
            'InstructorEditDashBoard.html', 
            instructor_name=iName,
            data=current_data,
            subject_list=subject_list
        )
    return "Error loading data for editing.", 500


@app.route('/instructor/update', methods=['POST'])
def update_instructor():
    # Route นี้ใช้รับค่าจากฟอร์ม Update และเรียกใช้ Service
    iID = session.get('iID')
    
    if not iID: return redirect(url_for('login_page'))

    # รับค่าจากฟอร์ม (ใช้ .get() เพื่อป้องกัน KeyError)
    tID = request.form.get('tID', type=int)
    mediaID = request.form.get('mediaID', type=int)
    subjectID = request.form.get('subjectID', type=int) # NEW: Subject ID
    
    # ข้อมูล Profile/Center
    iName = request.form.get('iName')
    iUsername = request.form.get('iUsername') # NEW: Username
    iPassword = request.form.get('iPassword') # NEW: Password
    tName = request.form.get('tName')
    address = request.form.get('address')
    
    # ข้อมูล Media URL
    profile_url = request.form.get('profile_url')
    reward_url = request.form.get('reward_url')
    video_url = request.form.get('video_url')

    success = InstructorEditDashboardServices.update_data(
        iID=iID,
        tID=tID,
        mediaID=mediaID,
        iName=iName,
        iUsername=iUsername,
        iPassword=iPassword, 
        tName=tName,
        address=address,
        profile_url=profile_url,
        reward_url=reward_url,
        video_url=video_url,
        subjectID=subjectID # NEW: Subject ID
    )
    
    if success:
        session['iName'] = iName 
    
    return redirect(url_for('instructor_dashboard'))


@app.route('/instructor/delete', methods=['POST'])
def delete_instructor_account():
    # Route นี้ใช้รับคำขอ Delete Account
    iID = request.form.get('iID', type=int) # รับ iID จาก Hidden Field ใน Modal Form
    
    # ตรวจสอบความถูกต้องของ Session
    if not session.get('iID') or session.get('iID') != iID:
        # อาจเป็นการโจมตี CSRF หรือ Session หมดอายุ
        return redirect(url_for('login_page'))
    
    success = InstructorEditDashboardServices.delete_account(iID)
    
    if success:
        # ลบบัญชีสำเร็จ: ล้าง Session และ Redirect ไปหน้า Login
        session.pop('iID', None) 
        session.pop('iName', None)
    
    # ไม่ว่าจะสำเร็จหรือไม่ (ถ้าล้มเหลวให้ถือว่าควรไปหน้า Login เพื่อความปลอดภัย)
    return redirect(url_for('login_page'))


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


@app.route('/student/enroll/<int:cID>', methods=['POST'])
def enroll_class(cID):
    sID = session.get('sID')
    if not sID: return redirect(url_for('login_page'))

    # ต้องดึง feeAmount จาก form ที่ส่งมา
    feeAmount = request.form.get('feeAmount', type=float)

    if feeAmount is None:
        print("Enrollment failed: feeAmount missing in form data.")
        return redirect(url_for('student_class_detail', cID=cID))


    success = StudentEnrollmentServices.enroll_student(sID, cID, feeAmount)

    if success:
        # Redirect ไปหน้า Payment History ใน Student Profile
        return redirect(url_for('student_profile') + '#payment-history')
    else:
        print("Enrollment failed: Database error.")
        return redirect(url_for('student_class_detail', cID=cID))
    
@app.route('/student/profile/confirm_payment/<int:cID>', methods=['POST'])
def confirm_payment(cID):
    sID = session.get('sID')
    if not sID: return redirect(url_for('login_page'))
        
    success = StudentPaymentServices.confirm_payment(sID, cID)
    
    if success:
        # Redirect กลับไปหน้า Payment History
        return redirect(url_for('student_profile') + '#payment-history')
    else:
        print(f"Payment confirmation failed for sID={sID}, cID={cID}")
        # สามารถเพิ่ม flash message แจ้งเตือนความล้มเหลวได้
        return redirect(url_for('student_profile') + '#payment-history')

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
    # ... (โค้ดตรวจสอบ Session เดิม) ...
    sID = session.get('sID')
    if not sID:
        flash('กรุณาเข้าสู่ระบบ', 'error')
        return redirect(url_for('login_page'))

    sName     = request.form.get('sName')
    sUsername = request.form.get('sUsername')
    sPassword = request.form.get('sPassword') # รับค่า password (อาจเป็น String ว่าง)

    # 1. เรียกใช้ Service เพื่ออัปเดตข้อมูล
    success = StudentProfileServices.update_profile(
        sID=sID,
        sName=sName,
        sUsername=sUsername,
        sPassword=sPassword # ส่งรหัสผ่านไป (Service จะจัดการถ้าค่าเป็นว่าง)
    )

    if success:
        # อัปเดตชื่อใน Session ถ้ามีการเปลี่ยนชื่อ
        session['sName'] = sName 
        flash('ข้อมูลบัญชีถูกอัปเดตเรียบร้อยแล้ว', 'success')
    else:
        flash('เกิดข้อผิดพลาดในการอัปเดตข้อมูล (ชื่อผู้ใช้อาจซ้ำ)', 'error')

    return redirect(url_for('student_profile') + '#account-settings')

# =================================================================
# [ADDED] Register routes
# =================================================================

# [ADDED] choose role page (Student / Instructor)
@app.route('/register', methods=['GET'])
def register_select_role():
    # simple page with 2 buttons:
    #  - go to /register/student
    #  - go to /register/instructor
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

# [MODIFIED] /register/instructor route in app.py
@app.route('/register/instructor', methods=['GET', 'POST'])
def register_instructor():
    if request.method == 'GET':
        # We still need subject list for the dropdown
        subjects = RegistrationServices.get_subject_list()
        return render_template(
            'register_instructor.html',
            subjects=subjects,
            error_msg=None
        )

    # POST: read all form fields
    name = request.form.get('name')
    subject_id = request.form.get('subject_id')
    exp_year = request.form.get('exp_year')
    username = request.form.get('username')
    password = request.form.get('password')

    center_name = request.form.get('center_name')
    center_address = request.form.get('center_address')

    class_day = request.form.get('class_day')
    class_time = request.form.get('class_time')
    max_students = request.form.get('max_students')
    class_price = request.form.get('class_price')

    # Convert numeric fields
    try:
        subject_id = int(subject_id) if subject_id else None
    except ValueError:
        subject_id = None

    try:
        exp_year = int(exp_year) if exp_year else None
    except ValueError:
        exp_year = None

    try:
        max_students = int(max_students) if max_students else None
    except ValueError:
        max_students = None

    try:
        class_price = int(class_price) if class_price else None
    except ValueError:
        class_price = None

    # Call service to insert Instructor + Center + ClassSlot
    result = RegistrationServices.register_instructor(
        name=name,
        subject_id=subject_id,
        exp_year=exp_year,
        username=username,
        password=password,
        center_name=center_name,
        center_address=center_address,
        class_day=class_day,
        class_time=class_time,
        max_students=max_students,
        class_price=class_price,
    )

    if result.get("success"):
        # success: go back to login so the new instructor can log in
        return redirect(url_for('login_page'))

    # failed -> reload form with error and same subject dropdown
    subjects = RegistrationServices.get_subject_list()
    return render_template(
        'register_instructor.html',
        subjects=subjects,
        error_msg=result.get("message", "Registration failed.")
    )


    # POST: read form fields
    name = request.form.get('name')
    subject_id = request.form.get('subject_id')
    exp_year = request.form.get('exp_year')
    username = request.form.get('username')
    password = request.form.get('password')

    # basic int casting for numeric columns
    try:
        subject_id = int(subject_id) if subject_id else None
    except ValueError:
        subject_id = None

    try:
        exp_year = int(exp_year) if exp_year else None
    except ValueError:
        exp_year = None

    result = RegistrationServices.register_instructor(
        name=name,
        subject_id=subject_id,
        exp_year=exp_year,
        username=username,
        password=password,
    )

    if result.get("success"):
        # ✅ สมัครเสร็จ ส่งกลับหน้า login ให้ instructor ไปล็อกอินด้วย iUsername/iPassword
        return redirect(url_for('login_page'))  # <-- ใช้ login_page เดิมของคุณ

    # ❌ สมัครไม่ผ่าน → render form พร้อม error
    subjects = RegistrationServices.get_subject_list()
    return render_template(
        'register_instructor.html',
        subjects=subjects,
        error_msg=result.get("message", "Registration failed.")
    )

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
