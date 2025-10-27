# StudentDashboardServices.py

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class StudentDashboardServices:
    @staticmethod
    def _get_db_connection():
        """Create and return PostgreSQL connection."""
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
            print(f"Database connection error in StudentDashboardService: {e}")
            return None

    @staticmethod
    def get_dashboard_data(sID: int, filter_day: str | None = None):
        """
        Fetch data for the Student dashboard.

        Returns dict:
        {
            "student_profile": (sid, sname),
            "classes": [
                (
                    cID,          0
                    cDay,         1
                    cTime,        2
                    studentMax,   3
                    studentNow,   4
                    price,        5
                    tName,        6
                    address,      7
                    iName,        8
                    expYear,      9
                    subjectName, 10
                    imageProfile,11
                    enrolled      12 (1 if this student already enrolled)
                ),
                ...
            ]
        }

        filter_day:
            None or ""  -> no filtering (all days)
            "Monday"    -> filter WHERE cs.cDay = 'Monday'
            etc.
        """

        conn = StudentDashboardServices._get_db_connection()
        if not conn:
            return None

        try:
            cur = conn.cursor()

            # 1. Student profile (sid, sname)
            cur.execute(
                """
                SELECT sid, sname
                FROM Student
                WHERE sid = %s;
                """,
                (sID,)
            )
            student_profile = cur.fetchone()

            # 2. Class list
            # core SELECT block
            base_sql = """
                SELECT
                    cs.cID,
                    cs.cDay,
                    cs.cTime,
                    cs.studentMax,
                    COALESCE(COUNT(e_all.sID), 0)                      AS studentNow,
                    cs.price,
                    t.tName,
                    t.address,
                    i.iName,
                    i.expYear,
                    sbj.sName                                         AS subjectName,
                    m.imageProfile,
                    MAX(CASE WHEN e_me.sID IS NOT NULL THEN 1 ELSE 0 END) AS enrolled
                FROM ClassSlot cs
                JOIN TutoringCenter t       ON cs.tID = t.tID
                JOIN CenterManager cm       ON t.tID = cm.tID
                JOIN Instructor i           ON cm.iID = i.iID
                LEFT JOIN Subject sbj       ON i.sID = sbj.sID
                LEFT JOIN InstructorMedia m ON i.iID = m.iID
                LEFT JOIN Enrollment e_all  ON cs.cID = e_all.cID
                LEFT JOIN Enrollment e_me   ON cs.cID = e_me.cID AND e_me.sID = %s
            """

            params = [sID]

            # add WHERE if filtering by day
            if filter_day and filter_day.strip() != "":
                base_sql += "\nWHERE cs.cDay = %s\n"
                params.append(filter_day.strip())

            # group + order
            base_sql += """
                GROUP BY
                    cs.cID, cs.cDay, cs.cTime, cs.studentMax, cs.price,
                    t.tName, t.address,
                    i.iName, i.expYear,
                    sbj.sName,
                    m.imageProfile
                ORDER BY
                    cs.cDay,
                    cs.cTime,
                    cs.cID;
            """

            cur.execute(base_sql, tuple(params))
            class_rows = cur.fetchall()

            cur.close()

            return {
                "student_profile": student_profile,
                "classes": class_rows
            }

        except psycopg2.Error as e:
            print(f"SQL execution error in student dashboard: {e}")
            return None
        finally:
            conn.close()
