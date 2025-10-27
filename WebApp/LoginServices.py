import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

class LoginServices:
    @staticmethod
    def _get_db_connection():
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
            with conn, conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT iID, iName
                    FROM Instructor
                    WHERE iUsername = %s AND iPassword = %s;
                    """,
                    (username, password),
                )
                return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def _verify_student_and_get_id(username, password):
        """Check Student by susername/spassword → (sid, sname)"""
        conn = LoginServices._get_db_connection()
        if not conn:
            return None
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT sid, sname
                    FROM Student
                    WHERE susername = %s AND spassword = %s;
                    """,
                    (username, password),
                )
                return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def authenticate(username, password, role):
        if not username or not password or not role:
            return {"success": False, "message": "Required fields missing."}, 400

        if role == "student":
            row = LoginServices._verify_student_and_get_id(username, password)
            if row:
                sid, sname = row
                return {"success": True, "sID": sid, "sName": sname,
                        "redirect_url": "/student/dashboard"}, 200
            return {"success": False, "message": "Invalid Student credentials."}, 401

        if role == "instructor":
            row = LoginServices._verify_instructor_and_get_id(username, password)
            if row:
                iID, iName = row
                return {"success": True, "iID": iID, "iName": iName,
                        "redirect_url": "/instructor/dashboard"}, 200
            return {"success": False, "message": "Invalid Instructor credentials."}, 401

        return {"success": False, "message": "Invalid role selected."}, 400
