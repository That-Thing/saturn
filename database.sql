-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               10.4.11-MariaDB - mariadb.org binary distribution
-- Server OS:                    Win64
-- HeidiSQL Version:             11.3.0.6295
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Dumping database structure for saturn
CREATE DATABASE IF NOT EXISTS `saturn` /*!40100 DEFAULT CHARACTER SET utf8mb4 */;
USE `saturn`;

-- Dumping structure for table saturn.accounts
CREATE TABLE IF NOT EXISTS `accounts` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'User ID',
  `username` varchar(50) NOT NULL COMMENT 'Username',
  `password` text NOT NULL COMMENT 'Encrypted password',
  `email` varchar(100) DEFAULT NULL COMMENT 'Optional email',
  `group` int(11) NOT NULL DEFAULT 0 COMMENT 'User permissions group',
  `date` int(11) NOT NULL COMMENT 'User creation date',
  `ip` varchar(50) DEFAULT NULL COMMENT 'Registration IP',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=utf8;

-- Data exporting was unselected.

-- Dumping structure for table saturn.banners
CREATE TABLE IF NOT EXISTS `banners` (
  `board` tinytext NOT NULL,
  `filename` text NOT NULL,
  `filesize` int(11) NOT NULL DEFAULT 0 COMMENT 'File size in KB'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Data exporting was unselected.

-- Dumping structure for table saturn.boards
CREATE TABLE IF NOT EXISTS `boards` (
  `uri` varchar(8) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` varchar(250) NOT NULL,
  `owner` varchar(250) NOT NULL,
  `anonymous` tinytext NOT NULL,
  `message` tinytext DEFAULT '',
  `posts` int(250) DEFAULT NULL,
  `PPH` int(250) DEFAULT NULL,
  `users` int(250) DEFAULT NULL,
  `captcha` tinyint(1) NOT NULL DEFAULT 0,
  `perPage` int(250) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='The list of boards. ';

-- Data exporting was unselected.

-- Dumping structure for table saturn.groups
CREATE TABLE IF NOT EXISTS `groups` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Data exporting was unselected.

-- Dumping structure for table saturn.posts
CREATE TABLE IF NOT EXISTS `posts` (
  `name` tinytext DEFAULT NULL COMMENT 'Post name',
  `subject` tinytext DEFAULT NULL COMMENT 'Post subject',
  `options` tinytext DEFAULT NULL COMMENT 'Post options',
  `message` text NOT NULL COMMENT 'Post message content',
  `number` int(11) NOT NULL COMMENT 'Post number',
  `date` int(11) NOT NULL COMMENT 'Unix Timestamp',
  `type` int(1) NOT NULL COMMENT '1 for thread, 2 for reply',
  `thread` int(11) DEFAULT NULL COMMENT 'Thread tied to a reply',
  `board` tinytext NOT NULL COMMENT 'Board that the post was made on',
  `files` text DEFAULT NULL COMMENT 'File paths',
  `filenames` text DEFAULT NULL COMMENT 'Names of files tied to post',
  `ip` tinytext DEFAULT NULL COMMENT 'User IP',
  `spoiler` int(11) NOT NULL DEFAULT 0 COMMENT '0 for normal, 1 for spoiler',
  `password` text NOT NULL COMMENT 'Password for post deletion',
  `trip` text DEFAULT NULL COMMENT 'Tripcode or role signature',
  `replies` text DEFAULT NULL COMMENT 'Replies for posts'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Data exporting was unselected.

-- Dumping structure for table saturn.rules
CREATE TABLE IF NOT EXISTS `rules` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content` text NOT NULL COMMENT 'Rule content',
  `type` int(11) NOT NULL COMMENT '0 for global 1 for board',
  `board` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4;

-- Data exporting was unselected.

-- Dumping structure for table saturn.server
CREATE TABLE IF NOT EXISTS `server` (
  `posts` int(11) NOT NULL DEFAULT 0,
  `salt` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Data exporting was unselected.

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
