/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE IF NOT EXISTS `saturn` /*!40100 DEFAULT CHARACTER SET utf8mb4 */;
USE `saturn`;

-- accounts
CREATE TABLE IF NOT EXISTS `accounts` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'User ID',
  `username` varchar(50) NOT NULL COMMENT 'Username',
  `password` text NOT NULL COMMENT 'Encrypted password',
  `email` varchar(100) DEFAULT NULL COMMENT 'Optional email',
  `group` int(11) NOT NULL DEFAULT 999 COMMENT 'User permissions group',
  `date` int(11) NOT NULL COMMENT 'User creation date',
  `ip` varchar(50) DEFAULT NULL COMMENT 'Registration IP',
  `banned` tinyint(1) NOT NULL DEFAULT 0 COMMENT '1 if banned, 0 if not. ',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=94 DEFAULT CHARSET=utf8;

-- banners
CREATE TABLE IF NOT EXISTS `banners` (
  `board` tinytext NOT NULL,
  `filename` text NOT NULL,
  `filesize` int(11) NOT NULL DEFAULT 0 COMMENT 'File size in KB'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- bans
CREATE TABLE IF NOT EXISTS `bans` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'Ban ID',
  `reason` tinytext DEFAULT NULL COMMENT 'Reason for ban',
  `length` int(11) DEFAULT NULL COMMENT 'Length of ban in minutes',
  `user` tinytext DEFAULT NULL COMMENT 'Username of banned person',
  `ip` text DEFAULT NULL,
  `date` int(11) DEFAULT NULL,
  `post` text DEFAULT NULL,
  `board` tinytext DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COMMENT='Banned users and IPs ';

-- boards
CREATE TABLE IF NOT EXISTS `boards` (
  `uri` varchar(8) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` varchar(250) NOT NULL,
  `owner` varchar(250) NOT NULL,
  `anonymous` tinytext NOT NULL,
  `message` tinytext DEFAULT NULL,
  `posts` int(11) DEFAULT NULL,
  `PPH` int(11) DEFAULT NULL,
  `users` int(11) DEFAULT NULL,
  `captcha` tinyint(1) NOT NULL DEFAULT 0,
  `perPage` int(11) NOT NULL,
  `bumpLock` int(11) DEFAULT NULL,
  `maxFiles` int(11) DEFAULT NULL,
  `maxFileSize` int(11) DEFAULT NULL,
  `mimeTypes` text DEFAULT NULL,
  `subjectLimit` int(11) DEFAULT NULL,
  `nameLimit` int(11) DEFAULT NULL,
  `characterLimit` int(11) DEFAULT NULL,
  `postID` int(11) NOT NULL DEFAULT 0,
  `forceAnonymity` int(11) NOT NULL DEFAULT 0,
  `r9k` int(11) NOT NULL DEFAULT 0,
  `pages` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='The list of boards. ';

-- groups
CREATE TABLE IF NOT EXISTS `groups` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- hashbans
CREATE TABLE IF NOT EXISTS `hashbans` (
  `hash` text NOT NULL COMMENT 'MD5 Hash of file',
  `reason` text DEFAULT NULL,
  `user` text NOT NULL COMMENT 'Banned by',
  `date` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- logs
CREATE TABLE IF NOT EXISTS `logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'Action ID',
  `type` tinytext NOT NULL,
  `action` text NOT NULL COMMENT 'Action description',
  `actionData` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'JSON of the logged action data',
  `user` text DEFAULT NULL,
  `ip` tinytext DEFAULT NULL COMMENT 'User IP. Can be null if connecting through TOR',
  `board` tinytext DEFAULT NULL COMMENT 'Used if action was related to a board',
  `date` int(11) NOT NULL COMMENT 'Unix timestamp',
  PRIMARY KEY (`id`),
  CONSTRAINT `logs_chk_1` CHECK (json_valid(`actionData`))
) ENGINE=InnoDB AUTO_INCREMENT=418 DEFAULT CHARSET=utf8mb4 COMMENT='Logs for user actions. ';

-- Posts
CREATE TABLE IF NOT EXISTS `posts` (
  `name` tinytext DEFAULT NULL COMMENT 'Post name',
  `subject` tinytext DEFAULT NULL COMMENT 'Post subject',
  `options` tinytext DEFAULT NULL COMMENT 'Post options',
  `message` text DEFAULT NULL COMMENT 'Post message content',
  `number` int(11) NOT NULL COMMENT 'Post number',
  `date` int(11) NOT NULL COMMENT 'Unix Timestamp',
  `type` int(11) NOT NULL COMMENT '1 for thread, 2 for reply',
  `thread` int(11) DEFAULT NULL COMMENT 'Thread tied to a reply',
  `board` tinytext NOT NULL COMMENT 'Board that the post was made on',
  `files` text DEFAULT NULL COMMENT 'File paths',
  `filenames` text DEFAULT NULL COMMENT 'Names of files tied to post',
  `ip` tinytext DEFAULT NULL COMMENT 'User IP',
  `spoiler` int(11) NOT NULL DEFAULT 0 COMMENT '0 for normal, 1 for spoiler',
  `password` text NOT NULL COMMENT 'Password for post deletion',
  `trip` text DEFAULT NULL COMMENT 'Tripcode or role signature',
  `replies` text DEFAULT NULL COMMENT 'Replies for posts',
  `append` text DEFAULT NULL COMMENT 'Message to be apended to the post',
  `locked` int(11) NOT NULL DEFAULT 0,
  `id` tinytext DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Reports
CREATE TABLE IF NOT EXISTS `reports` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'Report ID',
  `reporterIP` tinytext DEFAULT NULL COMMENT 'IP of reporter',
  `board` tinytext NOT NULL COMMENT 'Board of reported post',
  `number` int(11) NOT NULL COMMENT 'Number of reported post',
  `reason` text DEFAULT NULL COMMENT 'Reason for report',
  `date` int(11) DEFAULT NULL COMMENT 'Date of report',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Rules
CREATE TABLE IF NOT EXISTS `rules` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content` text NOT NULL COMMENT 'Rule content',
  `type` int(11) NOT NULL COMMENT '0 for global 1 for board',
  `board` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4;

-- Server
CREATE TABLE IF NOT EXISTS `server` (
  `posts` int(11) NOT NULL DEFAULT 0,
  `salt` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- Populate with default data
INSERT INTO `server` (posts, salt) VALUES (0, SUBSTRING(MD5(RAND()) FROM 1 FOR 50));
INSERT INTO `groups` (id, name) VALUES (0, 'root');
INSERT INTO `groups` (id, name) VALUES (1, 'administrator');
INSERT INTO `groups` (id, name) VALUES (2, 'moderator');
INSERT INTO `groups` (id, name) VALUES (3, 'janitor');
INSERT INTO `groups` (id, name) VALUES (4, 'user');