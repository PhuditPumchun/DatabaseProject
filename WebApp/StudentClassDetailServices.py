import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class StudentClassDetailServices:
    
    @staticmethod
    def _get_db_connection():
        """Create and return PostgreSQL connection."""
        try:
            return psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT')
            )
        except psycopg2.Error as e:
            print(f"Database connection error in StudentClassDetailServices: {e}")
            return None

    @staticmethod
    def get_class_detail(cID: int, sID: int):
        """
        Fetch detailed information for a specific Class ID, 
        including enrollment status for the student (sID).
        """
        conn = StudentClassDetailServices._get_db_connection()
        if not conn:
            return None

        try:
            with conn, conn.cursor() as cur:
                # Query นี้คล้ายกับที่ใช้ใน dashboard แต่กรองด้วย cID
                cur.execute(
                    """
                    SELECT
                        cs.cID,
                        cs.cDay,
                        cs.cTime,
                        cs.studentMax,
                        COALESCE(COUNT(e_all.sID), 0) AS studentNow,
                        cs.price,
                        t.tName,
                        t.address,
                        i.iName,
                        i.expYear,
                        sbj.sName AS subjectName,
                        m.imageProfile,
                        m.videoURL, -- เพิ่ม videoURL
                        MAX(CASE WHEN e_me.sID IS NOT NULL THEN 1 ELSE 0 END) AS enrolled
                    FROM ClassSlot cs
                    JOIN TutoringCenter t ON cs.tID = t.tID
                    JOIN CenterManager cm ON t.tID = cm.tID
                    JOIN Instructor i ON cm.iID = i.iID
                    LEFT JOIN Subject sbj ON i.sID = sbj.sID
                    LEFT JOIN InstructorMedia m ON i.iID = m.iID
                    LEFT JOIN Enrollment e_all ON cs.cID = e_all.cID
                    LEFT JOIN Enrollment e_me ON cs.cID = e_me.cID AND e_me.sID = %s
                    WHERE cs.cID = %s
                    GROUP BY
                        cs.cID, cs.cDay, cs.cTime, cs.studentMax, cs.price,
                        t.tName, t.address, i.iName, i.expYear, sbj.sName,
                        m.imageProfile, m.videoURL;
                    """,
                    (sID, cID)
                )
                return cur.fetchone()

        except psycopg2.Error as e:
            print(f"SQL execution error fetching class detail: {e}")
            return None