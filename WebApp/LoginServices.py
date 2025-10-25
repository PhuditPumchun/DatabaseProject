# LoginServices.py (อัปเดต)

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

    # [ADDED] ฟังก์ชันใหม่สำหรับ student
    @staticmethod
    def _verify_student_and_get_id(username):
        """
        ตรวจสอบ Student ด้วย sID (prototype)
        NOTE:
        - ตาราง Student ในโปรเจกต์นี้ (จากไฟล์ InsertStudent.sql) มี sID, sName
          ยังไม่มี username / password แยก
        - เพื่อให้ demo ใช้งานได้: เราจะถือว่า 'username' = รหัสนักเรียน sID
          ส่วน password เราไม่เช็คจริงจัง (แต่ฟอร์มยังต้องกรอกอยู่)
        """
        conn = LoginServices._get_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            sql_query = """
                SELECT sID, sName
                FROM Student
                WHERE sID = %s;
            """
            cursor.execute(sql_query, (username,))
            result = cursor.fetchone()
            cursor.close()
            return result

        except psycopg2.Error as e:
            print(f"SQL execution error during student login: {e}")
            return None

        finally:
            if conn:
                conn.close()

    # [MODIFIED] authenticate ตอนนี้รองรับ student ด้วย
    @staticmethod
    def authenticate(username, password, role):
        """
        ใช้โดย /api/login และ /login (POST)
        จะคืน dict + status_code
        """
        if not username or not password or not role:
            return {"success": False, "message": "Required fields missing."}, 400

        if role == 'student':
            student_info = LoginServices._verify_student_and_get_id(username)
            if student_info:
                sID, sName = student_info
                return {
                    "success": True,
                    "sID": sID,
                    "sName": sName,
                    "redirect_url": "/student/dashboard"  # เผื่อโค้ดเก่าเรียกใช้
                }, 200
            else:
                return {"success": False, "message": "Invalid Student credentials."}, 401
            
        elif role == 'instructor':
            user_info = LoginServices._verify_user_and_get_id(username, password)
            if user_info:
                iID, iName = user_info
                # คืนค่า success=True และข้อมูล instructor ให้ app.py เก็บใน session
                return {"success": True, "iID": iID, "iName": iName}, 200 
            else:
                return {"success": False, "message": "Invalid Instructor credentials."}, 401
        
        else:
            return {"success": False, "message": "Invalid role selected."}, 400
