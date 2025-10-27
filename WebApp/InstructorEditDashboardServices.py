# InstructorEditDashboardServices.py

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class InstructorEditDashboardServices:
    
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
            print(f"Database connection error in Edit Service: {e}")
            return None

    @staticmethod
    def update_data(iID, tID, mediaID, iName, iUsername, iPassword, tName, address, profile_url, reward_url, video_url):
        """อัปเดตข้อมูล Instructor, Center Manager, URL สื่อ, และ Security"""
        conn = InstructorEditDashboardServices._get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            
            # 1. UPDATE ชื่อและ Username ของ Instructor
            update_instructor_sql = """
                UPDATE Instructor 
                SET iName = %s, iUsername = %s 
                WHERE iID = %s;
            """
            params = [iName, iUsername, iID]

            # 1.1. หากมีการกรอก New Password, ให้ทำการ Update iPassword ด้วย
            if iPassword:
                # WARNING: ในโปรเจกต์จริง ต้องใช้ Password Hashing เช่น bcrypt ก่อนบันทึก
                update_instructor_sql = update_instructor_sql.replace(
                    "WHERE iID = %s", ", iPassword = %s WHERE iID = %s"
                )
                params.insert(2, iPassword)
            
            cursor.execute(update_instructor_sql, tuple(params))

            # 2. UPDATE ชื่อ Tutoring Center และ Address
            cursor.execute("""
                UPDATE TutoringCenter t 
                SET tName = %s, address = %s 
                WHERE tID = %s 
                AND EXISTS (SELECT 1 FROM CenterManager WHERE tID = t.tID AND iID = %s);
            """, (tName, address, tID, iID))
            
            # 3. UPDATE InstructorMedia URL 
            if mediaID is not None:
                 cursor.execute("""
                    UPDATE InstructorMedia 
                    SET imageProfile = %s, rewardURL = %s, videoURL = %s
                    WHERE mediaID = %s AND iID = %s;
                 """, (profile_url, reward_url, video_url, mediaID, iID))
            
            conn.commit()
            cursor.close()
            return True
            
        except psycopg2.Error as e:
            conn.rollback()
            print(f"SQL execution error during update: {e}")
            return False
        
        finally:
            if conn:
                conn.close()