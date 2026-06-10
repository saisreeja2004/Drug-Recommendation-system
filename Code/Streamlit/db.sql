DROP DATABASE IF EXISTS chatbot;
CREATE DATABASE chatbot;
USE chatbot;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(225),
    email VARCHAR(225),
    password VARCHAR(225)
);
