import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class InstructorEditDashboardServices:

    @staticmethod
    def _get_db_connection():
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
        mediaID=None,
        iName=None,
        iUsername=None,
        iPassword=None,
        tName=None,
        address=None,
        profile_url=None,
        reward_url=None,
        video_url=None,
        subjectID=None,
    ):
        """
        อัปเดตข้อมูล Instructor / TutoringCenter / InstructorMedia ให้เสร็จในทรานแซคชันเดียว
        - ถ้าไม่ได้ใส่รหัสผ่านใหม่ จะไม่แก้ iPassword
        - ถ้า InstructorMedia ไม่มี row เดิม → INSERT ใหม่ พร้อม mediaID ไม่เป็น NULL
        """

        conn = InstructorEditDashboardServices._get_db_connection()
        if not conn:
            return False

        try:
            cur = conn.cursor()

            # -------------------------------------------------
            # 1) UPDATE Instructor
            # -------------------------------------------------
            set_cols = []
            params = []

            if iName is not None:
                set_cols.append("iName = %s")
                params.append(iName)

            if iUsername is not None:
                set_cols.append("iUsername = %s")
                params.append(iUsername)

            # อัปเดต password เฉพาะถ้ากรอกใหม่
            if iPassword and iPassword.strip() != "":
                set_cols.append("iPassword = %s")
                params.append(iPassword)

            # อัปเดต subject (sID) ด้วยค่า subjectID จาก dropdown
            if subjectID is not None:
                set_cols.append("sID = %s")
                params.append(subjectID)

            if set_cols:
                sql = "UPDATE Instructor SET " + ", ".join(set_cols) + " WHERE iID = %s;"
                params.append(iID)
                cur.execute(sql, tuple(params))

            # -------------------------------------------------
            # 2) UPDATE TutoringCenter (เฉพาะศูนย์ที่ instructor คนนี้ดูแล)
            # -------------------------------------------------
            tc_cols = []
            tc_params = []

            if tName is not None:
                tc_cols.append("tName = %s")
                tc_params.append(tName)

            if address is not None:
                tc_cols.append("address = %s")
                tc_params.append(address)

            if tID is not None and tc_cols:
                sql_center = (
                    "UPDATE TutoringCenter t SET "
                    + ", ".join(tc_cols)
                    + " WHERE tID = %s "
                    + "AND EXISTS (SELECT 1 FROM CenterManager WHERE tID = t.tID AND iID = %s);"
                )
                tc_params.extend([tID, iID])
                cur.execute(sql_center, tuple(tc_params))

            # -------------------------------------------------
            # 3) UPSERT InstructorMedia
            # -------------------------------------------------

            # ถ้าไม่มีการแก้ media เลย ก็ข้าม
            touched_media = (
                profile_url is not None or
                reward_url  is not None or
                video_url   is not None
            )

            if touched_media:
                # ก่อนอื่นเช็กว่ามี row ของ instructor นี้อยู่แล้วหรือยัง
                cur.execute("SELECT mediaID FROM InstructorMedia WHERE iID = %s;", (iID,))
                row = cur.fetchone()

                if row:
                    # มีอยู่แล้ว -> UPDATE
                    existing_media_id = row[0]

                    media_set_cols = []
                    media_set_params = []

                    if profile_url is not None:
                        media_set_cols.append("imageProfile = %s")
                        media_set_params.append(profile_url)

                    if reward_url is not None:
                        media_set_cols.append("rewardURL = %s")
                        media_set_params.append(reward_url)

                    if video_url is not None:
                        media_set_cols.append("videoURL = %s")
                        media_set_params.append(video_url)

                    if media_set_cols:
                        sql_media_update = (
                            "UPDATE InstructorMedia SET "
                            + ", ".join(media_set_cols)
                            + " WHERE mediaID = %s AND iID = %s;"
                        )
                        media_set_params.extend([existing_media_id, iID])
                        cur.execute(sql_media_update, tuple(media_set_params))

                else:
                    # ยังไม่มี row -> ต้อง INSERT ใหม่พร้อม mediaID ที่ไม่เป็น NULL
                    # 1) หา mediaID ที่จะใช้
                    new_media_id = None

                    # ใช้ค่าจากฟอร์มถ้ามีส่งมา (hidden input mediaID)
                    if mediaID and str(mediaID).strip() != "":
                        try:
                            new_media_id = int(mediaID)
                        except ValueError:
                            new_media_id = None

                    # ถ้าไม่มี หรือไม่ใช่เลข -> สร้างใหม่จาก MAX(mediaID)+1
                    if new_media_id is None:
                        cur.execute("SELECT COALESCE(MAX(mediaID)+1, 1) FROM InstructorMedia;")
                        new_media_id = cur.fetchone()[0]

                    # เตรียมค่าที่จะ insert (ถ้า field ว่างในฟอร์ม เราจะเก็บเป็น '' ไม่ใช่ None ป้องกันปัญหา NOT NULL บางคอลัมน์)
                    insert_image   = profile_url if profile_url is not None else ''
                    insert_reward  = reward_url  if reward_url  is not None else ''
                    insert_video   = video_url   if video_url   is not None else ''

                    cur.execute("""
                        INSERT INTO InstructorMedia (mediaID, iID, imageProfile, rewardURL, videoURL)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (
                        new_media_id,
                        iID,
                        insert_image,
                        insert_reward,
                        insert_video
                    ))

            # -------------------------------------------------
            # commit
            # -------------------------------------------------
            conn.commit()
            cur.close()
            return True

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            print(f"SQL execution error during update: {e}")
            return False

        finally:
            if conn:
                conn.close()
