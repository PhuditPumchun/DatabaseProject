# StudentDashboardServices.py

import os
import psycopg2
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
load_dotenv()

class StudentDashboardServices:
    @staticmethod
    def _get_db_connection():
        """สร้างและคืนค่า connection object ไปยังฐานข้อมูล PostgreSQL"""
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
    def get_dashboard_data(sID: int):
        """
        ดึงข้อมูลสำหรับหน้า Student Dashboard
        - โปรไฟล์นักเรียน (student_profile)
        - รายการคลาสทั้งหมด (classes) พร้อมข้อมูลครู/ศูนย์/ตารางเรียน/ราคา/ที่นั่งว่าง

        classes แต่ละรายการจะมี tuple ประมาณนี้:
        (
            cID,            # 0
            cDay,           # 1
            cTime,          # 2
            studentMax,     # 3
            studentNow,     # 4  (จำนวนที่ลงแล้ว)
            price,          # 5
            tName,          # 6
            address,        # 7
            iName,          # 8
            expYear,        # 9
            subjectName,    # 10
            imageProfile,   # 11 (จาก InstructorMedia)
            enrolled_flag   # 12 (1 = นักเรียนคนนี้ลงอยู่แล้ว)
        )
        """

        conn = StudentDashboardServices._get_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()

            # 1) โปรไฟล์นักเรียน
            cursor.execute(
                """
                SELECT sID, sName
                FROM Student
                WHERE sID = %s;
                """,
                (sID,)
            )
            student_profile = cursor.fetchone()

            # 2) รายวิชาที่เปิดสอนทั้งหมด + ครู + ศูนย์ + สถานะลงทะเบียน
            #    อธิบาย JOIN:
            #    - ClassSlot cs    : ตารางรอบสอน (วัน/เวลา/ราคา/ที่สอนอยู่ที่ศูนย์ไหน)
            #    - TutoringCenter t: ศูนย์กวดวิชา (ชื่อ/ที่อยู่)
            #    - CenterManager cm: map ว่า center นี้มี instructor คนไหนดูแล
            #    - Instructor i    : ครูผู้สอน (ชื่อ, ปีประสบการณ์, วิชาไหน)
            #    - Subject sbj     : ชื่อวิชา เช่น Math / Physics ...
            #    - InstructorMedia m: รูปโปรไฟล์ครู
            #    - Enrollment e_all: ใช้นับว่านักเรียนลงไปแล้วกี่คน
            #    - Enrollment e_me : เช็กว่านักเรียนคนนี้ลงคลาสนี้แล้วหรือยัง
            cursor.execute(
                """
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
                """,
                (sID,)
            )
            class_rows = cursor.fetchall()

            cursor.close()

            return {
                "student_profile": student_profile,  # (sID, sName)
                "classes": class_rows                # list[tuple]
            }

        except psycopg2.Error as e:
            print(f"SQL execution error in student dashboard: {e}")
            return None
        finally:
            if conn:
                conn.close()
