# RegistrationServices.py
# Handles sign-up logic (Student)

import os
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv

load_dotenv()

class RegistrationServices:
    @staticmethod
    def _get_db_connection():
        """Return PostgreSQL connection using .env"""
        try:
            return psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
            )
        except psycopg2.Error as e:
            print(f"[Registration] DB connection error: {e}")
            return None

    @staticmethod
    def register_student(name: str, username: str, password: str):
        """
        Insert a new student row:
        INSERT INTO Student(sid,sname,susername,spassword)
        VALUES (<next id>, name, username, password)

        Returns:
          {success: True, sid: ..., sname: ...} or {success: False, message: ...}
        """
        conn = RegistrationServices._get_db_connection()
        if not conn:
            return {"success": False, "message": "Cannot connect to database."}

        try:
            with conn:
                with conn.cursor() as cur:
                    # compute next sid (1-based). Safe enough for this project scope.
                    cur.execute("SELECT COALESCE(MAX(sid)+1, 1) FROM Student;")
                    next_sid = cur.fetchone()[0]

                    cur.execute(
                        """
                        INSERT INTO Student (sid, sname, susername, spassword)
                        VALUES (%s, %s, %s, %s)
                        RETURNING sid, sname;
                        """,
                        (next_sid, name, username, password),
                    )
                    sid, sname = cur.fetchone()

            return {"success": True, "sid": sid, "sname": sname}

        except errors.UniqueViolation:
            # unique index on susername
            conn.rollback()
            return {"success": False, "message": "Username already exists."}

        except psycopg2.IntegrityError as e:
            conn.rollback()
            return {"success": False, "message": f"Integrity error: {e.pgerror}"}

        except psycopg2.Error as e:
            conn.rollback()
            return {"success": False, "message": f"DB error: {e.pgerror}"}

        finally:
            try:
                conn.close()
            except Exception:
                pass
