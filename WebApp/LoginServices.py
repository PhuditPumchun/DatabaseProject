# LoginServices.py (แก้ไข)

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

class LoginServices:
    
    @staticmethod
    def _get_db_connection():
        """สร้างและคืนค่า connection object ไปยังฐานข้อมูล PostgreSQL"""
        try:
            return psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
            )
        except psycopg2.Error as e:
            print(f"DB connection error: {e}")
            return None

    @staticmethod
    def _verify_instructor_and_get_id(username, password):
        """Check Instructor by iUsername/iPassword → (iID, iName)"""
        conn = LoginServices._get_db_connection()
        if not conn:
            return None
        
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT iID, iName
                        FROM Instructor
                        WHERE iUsername = %s AND iPassword = %s;
                        """,
                        (username, password),
                    )
                    return cur.fetchone()
        except psycopg2.Error as e:
            print(f"SQL execution error during instructor login: {e}")
            return None

    @staticmethod
    def _verify_student_and_get_id(username, password):
        """Check Student by sUsername/sPassword → (sID, sName)"""
        conn = LoginServices._get_db_connection()
        if not conn:
            return None
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        -- *** แก้ไขให้ใช้ SUsername และ SPassword ตาม Schema ***
                        SELECT sID, sName
                        FROM Student
                        WHERE sUsername = %s AND sPassword = %s;
                        """,
                        (username, password),
                    )
                    return cur.fetchone()
        except psycopg2.Error as e:
            print(f"SQL execution error during student login: {e}")
            return None
            
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
                return {
                    "success": True,
                    "sID": sID,
                    "sName": sName,
                    "redirect_url": "https://www.youtube.com/watch?v=u_c1tRmj7E4"
                }, 200
            else:
                return {"success": False, "message": "Invalid Student credentials."}, 401
            
        elif role == 'instructor':
            user_info = LoginServices._verify_instructor_and_get_id(username, password)
            if user_info:
                iID, iName = user_info
                return {"success": True, "iID": iID, "iName": iName}, 200 
            else:
                return {"success": False, "message": "Invalid Instructor credentials."}, 401
        
        else:
            return {"success": False, "message": "Invalid role selected."}, 400