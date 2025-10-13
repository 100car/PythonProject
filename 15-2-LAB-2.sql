-- Завдання 1. Створіть наступні запити для бази даних з оцінками студентів із попереднього практичного завдання:
-- ■ Показати ПІБ усіх студентів з мінімальною оцінкою у вказаному діапазоні.
SELECT PIB, MIN_SUBJECT_GRADE 
FROM STUDENTS
WHERE MIN_SUBJECT_GRADE BETWEEN 60 AND 70;

-- ■ Показати інформацію про студентів, яким виповнилося 22 рокИ.
SELECT PIB, BIRTHDAY, EXTRACT(YEAR FROM AGE(BIRTHDAY)) 
FROM STUDENTS
WHERE AGE(BIRTHDAY) > '22 YEAR'

-- ■ Показати інформацію про студентів з віком, у вказаному діапазоні.
SELECT PIB, BIRTHDAY, AGE(BIRTHDAY) 
FROM STUDENTS
WHERE AGE(BIRTHDAY) BETWEEN '20 YEAR' AND '22 YEAR';

-- ■ Показати інформацію про студентів із конкретним ім’ям. Наприклад, показати студентів з ім’ям Борис.
SELECT PIB
FROM STUDENTS
WHERE PIB LIKE '%Артем%';

-- ■ Показати інформацію про студентів, в номері яких є дві п"ятірки.
SELECT PIB, TELEPHONE
FROM STUDENTS
WHERE TELEPHONE LIKE '%5%5%'

--------------------------------------- А ТЕПЕР НАЙЦІКАВІШЕ ----------------------------------------------
-- Завдання 2
-- Створіть наступні запити для бази даних з оцінками студентів із попереднього практичного завдання:
-- ■ Показати мінімальну середню оцінку по всіх студентах.
SELECT PIB, MIN_SUBJECT_GRADE
FROM STUDENTS;

-- ■ Показати максимальну середню оцінку по всіх студентах.
SELECT PIB, MAX_SUBJECT_GRADE
FROM STUDENTS;

-- ■ Показати статистику міст. Має відображатися назва міста та кількість студентів з цього міста.
SELECT CITY, COUNT(*)
FROM STUDENTS
GROUP BY CITY;

-- ■ Показати статистику студентів. Має відображатися назва країни та кількість студентів з цієї країни.
SELECT COUNTRY, COUNT(*)
FROM STUDENTS
GROUP BY COUNTRY;

-- ■ Показати кількість студентів з мінімальною середньою оцінкою з математики.
SELECT COUNT(*)
FROM STUDENTS
WHERE LOWER(MIN_SUBJECT_NAME) = 'фізика';

-- ■ Показати кількість студентів з максимальною середньою оцінкою з математики.
SELECT COUNT(*)
FROM STUDENTS
WHERE UPPER(MAX_SUBJECT_NAME) = 'ПРОГРАМУВАННЯ';

-- ■ Показати кількість студентів у кожній групі.
SELECT GROUP_NAME, COUNT(*)
FROM STUDENTS
GROUP BY GROUP_NAME;

-- ■ Показати середню оцінку групи.
SELECT GROUP_NAME, AVG(AVG_GRADE)
FROM STUDENTS
GROUP BY GROUP_NAME;

-- ПОКАЗАТИ КІЛЬКІСТЬ СТУДЕНТІВ З КОЖНОГО МІСТА IT-21
SELECT CITY, COUNT(CITY) ---, STRING_AGG(PIB:: TEXT)
FROM STUDENTS
WHERE GROUP_NAME = 'ІТ-21'
GROUP BY CITY;

-- ЗНАЙТИ СТУДЕНТА З НАЙБІЛЬШОЮ СЕРЕДНЬОЮ ОЦІНКОЮ
-- СПОЧАТКУ ШУКАЄМО НАЙБІЛЬШЕ СЕРЕДНЮ ОЦІНКУ
SELECT MAX(AVG_GRADE) 
FROM STUDENTS;
-- А ТЕПЕР СТУДЕНТА З 92 (РЕЗУЛЬТАТ ПОПЕРЕДНЬОЇ ПІДЗАДАЧІ)
SELECT PIB, AVG_GRADE
FROM STUDENTS
-- WHERE AVG_GRADE = 92
WHERE AVG_GRADE = (
	SELECT MAX(AVG_GRADE) 
	FROM STUDENTS);

-- ТЕ Ж САМЕ ЧЕРЕЗ ПРОМІЖНУ ЗМІННУ
WITH MAXIMUM_AVG AS (
	SELECT MAX(AVG_GRADE) AS COLUMN_AVG
	FROM STUDENTS
	)
SELECT PIB, AVG_GRADE
FROM STUDENTS, MAXIMUM_AVG
WHERE AVG_GRADE = MAXIMUM_AVG.COLUMN_AVG;

-- ПРОДОВЖЕННЯ
WITH MAXIMUM_AVG AS (
	SELECT MAX(AVG_GRADE) AS COLUMN_AVG
	FROM STUDENTS
	)
SELECT *
FROM STUDENTS, MAXIMUM_AVG

