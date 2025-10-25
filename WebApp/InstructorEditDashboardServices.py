# InstructorEditDashboardServices.py

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class InstructorEditDashboardServices:
    
    @staticmethod
    def _get_db_connection():
        """สร้างและคืนค่า Connection Object ไปยังฐานข้อมูล PostgreSQL"""
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
            print(f"Database connection error in Edit Service: {e}")
            return None

    @staticmethod
    def update_data(iID, tID, iName, tName, address):
        """อัปเดตชื่อ Instructor และรายละเอียด Center Manager"""
        conn = InstructorEditDashboardServices._get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            
            # 1. UPDATE ชื่อ Instructor
            cursor.execute("""
                UPDATE Instructor SET iName = %s WHERE iID = %s;
            """, (iName, iID))

            # 2. UPDATE ชื่อ Tutoring Center และ Address (ต้องเป็น Center ที่เขารับผิดชอบ)
            cursor.execute("""
                UPDATE TutoringCenter t 
                SET tName = %s, address = %s 
                WHERE tID = %s 
                AND EXISTS (SELECT 1 FROM CenterManager WHERE tID = t.tID AND iID = %s);
            """, (tName, address, tID, iID))
            
            conn.commit()
            cursor.close()
            return True
            
        except psycopg2.Error as e:
            conn.rollback()
            print(f"SQL execution error during update: {e}")
            return False
        
        finally:
            if conn:
                conn.close()