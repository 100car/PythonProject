-- CREATE DATABASE FRUITS_VEGETABLES; ТИРИ-ПИРИ

-- Створіть однотабличну базу даних «Овочі та фрукти», яка зберігатиме таку інформацію:
-- ■ Назва;
-- ■ Тип (овоч або фрукт);
-- ■ Колір;
-- ■ Калорійність;
-- ■ Короткий опис.
CREATE TABLE PRODUCE (
	PRODUCE_ID SERIAL PRIMARY KEY,
	NAME VARCHAR(30),
	TYPE VARCHAR(9),
	COLOR VARCHAR(10),
	CALORIES INT,
	DESCRIPTIONS TEXT
);

-- ЗАПОВНЕННЯ
INSERT INTO produce (name, type, color, calories, descriptions) VALUES
('Apple', 'Fruit', 'Red', 52, 'Crisp and juicy'),
('Banana', 'Fruit', 'Yellow', 89, 'Soft and sweet'),
('Carrot', 'Vegetable', 'Orange', 41, 'Crunchy root vegetable'),
('Tomato', 'Vegetable', 'Red', 18, 'Often mistaken for a fruit'),
('Strawberry', 'Fruit', 'Red', 33, 'Sweet, with tiny seeds outside'),
('Lemon', 'Fruit', 'Yellow', 29, 'Sour citrus fruit'),
('Cucumber', 'Vegetable', 'Green', 16, 'Refreshing and hydrating'),
('Grape', 'Fruit', 'Purple', 69, 'Small and sweet clusters'),
('Potato', 'Vegetable', 'Brown', 77, 'Starchy tuber'),
('Orange', 'Fruit', 'Orange', 47, 'Juicy citrus fruit'),
('Bell Pepper', 'Vegetable', 'Red', 31, 'Sweet and crunchy'),
('Blueberry', 'Fruit', 'Blue', 57, 'Tiny antioxidant-rich berries'),
('Spinach', 'Vegetable', 'Green', 23, 'Leafy green, rich in iron'),
('Pineapple', 'Fruit', 'Yellow', 50, 'Tropical and tangy'),
('Broccoli', 'Vegetable', 'Green', 34, 'Tree-like vegetable, rich in vitamins'),
('Peach', 'Fruit', 'Pink', 39, 'Soft, fuzzy skin, juicy inside'),
('Eggplant', 'Vegetable', 'Purple', 25, 'Smooth-skinned and versatile'),
('Watermelon', 'Fruit', 'Green', 30, 'Juicy and refreshing'),
('Cherries', 'Fruit', 'Red', 50, 'Small, sweet and tart'),
('Onion', 'Vegetable', 'White', 40, 'Adds flavor to many dishes'),
('Pear', 'Fruit', 'Green', 57, 'Sweet, with soft flesh'),
('Garlic', 'Vegetable', 'White', 149, 'Strong flavor, used in cooking'),
('Mango', 'Fruit', 'Orange', 60, 'Sweet tropical fruit'),
('Zucchini', 'Vegetable', 'Green', 17, 'Soft summer squash'),
('Plum', 'Fruit', 'Purple', 46, 'Sweet and tart stone fruit'),
('Cabbage', 'Vegetable', 'Green', 25, 'Leafy vegetable, good for salads'),
('Kiwi', 'Fruit', 'Brown', 61, 'Tart fruit with green flesh'),
('Radish', 'Vegetable', 'Red', 16, 'Spicy and crunchy root'),
('Pomegranate', 'Fruit', 'Red', 83, 'Juicy seeds, slightly tart'),
('Lettuce', 'Vegetable', 'Green', 15, 'Leafy base for salads');

-- ■ Відображення всієї інформації з таблиці овочів та фруктів;
SELECT * 
FROM PRODUCE; 

-- ■ Відображення усіх овочів;
SELECT * 
FROM PRODUCE
WHERE TYPE = 'Fruit'; 

-- ■ Відображення усіх фруктів;
SELECT * 
FROM PRODUCE
WHERE TYPE = 'Vegetable'; 

-- ■ Відображення усіх назв овочів та фруктів;
SELECT NAME 
FROM PRODUCE;

-- ■ Відображення усіх кольорів. Кольори мають бути унікальними;
SELECT DISTINCT COLOR 
FROM PRODUCE;

-- ■ Відображення фруктів певного кольору;
SELECT * 
FROM PRODUCE
WHERE TYPE = 'Fruit' AND COLOR = 'Red'; 

-- ■ Відображення овочів певного кольору.
SELECT * 
FROM PRODUCE
WHERE TYPE = 'Vegetable' AND COLOR = 'Green'; 