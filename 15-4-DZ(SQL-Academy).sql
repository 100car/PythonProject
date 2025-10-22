-- -----------------------------
-- 1. Таблиці
-- -----------------------------

-- Faculties
CREATE TABLE Faculties (
    Id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Financing DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (Financing >= 0),
    Name VARCHAR(100) NOT NULL UNIQUE CHECK (Name <> '')
);

-- Departments
CREATE TABLE Departments (
    Id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Financing DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (Financing >= 0),
    Name VARCHAR(100) NOT NULL UNIQUE CHECK (Name <> ''),
    FacultyId INT NOT NULL REFERENCES Faculties(Id)
);

-- Groups
CREATE TABLE Groups (
    Id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Name VARCHAR(10) NOT NULL UNIQUE CHECK (Name <> ''),
    Year INT NOT NULL CHECK (Year BETWEEN 1 AND 5),
    DepartmentId INT NOT NULL REFERENCES Departments(Id)
);

-- Curators
CREATE TABLE Curators (
    Id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Name TEXT NOT NULL CHECK (Name <> ''),
    Surname TEXT NOT NULL CHECK (Surname <> '')
);

-- GroupsCurators
CREATE TABLE GroupsCurators (
    Id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    CuratorId INT NOT NULL REFERENCES Curators(Id),
    GroupId INT NOT NULL REFERENCES Groups(Id)
);

-- Teachers
CREATE TABLE Teachers (
    Id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Name TEXT NOT NULL CHECK (Name <> ''),
    Surname TEXT NOT NULL CHECK (Surname <> ''),
    Salary DECIMAL(10,2) NOT NULL CHECK (Salary > 0)
);

-- Subjects
CREATE TABLE Subjects (
    Id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Name VARCHAR(100) NOT NULL UNIQUE CHECK (Name <> '')
);

-- Lectures
CREATE TABLE Lectures (
    Id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    LectureRoom TEXT NOT NULL CHECK (LectureRoom <> ''),
    SubjectId INT NOT NULL REFERENCES Subjects(Id),
    TeacherId INT NOT NULL REFERENCES Teachers(Id)
);

-- GroupsLectures
CREATE TABLE GroupsLectures (
    Id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    GroupId INT NOT NULL REFERENCES Groups(Id),
    LectureId INT NOT NULL REFERENCES Lectures(Id)
);

-- -----------------------------
-- Faculties
-- -----------------------------
INSERT INTO Faculties (Financing, Name) VALUES
(300000.00, 'Computer Science'),
(250000.00, 'Mathematics'),
(200000.00, 'Physics');

-- -----------------------------
-- Departments
-- -----------------------------
INSERT INTO Departments (Financing, Name, FacultyId) VALUES
(150000.00, 'Department of Informatics', 1),
(120000.00, 'Department of Software Engineering', 1),
(130000.00, 'Department of Math', 2),
(100000.00, 'Department of Physics', 3);

-- -----------------------------
-- Groups
-- -----------------------------
INSERT INTO Groups (Name, Year, DepartmentId) VALUES
('P101', 1, 1),
('P102', 2, 1),
('P103', 3, 2),
('P104', 4, 2),
('P105', 5, 3),
('P106', 1, 3),
('P107', 2, 3),
('P108', 5, 4);

-- -----------------------------
-- Curators
-- -----------------------------
INSERT INTO Curators (Name, Surname) VALUES
('Olena', 'Petrenko'),
('Ihor', 'Savchenko'),
('Marina', 'Koval'),
('Vasyl', 'Tkachuk'),
('Svitlana', 'Melnyk');

-- -----------------------------
-- GroupsCurators
-- -----------------------------
INSERT INTO GroupsCurators (CuratorId, GroupId) VALUES
(1,1),(1,2),(2,3),(2,7),(3,4),(4,5),(5,6),(3,8);

-- -----------------------------
-- Teachers
-- -----------------------------
INSERT INTO Teachers (Name, Surname, Salary) VALUES
('Samantha','Adams',1500),
('John','Smith',1200),
('Alice','Johnson',1100),
('Michael','Brown',1300),
('Emma','Davis',1250);

-- -----------------------------
-- Subjects
-- -----------------------------
INSERT INTO Subjects (Name) VALUES
('Python Programming'),
('Database Theory'),
('Math'),
('Physics'),
('Software Engineering');

-- -----------------------------
-- Lectures
-- -----------------------------
INSERT INTO Lectures (LectureRoom, SubjectId, TeacherId) VALUES
('B101', 1, 1),
('B103', 2, 1),
('B102', 3, 2),
('B103', 2, 3),
('B201', 4, 4),
('B202', 5, 5);

-- -----------------------------
-- GroupsLectures
-- -----------------------------
INSERT INTO GroupsLectures (GroupId, LectureId) VALUES
(1,1),(2,1),(3,2),(4,3),(5,4),(6,4),(7,2),(8,5);

-- -----------------------------
-- 3. Запити (завдання 1-11)
-- -----------------------------

-- 1. Всі можливі пари викладачів і груп (через ланцюжок)
SELECT t.Name, t.Surname, g.Name AS GroupName
FROM Teachers t
JOIN Lectures l ON t.Id = l.TeacherId
JOIN GroupsLectures gl ON l.Id = gl.LectureId
JOIN Groups g ON gl.GroupId = g.Id;

-- 2. Факультети, фонд кафедр яких НЕ перевищує фонд факультету
SELECT f.Name
FROM Faculties f
JOIN Departments d ON d.FacultyId = f.Id
GROUP BY f.Id, f.Name, f.Financing
HAVING SUM(d.Financing) <= f.Financing;

-- 3. Прізвища кураторів і список груп
SELECT c.Surname, STRING_AGG(g.Name, ', ') AS GroupsList
FROM GroupsCurators gc
JOIN Curators c ON gc.CuratorId = c.Id
JOIN Groups g ON gc.GroupId = g.Id
GROUP BY c.Id, c.Surname;

-- 4. Імена та прізвища викладачів, які читають лекції у групі «P107»
SELECT DISTINCT t.Name, t.Surname
FROM Teachers t
JOIN Lectures l ON t.Id = l.TeacherId
JOIN GroupsLectures gl ON l.Id = gl.LectureId
JOIN Groups g ON gl.GroupId = g.Id
WHERE g.Name = 'P107';

-- 5. Прізвища викладачів і назви факультетів, де вони читають
SELECT DISTINCT t.Surname, f.Name AS FacultyName
FROM Teachers t
JOIN Lectures l ON t.Id = l.TeacherId
JOIN GroupsLectures gl ON l.Id = gl.LectureId
JOIN Groups g ON gl.GroupId = g.Id
JOIN Departments d ON g.DepartmentId = d.Id
JOIN Faculties f ON d.FacultyId = f.Id;

-- 6. Назви кафедр і груп, які до них належать
SELECT d.Name AS DepartmentName, STRING_AGG(g.Name, ', ') AS GroupsList
FROM Departments d
JOIN Groups g ON g.DepartmentId = d.Id
GROUP BY d.Id, d.Name;

-- 7. Назви предметів, які викладає викладач «Samantha Adams»
SELECT STRING_AGG(s.Name, ', ') AS Subjects
FROM Teachers t
JOIN Lectures l ON t.Id = l.TeacherId
JOIN Subjects s ON l.SubjectId = s.Id
WHERE t.Name='Samantha' AND t.Surname='Adams';

-- 8. Назви кафедр, на яких викладається дисципліна «Database Theory»
SELECT DISTINCT d.Name
FROM Subjects s
JOIN Lectures l ON s.Id = l.SubjectId
JOIN GroupsLectures gl ON l.Id = gl.LectureId
JOIN Groups g ON gl.GroupId = g.Id
JOIN Departments d ON g.DepartmentId = d.Id
WHERE s.Name='Database Theory';

-- 9. Назви груп, що належать до факультету «Computer Science»
SELECT g.Name
FROM Groups g
JOIN Departments d ON g.DepartmentId = d.Id
JOIN Faculties f ON d.FacultyId = f.Id
WHERE f.Name='Computer Science';

-- 10. Назви груп 5-го курсу і їх факультети
SELECT g.Name AS GroupName, f.Name AS FacultyName
FROM Groups g
JOIN Departments d ON g.DepartmentId = d.Id
JOIN Faculties f ON d.FacultyId = f.Id
WHERE g.Year=5;

-- 11. Повні імена викладачів і лекції в аудиторії «B103»
SELECT t.Name, t.Surname, s.Name AS SubjectName, g.Name AS GroupName
FROM Teachers t
JOIN Lectures l ON t.Id = l.TeacherId
JOIN Subjects s ON l.SubjectId = s.Id
JOIN GroupsLectures gl ON l.Id = gl.LectureId
JOIN Groups g ON gl.GroupId = g.Id
WHERE l.LectureRoom='B103';
