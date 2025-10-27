
import os
import psycopg2
from dotenv import load_dotenv
from datetime import date

load_dotenv()

class StudentEnrollmentServices:
    
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
            print(f"Database connection error in StudentEnrollmentServices: {e}")
            return None

    @staticmethod
    def enroll_student(sID: int, cID: int, feeAmount: float) -> bool:
        """
        บันทึกรายการลงทะเบียนใหม่ในตาราง Enrollment โดยมีสถานะเริ่มต้นเป็น 'Pending'
        
        Args:
            sID: Student ID
            cID: Class Slot ID
            feeAmount: ค่าธรรมเนียมของคลาส
            
        Returns:
            True หากการลงทะเบียนสำเร็จหรือมีรายการอยู่แล้ว, False หากเกิดข้อผิดพลาด
        """
        conn = StudentEnrollmentServices._get_db_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                # 1. ตรวจสอบว่าเคยลงทะเบียนคลาสนี้แล้วหรือไม่
                cur.execute(
                    "SELECT COUNT(*) FROM Enrollment WHERE sID = %s AND cID = %s;",
                    (sID, cID)
                )
                if cur.fetchone()[0] > 0:
                    print(f"Student {sID} already has an enrollment record for Class {cID}.")
                    # หากมีรายการอยู่แล้ว ถือว่าการดำเนินการสำเร็จ (ไม่ต้องทำซ้ำ)
                    return True
                    
                # 2. ทำการ INSERT รายการลงทะเบียนใหม่
                # Schema: sID, cID, enrollDate, paymentStatus, feeAmount
                cur.execute(
                    """
                    INSERT INTO Enrollment (sID, cID, enrollDate, paymentStatus, feeAmount)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (sID, cID, date.today(), 'Pending', feeAmount)
                )
            
            conn.commit()
            return True
            
        except psycopg2.Error as e:
            print(f"SQL execution error during enrollment: {e}")
            conn.rollback()
            return False
            
        finally:
            if conn:
                conn.close()
