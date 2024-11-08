-- Adminer 4.8.1 MySQL 8.0.30 dump

SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

SET NAMES utf8mb4;

-- DROP DATABASE IF EXISTS `klastering_siswa`;  -- Removed
-- CREATE DATABASE `klastering_siswa`;          -- Removed
USE `klastering_siswa`;  -- Keep this to use the existing database

DROP TABLE IF EXISTS `dataset`;
CREATE TABLE `dataset` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `id_user` INT,
  `nis` int NOT NULL,
  `nama_siswa` varchar(225) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `kelas` VARCHAR(50) DEFAULT NULL,
  `mapel1` int DEFAULT NULL,
  `mapel2` int DEFAULT NULL,
  `mapel3` int DEFAULT NULL,
  `mapel4` int DEFAULT NULL,
  `mapel5` int DEFAULT NULL,
  `nilai_total` int DEFAULT NULL,
  `rata_rata` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `cluster` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `jurusan` VARCHAR(50) DEFAULT NULL,
  `semester` INT DEFAULT NULL,
  `tahun_ajaran` VARCHAR(9) DEFAULT NULL,
  PRIMARY KEY (`id`)
); ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS `instruksi`;
CREATE TABLE `instruksi` (
  `id` int NOT NULL AUTO_INCREMENT,
  `kluster` int NOT NULL,
  `iterasi` int NOT NULL,
  `parameter` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(225) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `password` varchar(225) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

TRUNCATE `users`;
INSERT INTO `users` (`id`, `username`, `email`, `password`) VALUES
(1,	'admin',	'admin@gmail.com',	'admin');

-- 2024-07-27 13:13:49
