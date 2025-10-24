CREATE TABLE Subject (
  sID INTEGER,
  sName VARCHAR(255),
  PRIMARY KEY (sID)
);

CREATE TABLE Instructor (
  iID INTEGER,
  iName VARCHAR(255),
  sID INTEGER, -- 1 Instructor teaches 1 Subject
  expYear INTEGER,
  PRIMARY KEY (iID),
  FOREIGN KEY (sID) REFERENCES Subject(sID)
);

CREATE TABLE TutoringCenter (
  tID INTEGER,
  tName VARCHAR(255),
  address VARCHAR(255),
  PRIMARY KEY (tID)
);

CREATE TABLE CenterManager (
    tID INTEGER, -- PK, FK: 1 Center
    iID INTEGER UNIQUE, -- FK: 1 Instructor (ใช้ UNIQUE เพื่อบังคับความสัมพันธ์ 1:1)
    PRIMARY KEY (tID),
    FOREIGN KEY (tID) REFERENCES TutoringCenter(tID),
    FOREIGN KEY (iID) REFERENCES Instructor(iID)
);
-- --------------------------------------------------------------------------

CREATE TABLE Student (
  sID INTEGER,
  sName VARCHAR(255),
  PRIMARY KEY (sID)
);

CREATE TABLE ClassSlot (
  cID INTEGER,
  cDay VARCHAR(255),
  cTime VARCHAR(255),
  tID INTEGER,
  PRIMARY KEY (cID),
  FOREIGN KEY (tID) REFERENCES TutoringCenter(tID)
);

CREATE TABLE Enrollment (
  sID INTEGER,
  cID INTEGER,
  enrollDate DATE,
  paymentStatus VARCHAR(50),
  feeAmount DECIMAL(10, 2),
  PRIMARY KEY (sID, cID),
  FOREIGN KEY (sID) REFERENCES Student(sID),
  FOREIGN KEY (cID) REFERENCES ClassSlot(cID)
);

CREATE TABLE InstructorMedia (
  mediaID INTEGER,
  iID INTEGER,
  imageURL VARCHAR(512) NOT NULL,
  videoURL VARCHAR(512) NOT NULL,
  PRIMARY KEY (mediaID),
  FOREIGN KEY (iID) REFERENCES Instructor(iID)
);