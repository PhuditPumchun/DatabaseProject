-- 1. Subject (วิชา)
INSERT INTO Subject (sID, sName) VALUES
(101, 'Mathematics'),
(102, 'Physics'),
(103, 'Chemistry');

---

-- 2. Instructor (ผู้สอน)
-- สมมติว่า sID 101 คือ Mathematics และ sID 102 คือ Physics
INSERT INTO Instructor (iID, iName, sID, expYear) VALUES
(1, 'Mr. Somchai Klinhom', 101, 5),    -- สอนคณิตศาสตร์
(2, 'Ms. Sudarat Jaisue', 102, 8),     -- สอนฟิสิกส์
(3, 'Dr. Preecha Vongyai', 101, 15);   -- สอนคณิตศาสตร์

---

-- 3. TutoringCenter (ศูนย์กวดวิชา)
-- สมมติว่า iID 1 เป็นผู้รับผิดชอบของ Center A, iID 2 ของ Center B
INSERT INTO TutoringCenter (tID, tName, address, iID) VALUES
(501, 'Tutor Center A', '123 Rama I Rd, Bangkok', 1),
(502, 'Smart Brain Institute', '456 Phahonyothin Rd, Nonthaburi', 2);

---

-- 4. Student (นักเรียน)
INSERT INTO Student (sID, sName) VALUES
(2001, 'Akarawat Choosak'),
(2002, 'Boonchai Suksawat'),
(2003, 'Chanya Rakdee');

---

-- 5. ClassSlot (รอบเรียน/ตารางเรียน)
-- iID 1 (Mr. Somchai) สอนที่ tID 501 (Center A)
-- iID 2 (Ms. Sudarat) สอนที่ tID 502 (Smart Brain Institute)
INSERT INTO ClassSlot (cID, cDay, cTime, iID, tID) VALUES
(301, 'Monday', '18:00-20:00', 1, 501),   -- คณิต, จันทร์เย็น, Center A, Somchai
(302, 'Saturday', '09:00-12:00', 2, 502), -- ฟิสิกส์, เสาร์เช้า, Smart Brain, Sudarat
(303, 'Tuesday', '16:00-18:00', 1, 501);  -- คณิต, อังคารเย็น, Center A, Somchai

---

-- 6. Enrollment (การลงทะเบียนเรียน)
-- sID 2001 ลงเรียน cID 301 (คณิต) และ cID 302 (ฟิสิกส์)
-- sID 2002 ลงเรียน cID 301 (คณิต)
INSERT INTO Enrollment (sID, cID, enrollDate, paymentStatus, feeAmount) VALUES
(2001, 301, '2025-09-01', 'Paid', 3500.00),
(2001, 302, '2025-09-05', 'Paid', 4500.00),
(2002, 301, '2025-09-01', 'Pending', 3500.00);

---

-- 7. InstructorMedia (สื่อของผู้สอน)
-- iID 1 (Mr. Somchai) มีสื่อ 2 ชิ้น
INSERT INTO InstructorMedia (mediaID, iID, mediaType, mediaURL, mediaTitle, uploadDate) VALUES
(4001, 1, 'YouTube VDO', 'https://youtube.com/math-tutor-ch1', 'Basic Algebra Tutorial', '2025-08-15'),
(4002, 1, 'PDF Document', 'https://example.com/math-notes-01.pdf', 'Advanced Calculus Notes', '2025-09-20'),
(4003, 2, 'YouTube VDO', 'https://youtube.com/physics-guru-ch2', 'Quantum Mechanics Intro', '2025-07-01');