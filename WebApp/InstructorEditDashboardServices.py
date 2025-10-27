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
                port=os.getenv('DB_PORT'),
            )
            return conn
        except psycopg2.Error as e:
            print(f"Database connection error in Edit Service: {e}")
            return None

    @staticmethod
    def update_data(
        iID,
        tID=None,
        iName=None,
        tName=None,
        address=None,
        mediaID=None,
        iUsername=None,
        iPassword=None,
        profile_url=None,
        reward_url=None,
        video_url=None,
        subjectID=None, # NEW: เพิ่ม subjectID
    ):
        """อัปเดตข้อมูล Instructor / TutoringCenter / InstructorMedia เฉพาะฟิลด์ที่ส่งมา"""
        conn = InstructorEditDashboardServices._get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # --- 1) UPDATE Instructor (Name, Username, Password, Subject) ---
            set_cols, params = [], []
            if iName is not None:
                set_cols.append("iName = %s")
                params.append(iName)
            if iUsername is not None:
                set_cols.append("iUsername = %s")
                params.append(iUsername)
            if iPassword and iPassword.strip() != "":
                set_cols.append("iPassword = %s")
                params.append(iPassword)
            if subjectID is not None:
                 set_cols.append("sID = %s")
                 params.append(subjectID)


            if set_cols:
                sql = "UPDATE Instructor SET " + ", ".join(set_cols) + " WHERE iID = %s;"
                params.append(iID)
                cursor.execute(sql, tuple(params))

            # --- 2) UPDATE TutoringCenter (Name, Address) ---
            tc_cols, tc_params = [], []
            if tName is not None:
                tc_cols.append("tName = %s")
                tc_params.append(tName)
            if address is not None:
                tc_cols.append("address = %s")
                tc_params.append(address)

            if tID is not None and tc_cols:
                sql = (
                    "UPDATE TutoringCenter t SET "
                    + ", ".join(tc_cols)
                    + " WHERE tID = %s "
                    + "AND EXISTS (SELECT 1 FROM CenterManager WHERE tID = t.tID AND iID = %s);"
                )
                tc_params.extend([tID, iID])
                cursor.execute(sql, tuple(tc_params))

            # --- 3) UPDATE or INSERT (UPSERT Logic Manual) InstructorMedia (URLs) ---
            media_cols, media_params = [], []
            if profile_url is not None:
                media_cols.append("imageProfile = %s")
                media_params.append(profile_url)
            if reward_url is not None:
                media_cols.append("rewardURL = %s")
                media_params.append(reward_url)
            if video_url is not None:
                media_cols.append("videoURL = %s")
                media_params.append(video_url)
                
            if media_cols:
                # 3a. ลองทำการ UPDATE ก่อน (หากมีแถวอยู่แล้ว)
                sql_update = (
                    "UPDATE InstructorMedia SET "
                    + ", ".join(media_cols)
                    + " WHERE iID = %s;"
                )
                
                update_params = media_params + [iID]
                cursor.execute(sql_update, tuple(update_params))
                
                # 3b. ถ้า UPDATE ไม่สำเร็จ (แถวไม่พบ - rowcount == 0) ให้ทำการ INSERT
                if cursor.rowcount == 0:
                    # SQL สำหรับ INSERT:
                    sql_insert = """
                        INSERT INTO InstructorMedia (iID, imageProfile, rewardURL, videoURL)
                        VALUES (%s, %s, %s, %s);
                    """
                    # ใช้ค่าที่ส่งมา (ใช้ '' แทน None เพื่อป้องกัน NOT NULL error)
                    insert_values_final = [
                        iID,
                        profile_url or '', 
                        reward_url or '',
                        video_url or ''
                    ]
                    
                    cursor.execute(sql_insert, tuple(insert_values_final))


            conn.commit()
            cursor.close()
            return True

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            print(f"SQL execution error during update: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    # --- EDITED: เมธอดสำหรับลบบัญชี (รวมการลบ Center, ClassSlot, Enrollment) ---
    @staticmethod
    def delete_account(iID):
        """
        ลบ Instructor และข้อมูลที่เกี่ยวข้องทั้งหมด:
        1. ลบ ClassSlot ในศูนย์ที่ Instructor บริหาร (Enrollment ถูกลบโดย CASCADE)
        2. ลบ TutoringCenter ที่ Instructor บริหาร
        3. ลบ Instructor (ลบ CenterManager, InstructorMedia โดย CASCADE)
        """
        conn = InstructorEditDashboardServices._get_db_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cursor:
                
                # 1. ค้นหา tID ของศูนย์ที่ Instructor คนนี้บริหารอยู่
                cursor.execute(
                    "SELECT tID FROM CenterManager WHERE iID = %s;", 
                    (iID,)
                )
                center_manager_tID = cursor.fetchone()
                
                if center_manager_tID:
                    tID = center_manager_tID[0]
                    
                    # 2. ลบ ClassSlot ทั้งหมดใน Center นั้น
                    #    (หาก Enrollment มี CASCADE จาก ClassSlot, ข้อมูล Enroll จะถูกลบ)
                    cursor.execute(
                        "DELETE FROM ClassSlot WHERE tID = %s;",
                        (tID,)
                    )
                    
                    # 3. ลบ TutoringCenter ที่ Instructor บริหาร
                    cursor.execute(
                        "DELETE FROM TutoringCenter WHERE tID = %s;",
                        (tID,)
                    )
                
                # 4. ลบ Instructor
                #    (InstructorMedia และ CenterManager จะถูกลบโดย Foreign Key CASCADE)
                cursor.execute("DELETE FROM Instructor WHERE iID = %s;", (iID,))
            
            conn.commit()
            return True
        except psycopg2.Error as e:
            print(f"SQL execution error during delete account: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()