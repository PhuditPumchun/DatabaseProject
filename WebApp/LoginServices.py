
import os
from dotenv import load_dotenv
import psycopg2
from flask import jsonify

load_dotenv()

class LoginServices:
    
    @staticmethod
    def _get_db_connection():
        """สร้างและคืนค่า connection object ไปยังฐานข้อมูล PostgreSQL"""
        try:
            conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT')
            )
            return conn
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            return None

    @staticmethod
    def _verify_user_and_get_id(username, password):
        """
        ใช้สำหรับ Instructor เท่านั้น
        ตรวจสอบ username/password -> คืน (iID, iName)
        """
        conn = LoginServices._get_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            sql_query = """
                SELECT iID, iName
                FROM Instructor 
                WHERE iUsername = %s AND iPassword = %s;
            """
            cursor.execute(sql_query, (username, password))
            result = cursor.fetchone()
            cursor.close()
            return result
        
        except psycopg2.Error as e:
            print(f"SQL execution error during login: {e}")
            return None
        
        finally:
            if conn:
                conn.close()

    # [MODIFIED] ฟังก์ชันสำหรับ student: ใช้ sUsername และ sPassword
    @staticmethod
    def _verify_student_and_get_id(username, password):
        """
        ตรวจสอบ Student โดยใช้ sUsername และ sPassword (เหมือน Instructor)
        คืนค่า (sID, sName)
        """
        conn = LoginServices._get_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            sql_query = """
                SELECT sID, sName
                FROM Student
                WHERE sUsername = %s AND sPassword = %s;
            """
            cursor.execute(sql_query, (username, password))
            result = cursor.fetchone()
            cursor.close()
            return result

        except psycopg2.Error as e:
            print(f"SQL execution error during student login: {e}")
            return None

        finally:
            if conn:
                conn.close()

    # [MODIFIED] authenticate ตอนนี้รองรับ student ด้วย Logic ที่แก้ไข
    @staticmethod
    def authenticate(username, password, role):
        """
        ใช้โดย /api/login และ /login (POST)
        จะคืน dict + status_code
        """
        if not username or not password or not role:
            return {"success": False, "message": "Required fields missing."}, 400

        if role == 'student':
            student_info = LoginServices._verify_student_and_get_id(username, password)
            if student_info:
                sID, sName = student_info
                # NOTE: ใน app.py เก่า Redirect Student ไป YouTube 
                # ถ้าต้องการ Dashboard Student ต้องเพิ่ม Route ใน app.py ด้วย
                return {
                    "success": True,
                    "sID": sID,
                    "sName": sName,
                    "redirect_url": "https://www.youtube.com/watch?v=u_c1tRmj7E4"
                }, 200
            else:
                return {"success": False, "message": "Invalid Student credentials."}, 401
            
        elif role == 'instructor':
            user_info = LoginServices._verify_user_and_get_id(username, password)
            if user_info:
                iID, iName = user_info
                return {"success": True, "iID": iID, "iName": iName}, 200 
            else:
                return {"success": False, "message": "Invalid Instructor credentials."}, 401
        
        else:
            return {"success": False, "message": "Invalid role selected."}, 400
