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
    ):
        """อัปเดตข้อมูล Instructor / TutoringCenter / InstructorMedia เฉพาะฟิลด์ที่ส่งมา"""
        conn = InstructorEditDashboardServices._get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # --- 1) UPDATE Instructor (เฉพาะคอลัมน์ที่ส่งมา) ---
            set_cols, params = [], []
            if iName is not None:
                set_cols.append("iName = %s")
                params.append(iName)
            if iUsername is not None:
                set_cols.append("iUsername = %s")
                params.append(iUsername)
            if iPassword:  # ถ้าส่งพาสเวิร์ดมา (ไม่ None/ไม่ว่าง) ให้อัปเดตด้วย
                set_cols.append("iPassword = %s")
                params.append(iPassword)

            if set_cols:
                sql = "UPDATE Instructor SET " + ", ".join(set_cols) + " WHERE iID = %s;"
                params.append(iID)
                cursor.execute(sql, tuple(params))

            # --- 2) UPDATE TutoringCenter (ต้องทราบ tID และมีอย่างน้อยหนึ่งคอลัมน์) ---
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

            # --- 3) UPDATE InstructorMedia (ต้องทราบ mediaID และมีอย่างน้อยหนึ่งคอลัมน์) ---
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

            if mediaID is not None and media_cols:
                sql = (
                    "UPDATE InstructorMedia SET "
                    + ", ".join(media_cols)
                    + " WHERE mediaID = %s AND iID = %s;"
                )
                media_params.extend([mediaID, iID])
                cursor.execute(sql, tuple(media_params))

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
