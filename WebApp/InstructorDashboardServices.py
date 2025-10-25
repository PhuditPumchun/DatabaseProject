# InstructorDashboardServices.py

import os
import psycopg2
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env (ต้องทำในทุกโมดูลที่ใช้ os.getenv)
load_dotenv()

class InstructorDashboardServices:

    # ----------------------------------------------------
    # เมธอดสำหรับสร้างการเชื่อมต่อฐานข้อมูล (นำมาจาก LoginServices)
    # ----------------------------------------------------
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
            print(f"Database connection error in Dashboard Service: {e}")
            return None

    # ----------------------------------------------------
    # เมธอดหลัก: ดึงข้อมูล Dashboard สำหรับ Instructor
    # ----------------------------------------------------
    @staticmethod
    def get_dashboard_data(iID):
        """ดึงข้อมูลที่เกี่ยวข้องทั้งหมดสำหรับ Instructor ID ที่กำหนด"""
        conn = InstructorDashboardServices._get_db_connection()
        if not conn:
            return None

        data = {}
        try:
            cursor = conn.cursor()
            
            # 1. ข้อมูลพื้นฐานของ Instructor
            cursor.execute("""
                SELECT 
                    i.iName, s.sName AS SubjectName, i.expYear, im.imageProfile, im.rewardURL
                FROM Instructor i
                LEFT JOIN Subject s ON i.sID = s.sID
                LEFT JOIN InstructorMedia im ON i.iID = im.iID
                WHERE i.iID = %s;
            """, (iID,))
            data['profile'] = cursor.fetchone()
            
            # 2. ข้อมูลศูนย์ที่ดูแล (ถ้าเป็น CenterManager)
            cursor.execute("""
                SELECT t.tName, t.address
                FROM TutoringCenter t
                JOIN CenterManager cm ON t.tID = cm.tID
                WHERE cm.iID = %s;
            """, (iID,))
            data['managed_center'] = cursor.fetchone()

            # 3. ข้อมูล Class Slot ที่มี
            # ดึง Class Slot ทั้งหมดใน Center ที่เขาดูแล
            cursor.execute("""
                SELECT 
                    cDay, cTime, studentNow, studentMax, t.tName 
                FROM ClassSlot cs
                JOIN TutoringCenter t ON cs.tID = t.tID
                WHERE cs.tID = (SELECT tID FROM CenterManager WHERE iID = %s);
            """, (iID,))
            data['classes'] = cursor.fetchall()
            
            cursor.close()
            return data
            
        except psycopg2.Error as e:
            print(f"SQL execution error in dashboard: {e}")
            return None
        
        finally:
            if conn:
                conn.close()