# StudentProfileServices.py

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class StudentProfileServices:
    
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
            print(f"Database connection error in StudentProfileServices: {e}")
            return None

    @staticmethod
    def get_full_profile(sID: int):
        """
        ดึงข้อมูลส่วนตัว (sID, sName, sUsername) และคลาสที่ลงทะเบียนสำเร็จ (Status = 'Paid')
        """
        conn = StudentProfileServices._get_db_connection()
        if not conn: return None
        
        try:
            cur = conn.cursor()

            # 1. ดึง Student Profile (sID, sName, sUsername)
            cur.execute(
                "SELECT sID, sName, sUsername FROM Student WHERE sID = %s;", (sID,)
            )
            profile = cur.fetchone()
            
            # 2. ดึงคลาสที่ลงทะเบียนสำเร็จ (Status = 'Paid')
            # Columns: enrollDate, cDay, cTime, CenterName, InstructorName, SubjectName, Price
            cur.execute("""
                SELECT
                    e.enrollDate, cs.cDay, cs.cTime, t.tName, i.iName, sbj.sName, cs.price
                FROM Enrollment e
                JOIN ClassSlot cs ON e.cID = cs.cID
                JOIN TutoringCenter t ON cs.tID = t.tID
                JOIN CenterManager cm ON t.tID = cm.tID
                JOIN Instructor i ON cm.iID = i.iID
                LEFT JOIN Subject sbj ON i.sID = sbj.sID
                WHERE e.sID = %s AND e.paymentStatus = 'Paid'
                ORDER BY e.enrollDate DESC;
            """, (sID,))
            enrolled_classes = cur.fetchall()

            return {
                "profile": profile,
                "enrolled_classes": enrolled_classes,
            }

        except psycopg2.Error as e:
            print(f"SQL execution error fetching full profile: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_payment_history(sID: int):
        """
        ดึงประวัติการชำระเงินทั้งหมด
        Columns: cID, InstructorName, CenterName, feeAmount, paymentStatus, enrollDate
        """
        conn = StudentProfileServices._get_db_connection()
        if not conn: return []

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    e.cID, i.iName, t.tName, e.feeAmount, e.paymentStatus, e.enrollDate
                FROM Enrollment e
                JOIN ClassSlot cs ON e.cID = cs.cID
                JOIN TutoringCenter t ON cs.tID = t.tID
                JOIN CenterManager cm ON t.tID = cm.tID
                JOIN Instructor i ON cm.iID = i.iID
                WHERE e.sID = %s
                ORDER BY e.enrollDate DESC;
            """, (sID,))
            return cur.fetchall()

        except psycopg2.Error as e:
            print(f"SQL execution error fetching payment history: {e}")
            return []
        finally:
            if conn:
                conn.close()