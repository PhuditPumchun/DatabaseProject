
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class StudentPaymentServices:
    
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
            print(f"Database connection error in StudentPaymentServices: {e}")
            return None

    @staticmethod
    def confirm_payment(sID: int, cID: int) -> bool:
        """
        อัปเดตสถานะการชำระเงินเป็น 'Paid' และเพิ่มจำนวนนักเรียนใน ClassSlot
        """
        conn = StudentPaymentServices._get_db_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                # 1. ตรวจสอบสถานะปัจจุบันและป้องกันการอัปเดตซ้ำ
                cur.execute(
                    "SELECT paymentStatus FROM Enrollment WHERE sID = %s AND cID = %s;",
                    (sID, cID)
                )
                result = cur.fetchone()
                if not result or result[0] == 'Paid':
                    print(f"Enrollment record not found or already paid for sID={sID}, cID={cID}")
                    return True # ถือว่าสำเร็จถ้าจ่ายแล้ว

                # 2. อัปเดตสถานะการชำระเงินในตาราง Enrollment
                cur.execute(
                    """
                    UPDATE Enrollment
                    SET paymentStatus = 'Paid'
                    WHERE sID = %s AND cID = %s;
                    """,
                    (sID, cID)
                )

                # 3. อัปเดตจำนวนนักเรียนในตาราง ClassSlot (เพิ่ม studentNow + 1)
                cur.execute(
                    """
                    UPDATE ClassSlot
                    SET studentNow = studentNow + 1
                    WHERE cID = %s;
                    """,
                    (cID,)
                )
            
            conn.commit()
            return True
            
        except psycopg2.Error as e:
            print(f"SQL execution error during payment confirmation: {e}")
            conn.rollback()
            return False
            
        finally:
            if conn:
                conn.close()
