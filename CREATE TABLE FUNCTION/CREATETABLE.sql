CREATE TABLE Subject (
  sID INTEGER,
  sName VARCHAR(255),
  PRIMARY KEY (sID)
);

-- *** Entities: Instructor (1 Instructor teaches 1 Subject) ***
CREATE TABLE Instructor (
  iID INTEGER,
  iName VARCHAR(255),
  sID INTEGER,
  expYear INTEGER,
  PRIMARY KEY (iID),
  FOREIGN KEY (sID) REFERENCES Subject(sID)
);

-- *** Entities: TutoringCenter ***
CREATE TABLE TutoringCenter (
  tID INTEGER,
  tName VARCHAR(255),  -- ข้อมูลที่ขาดหายไป
  address VARCHAR(255),
  iID INTEGER, -- ผู้รับผิดชอบ (Responsible Instructor)
  PRIMARY KEY (tID),
  FOREIGN KEY (iID) REFERENCES Instructor(iID)
);

-- *** Entities: Student ***
CREATE TABLE Student (
  sID INTEGER,
  sName VARCHAR(255),
  PRIMARY KEY (sID)
);

-- *** Entities: ClassSlot (แทน Class เดิม) ***
CREATE TABLE ClassSlot (
  cID INTEGER,
  cDay VARCHAR(255),
  cTime VARCHAR(255), -- ใช้ Varchar สำหรับการแสดงผล (เช่น 10:00-11:00)
  iID INTEGER, -- ผู้สอน
  tID INTEGER,     -- สถานที่สอน
  PRIMARY KEY (cID),
  FOREIGN KEY (iID) REFERENCES Instructor(iID),
  FOREIGN KEY (tID) REFERENCES TutoringCenter(tID)
);

-- *** Relationship: Enrollment (Student M:N ClassSlot) ***
CREATE TABLE Enrollment (
  sID INTEGER,
  cID INTEGER,
  enrollDate DATE,
  paymentStatus VARCHAR(50),
  feeAmount DECIMAL(10, 2),
  PRIMARY KEY (sID, cID), -- Composite Key
  FOREIGN KEY (sID) REFERENCES Student(sID),
  FOREIGN KEY (cID) REFERENCES ClassSlot(cID)
);

-- *** Relationship: InstructorMedia (Instructor 1:N Media) ***
CREATE TABLE InstructorMedia (
  mediaID INTEGER,
  iID INTEGER,  -- Foreign Key เชื่อมไปที่ Instructor
  mediaType VARCHAR(50) NOT NULL, -- เช่น 'YouTube VDO'
  mediaURL VARCHAR(512) NOT NULL, -- ลิงก์ YouTube
  mediaTitle VARCHAR(255),
  uploadDate DATE,
  PRIMARY KEY (mediaID),
  FOREIGN KEY (iID) REFERENCES Instructor(iID)
);