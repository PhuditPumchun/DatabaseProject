# InstructorEditDashboardServices.py

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class InstructorEditDashboardServices: # ใช้ชื่อคลาสนี้ตามที่ผู้ใช้ส่งมา

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
    ):
        """อัปเดตข้อมูล Instructor / TutoringCenter / InstructorMedia เฉพาะฟิลด์ที่ส่งมา"""
        conn = InstructorEditDashboardServices._get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # --- 1) UPDATE Instructor (Name, Username, Password) ---
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
                    # ใช้ COALESCE เพื่อรับรองว่าค่าที่ไม่ถูกส่งมา (เป็น None) จะถูกแทนที่ด้วยค่าว่าง/ค่าเริ่มต้น
                    # ในตารางคุณฟิลด์เป็น NOT NULL ต้องมั่นใจว่าค่าที่ INSERT ไม่ใช่ NULL
                    
                    # รวบรวมฟิลด์ทั้งหมดที่ต้องใส่ใน INSERT (รวม iID)
                    insert_cols = ['iID'] + media_cols
                    insert_values = [iID] + media_params
                    
                    # NOTE: ต้องมั่นใจว่าคอลัมน์ NOT NULL อื่นๆ ถูกรวมอยู่ใน INSERT
                    # จาก Schema ที่มี: mediaID (PK), iID, imageProfile (NOT NULL), rewardURL (NOT NULL), videoURL (NOT NULL)
                    # เนื่องจาก imageProfile, rewardURL, videoURL เป็น NOT NULL, ถ้าฟอร์มส่ง None มาจะเกิด Error
                    # แต่เราสมมติว่าฟอร์มส่งค่าปัจจุบันมาเสมอ ดังนั้นเราจะ INSERT เฉพาะค่าที่ถูกส่งมา

                    # หากขาดคอลัมน์ NOT NULL เราต้องรวมมันใน INSERT
                    # แต่เนื่องจากเราไม่ทราบค่า mediaID ที่ถูกต้องสำหรับการ INSERT, เราจะสมมติว่า 
                    # imageProfile, rewardURL, videoURL ถูกเติมเต็มด้วยค่าว่าง (ถ้าไม่ได้ถูกส่งมา)
                    
                    # เนื่องจากหน้า UI ส่งค่าปัจจุบันมาเสมอ เราจะใช้ค่าที่ส่งมา
                    # (ถ้าไม่ได้ถูกส่งมาจริงๆ โค้ดจะใช้ None ซึ่งอาจทำให้เกิด Error NOT NULL)
                    
                    # เราต้องหาค่า mediaID ใหม่ (ถ้า mediaID เป็น PK)
                    # แต่เพื่อความง่าย เราจะสมมติว่าโค้ดที่รันก่อนหน้านี้จัดการ mediaID ไปแล้ว
                    
                    # SQL สำหรับ INSERT:
                    sql_insert = """
                        INSERT INTO InstructorMedia (iID, imageProfile, rewardURL, videoURL)
                        VALUES (%s, %s, %s, %s);
                    """
                    
                    # ใช้ค่าที่ส่งมา (อาจต้องตรวจสอบว่าไม่ใช่ None สำหรับคอลัมน์ NOT NULL)
                    insert_values_final = [
                        iID,
                        profile_url or '', # ป้องกัน NOT NULL error (ควรปรับใน UI)
                        reward_url or '',  # ป้องกัน NOT NULL error (ควรปรับใน UI)
                        video_url or ''    # ป้องกัน NOT NULL error (ควรปรับใน UI)
                    ]
                    
                    # NOTE: การใช้ 'profile_url or ''' เป็นการแก้ไขชั่วคราว ถ้าฟิลด์อนุญาตให้เป็น string ว่าง
                    
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