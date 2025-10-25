# app.py

# ... (import ต่างๆ เหมือนเดิม) ...
from flask import Flask, render_template, request, jsonify, redirect, url_for, session # เพิ่ม session
from LoginServices import LoginServices
from InstructorDashboardServices import InstructorDashboardServices

app = Flask(__name__)
# ตั้งค่า SECRET_KEY สำหรับการใช้งาน Session (จำเป็นมากในการทำงานจริง)
app.config['SECRET_KEY'] = 'your_super_secret_key_here' 

# ... (Route สำหรับ login_page และ api_login เหมือนเดิม) ...
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

# ----------------------------------------------------
# 3. Form Handler Route (POST) - สำหรับหน้าเว็บ HTML
# ----------------------------------------------------
@app.route('/login', methods=['POST'])
def handle_login_form():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    response, status_code = LoginServices.authenticate(username, password, role)

    if response.get('success'):
        if role == 'instructor':
            # เก็บ iID ไว้ใน Session เพื่อใช้ดึงข้อมูลใน Dashboard
            session['iID'] = response.get('iID')
            session['iName'] = response.get('iName')
            
            # Redirect ไปยัง Dashboard
            return redirect(url_for('instructor_dashboard'))
        else:
            # สำหรับ Student (ถ้า implement แล้ว)
            redirect_url = response.get('redirect_url')
            return redirect(redirect_url)
    else:
        # ล็อกอินล้มเหลว: redirect กลับไปหน้า login
        # ในโลกจริง ควรใช้ flash() เพื่อแสดงข้อผิดพลาด
        return redirect(url_for('login_page'))


# ----------------------------------------------------
# 4. Route ใหม่: Instructor Dashboard
# ----------------------------------------------------
@app.route('/instructor/dashboard', methods=['GET'])
def instructor_dashboard():
    iID = session.get('iID')
    iName = session.get('iName', 'Instructor')

    if not iID:
        return redirect(url_for('login_page'))

    # ดึงข้อมูลทั้งหมดจาก Service ใหม่
    dashboard_data = InstructorDashboardServices.get_dashboard_data(iID) # <--- CALL SERVICE ใหม่

    if dashboard_data:
        return render_template('instructor_dashboard.html', 
                                instructor_name=iName,
                                data=dashboard_data)
    else:
        return "Error loading dashboard data.", 500
    
@app.route('/logout')
def logout():
    """ล้างข้อมูล session และ Redirect ไปยังหน้า Login"""
    
    # ลบตัวแปร iID และ iName ออกจาก session
    session.pop('iID', None) 
    session.pop('iName', None) 
    
    # Redirect ผู้ใช้กลับไปที่หน้า Login
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)