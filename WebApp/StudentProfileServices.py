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

    # ===================== READ =====================

    @staticmethod
    def get_full_profile(sID: int):
        """
        ดึงข้อมูลส่วนตัว (sID, sName, sUsername) และคลาสที่ลงทะเบียนสำเร็จ (Status = 'Paid')
        """
        conn = StudentProfileServices._get_db_connection()
        if not conn:
            return None

        try:
            cur = conn.cursor()

            # 1) ดึง Student Profile
            cur.execute(
                "SELECT sID, sName, sUsername FROM Student WHERE sID = %s;",
                (sID,)
            )
            row = cur.fetchone()
            if not row:
                return {"profile": None, "enrolled_classes": []}

            profile = {
                "sID": row[0],
                "sName": row[1],
                "sUsername": row[2],
            }

            # 2) ดึงคลาสที่ลงทะเบียนสำเร็จ (Paid)
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
        if not conn:
            return []

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

    # ===================== UPDATE =====================

    @staticmethod
    def update_profile(sID: int, sName: str | None = None,
                       sUsername: str | None = None,
                       sPassword: str | None = None) -> bool:
        """
        อัปเดตข้อมูลนักเรียนในตาราง Student เฉพาะฟิลด์ที่ส่งมา
        คอลัมน์เป้าหมาย: sName, sUsername, sPassword
        """
        conn = StudentProfileServices._get_db_connection()
        if not conn:
            return False

        try:
            cur = conn.cursor()

            set_cols, params = [], []

            if sName is not None:
                set_cols.append("sName = %s")
                params.append(sName)

            if sUsername is not None:
                set_cols.append("sUsername = %s")
                params.append(sUsername)

            if sPassword is not None:
                set_cols.append("sPassword = %s")
                params.append(sPassword)

            if not set_cols:
                # ไม่มีอะไรให้อัปเดต
                cur.close()
                return True

            sql = "UPDATE Student SET " + ", ".join(set_cols) + " WHERE sID = %s;"
            params.append(sID)
            cur.execute(sql, tuple(params))

            conn.commit()
            cur.close()
            return True

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            print(f"SQL execution error updating student: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_account(sID: int, new_sID: int | None = None,
                       sName: str | None = None,
                       sUsername: str | None = None) -> bool:
        """
        อัปเดตข้อมูลบัญชี: sName, sUsername และ 'อาจ' เปลี่ยน sID
        * การเปลี่ยน sID ต้องอาศัย FK แบบ ON UPDATE CASCADE มิฉะนั้นจะล้มเหลว
        """
        conn = StudentProfileServices._get_db_connection()
        if not conn:
            return False
        try:
            cur = conn.cursor()

            # 1) อัปเดตชื่อ/ยูสเซอร์เนม (ถ้ามี)
            cols, params = [], []
            if sName is not None:
                cols.append("sName = %s"); params.append(sName)
            if sUsername is not None:
                cols.append("sUsername = %s"); params.append(sUsername)
            if cols:
                cur.execute("UPDATE Student SET " + ", ".join(cols) + " WHERE sID = %s;",
                            params + [sID])

            # 2) เปลี่ยน sID (ถ้าส่งมาและต่างจากเดิม)
            if new_sID is not None and new_sID != sID:
                # แยกเป็นคำสั่งต่างหากเพื่อให้ DB จัดการ FK/constraint
                cur.execute("UPDATE Student SET sID = %s WHERE sID = %s;", (new_sID, sID))

            conn.commit()
            cur.close()
            return True
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            print(f"SQL execution error updating student account: {e}")
            return False
        finally:
            if conn:
                conn.close()

