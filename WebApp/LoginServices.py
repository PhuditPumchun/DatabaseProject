# LoginServices.py (แก้ไข: ลบเมธอด get_instructor_dashboard_data ออก)

# ... (import ต่างๆ เหมือนเดิม) ...
import os
from dotenv import load_dotenv
import psycopg2
from flask import jsonify

load_dotenv()

class LoginServices:
    
    # ... (เมธอด _get_db_connection เหมือนเดิม) ...
    @staticmethod
    def _get_db_connection():
        # ... (โค้ดเชื่อมต่อฐานข้อมูลเดิม) ...
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

    # ... (เมธอด _verify_user_and_get_id เหมือนเดิม) ...
    @staticmethod
    def _verify_user_and_get_id(username, password):
        # ... (โค้ดค้นหา iID เหมือนเดิม) ...
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

    # ----------------------------------------------------
    # เมธอดหลักในการตรวจสอบสิทธิ์ (authenticate ยังคงเดิม)
    # ----------------------------------------------------
    @staticmethod
    def authenticate(username, password, role):
        # ... (Logic การตรวจสอบสิทธิ์เหมือนเดิม) ...
        
        if not username or not password or not role:
            return {"success": False, "message": "Required fields missing."}, 400

        if role == 'student':
            return {"success": False, "message": "Student login not implemented yet."}, 401
            
        elif role == 'instructor':
            user_info = LoginServices._verify_user_and_get_id(username, password)
            
            if user_info:
                iID, iName = user_info
                # คืนค่า success=True และ iID เพื่อให้ app.py นำไปใช้ต่อ
                return {"success": True, "iID": iID, "iName": iName}, 200 
            else:
                return {"success": False, "message": "Invalid Instructor credentials."}, 401
        
        else:
            return {"success": False, "message": "Invalid role selected."}, 400