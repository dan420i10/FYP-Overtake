CREATE DATABASE overtake;
USE overtake;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    age INT
);

INSERT INTO users (name, email, password, age) VALUES 
('Danial Mahar', 'dani@gmail.com', '123', 22),
('Sara Malik', 'sara.m@example.com', '123', 25),
('Zain Ali', 'zain.a@example.com', '123', 30),
('Dua Fatima', 'dua.f@example.com', '123', 21),
('Hamza Sheikh', 'hamza.s@example.com', '123', 28),
('Ayesha Noor', 'ayesha.n@example.com', '123', 24),
('Bilal Siddiqui', 'bilal.s@example.com', '123', 27),
('Hania Amir', 'hania.a@example.com', '123', 23),
('Mustafa Raza', 'mustafa.r@example.com', '123', 29),
('Zoya Hassan', 'zoya.h@example.com', '123', 26);