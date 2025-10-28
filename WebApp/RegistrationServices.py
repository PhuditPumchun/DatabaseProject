# RegistrationServices.py
# [MODIFIED] upgraded to also create TutoringCenter + ClassSlot
#
# Flow when an instructor registers:
#   1) create new TutoringCenter (tID, lID, tName, address)
#   2) create new Instructor (iID, iName, sID, expYear, iUsername, iPassword, tID)
#   3) create new ClassSlot (cID, cDay, cTime, studentNow=0, studentMax, tID, price)
#
# All in ONE transaction. If anything fails, nothing is inserted.

import os
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv

load_dotenv()

class RegistrationServices:
    @staticmethod
    def _conn():
        """Open DB connection using .env values."""
        try:
            return psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
            )
        except psycopg2.Error as e:
            print(f"[Registration] DB connect error: {e}")
            return None

    # -----------------------------------------------------------------
    # (ยังเก็บไว้ให้) Student register
    # ถ้าโปรเจกต์คุณมี register_student route อยู่แล้ว ก็ใช้ต่อได้
    # -----------------------------------------------------------------
    @staticmethod
    def register_student(name: str, username: str, password: str):
        conn = RegistrationServices._conn()
        if not conn:
            return {"success": False, "message": "Cannot connect database."}

        try:
            with conn:
                with conn.cursor() as cur:
                    # next sid
                    cur.execute("SELECT COALESCE(MAX(sid)+1, 1) FROM Student;")
                    next_sid = cur.fetchone()[0]

                    cur.execute("""
                        INSERT INTO Student (sid, sname, susername, spassword)
                        VALUES (%s, %s, %s, %s)
                        RETURNING sid, sname;
                    """, (next_sid, name, username, password))

                    sid, sname = cur.fetchone()

            return {"success": True, "sid": sid, "sname": sname}

        except errors.UniqueViolation:
            conn.rollback()
            return {"success": False, "message": "Username already exists."}
        except psycopg2.Error as e:
            conn.rollback()
            return {"success": False, "message": f"DB error: {e.pgerror}"}
        finally:
            conn.close()

    # -----------------------------------------------------------------
    # Subject list (for dropdown in instructor form)
    # -----------------------------------------------------------------
    @staticmethod
    def get_subject_list():
        conn = RegistrationServices._conn()
        if not conn:
            return []

        try:
            with conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT sID, sName
                    FROM Subject
                    ORDER BY sName;
                """)
                rows = cur.fetchall()   # [(1,"Math"), (2,"Physics"), ...]
                return rows
        except psycopg2.Error as e:
            print(f"[Registration] get_subject_list error: {e}")
            return []
        finally:
            conn.close()

    # -----------------------------------------------------------------
    # MAIN: Register new instructor WITH center AND first class slot
    #
    # Incoming data from the form:
    #   name           -> Instructor.iName
    #   subject_id     -> Instructor.sID
    #   exp_year       -> Instructor.expYear
    #   username       -> Instructor.iUsername
    #   password       -> Instructor.iPassword
    #
    #   center_name    -> TutoringCenter.tName
    #   center_address -> TutoringCenter.address
    #
    #   class_day      -> ClassSlot.cDay
    #   class_time     -> ClassSlot.cTime
    #   max_students   -> ClassSlot.studentMax
    #   class_price    -> ClassSlot.price
    #
    # Notes / assumptions:
    #   - Instructor table right now is assumed to ALSO have tID (FK to TutoringCenter).
    #     We will set that tID when we insert the instructor.
    #
    #   - TutoringCenter table is assumed to have columns like:
    #       tID (PK),
    #       lID (branch/location id),
    #       tName,
    #       address
    #     From your DB screenshot it looks like each center row has both tID and lID
    #     and so far they match (1/1, 2/2). We'll just set lID = tID for new rows.
    #
    #   - ClassSlot table is assumed to have columns:
    #       cID, cDay, cTime, studentNow, studentMax, tID, price
    #
    #   - studentNow starts at 0 for a fresh class.
    #
    # Return:
    #   {success: True, iID: ..., iName: ...}
    #   or {success: False, message: "..."}
    # -----------------------------------------------------------------
    # RegistrationServices.py  (เฉพาะฟังก์ชันนี้)
    @staticmethod
    def register_instructor(
        name: str,
        subject_id: int,
        exp_year: int,
        username: str,
        password: str,
        center_name: str,
        center_address: str,
        class_day: str,
        class_time: str,
        max_students: int,
        class_price: int,
    ):
        conn = RegistrationServices._conn()
        if not conn:
            return {"success": False, "message": "Cannot connect database."}

        try:
            with conn:
                with conn.cursor() as cur:
                    # next ids
                    cur.execute("SELECT COALESCE(MAX(tID)+1, 1) FROM TutoringCenter;")
                    next_tid = cur.fetchone()[0]

                    cur.execute("SELECT COALESCE(MAX(iID)+1, 1) FROM Instructor;")
                    next_iid = cur.fetchone()[0]

                    cur.execute("SELECT COALESCE(MAX(cID)+1, 1) FROM ClassSlot;")
                    next_cid = cur.fetchone()[0]

                    # 1) TutoringCenter
                    cur.execute("""
                        INSERT INTO TutoringCenter (tID, tName, address)
                        VALUES (%s, %s, %s);
                    """, (next_tid, center_name, center_address))

                    # 2) Instructor  (ไม่มีคอลัมน์ tID ใน table นี้)
                    cur.execute("""
                        INSERT INTO Instructor
                        (iID, iName, sID, expYear, iUsername, iPassword)
                        VALUES (%s, %s, %s, %s, %s, %s);
                    """, (next_iid, name, subject_id, exp_year, username, password))

                    # ✅ 2.5) LINK Instructor กับ Center ผ่าน CenterManager (สำคัญ!)
                    cur.execute("""
                        INSERT INTO CenterManager (tID, iID)
                        VALUES (%s, %s);
                    """, (next_tid, next_iid))

                    # 3) ClassSlot ของศูนย์นี้
                    cur.execute("""
                        INSERT INTO ClassSlot
                        (cID, cDay, cTime, studentNow, studentMax, tID, price)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (next_cid, class_day, class_time, 0, max_students, next_tid, class_price))

            return {"success": True, "iID": next_iid, "iName": name}

        except errors.UniqueViolation:
            conn.rollback()
            return {"success": False, "message": "Username already exists."}
        except psycopg2.Error as e:
            conn.rollback()
            print(f"[Registration] register_instructor error: {e}")
            return {"success": False, "message": f"DB error: {e.pgerror}"}
        finally:
            conn.close()
