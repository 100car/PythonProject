SELECT *
FROM PRODUCTS;

-- Завдання 1
-- Створіть наступні запити для бази даних з інформацією про овочі та фрукти з попереднього домашнього завдання:
-- ■ Відображення усіх овочів з калорійністю, менше вказаної.
SELECT *
FROM PRODUCTS
WHERE calories < 20;

-- ■ Відображення усіх фруктів з калорійністю у вказаному діапазоні.
SELECT *
FROM PRODUCTS
WHERE calories BETWEEN 20 AND 50;

-- ■ Відображення усіх овочів, у назві яких є вказане слово. Наприклад, слово: Potato.
SELECT *
FROM PRODUCTS
WHERE type = 'Vegetable' AND name LIKE '%Potato%';

-- ■ Відображення усіх овочів та фруктів, у короткому описі яких є вказане слово. Наприклад, слово: sweet.
SELECT *
FROM PRODUCTS
WHERE UPPER(descriptions) LIKE '%SWEET%';

-- ■ Показати усі овочі та фрукти жовтого або червоного кольору.
SELECT *
FROM PRODUCTS
WHERE LOWER(color) = 'red' OR LOWER(color) = 'yellow';

-- Завдання 2. Створіть наступні запити для бази даних з інформацією про овочі та фрукти з попереднього домашнього завдання:
-- ■ Показати кількість овочів.
SELECT COUNT(*) AS VEGETABLES_TOTAL
FROM PRODUCTS
WHERE type = 'Vegetable';

-- ■ Показати кількість фруктів.
SELECT COUNT(*) AS FRUITS_TOTAL
FROM PRODUCTS
WHERE type = 'Fruit';

-- ■ Показати кількість овочів та фруктів заданого кольору.
SELECT COUNT(*) AS RED_COLOR_TOTAL
FROM PRODUCTS
WHERE color = 'Red'
GROUP BY color;

-- ■ Показати кількість овочів та фруктів кожного кольору.
SELECT color, COUNT(*) AS COLOR_TOTAL
FROM PRODUCTS
GROUP BY color;

-- ■ Показати колір мінімальної кількості овочів та фруктів.
-- ■ РОБЛЮ ЧЕРЕЗ ТИМЧАСОВУ ТАБЛИЦЮ color_counts І ПІДЗАПИТ
WITH color_counts AS (
    SELECT color, COUNT(*) AS COLOR_TOTAL
    FROM PRODUCTS
    GROUP BY color
)
SELECT color, COLOR_TOTAL
FROM color_counts
WHERE COLOR_TOTAL = (
	SELECT MIN(COLOR_TOTAL) 
	FROM color_counts);

-- ■ Показати колір максимальної кількості овочів та фруктів.
WITH color_counts AS (
    SELECT color, COUNT(*) AS COLOR_TOTAL
    FROM PRODUCTS
    GROUP BY color
)
SELECT color, COLOR_TOTAL
FROM color_counts
WHERE COLOR_TOTAL = (
	SELECT MAX(COLOR_TOTAL) 
	FROM color_counts);

-- ■ Показати мінімальну калорійність овочів та фруктів.
SELECT MIN(CALORIES)
FROM PRODUCTS;

-- ■ Показати максимальну калорійність овочів та фруктів.
SELECT MAX(CALORIES)
FROM PRODUCTS;


-- ■ Показати середню калорійність овочів та фруктів.
SELECT AVG(CALORIES)
FROM PRODUCTS;

-- ■ Показати фрукт з мінімальною калорійністю.
WITH fruits_table AS (
	SELECT *
	FROM PRODUCTS
	WHERE TYPE = 'Fruit'
)
SELECT NAME, CALORIES
FROM fruits_table
WHERE CALORIES = (
	SELECT MIN(CALORIES) 
	FROM fruits_table);

-- ■ Показати фрукт з максимальною калорійністю.
WITH fruits_table AS (
	SELECT *
	FROM PRODUCTS
	WHERE TYPE = 'Fruit'
)
SELECT NAME, CALORIES
FROM fruits_table
WHERE CALORIES = (
	SELECT MAX(CALORIES) 
	FROM fruits_table);