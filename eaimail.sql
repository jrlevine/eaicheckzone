--
-- Table structure for table eaimail
--

CREATE DATABASE eaimail;

GRANT ALL ON eaimail.* TO eaimail IDENTIFIED BY 'x';

USE eaimail

DROP TABLE IF EXISTS eaimail;
CREATE TABLE eaimail (
  tld varchar(65) NOT NULL DEFAULT '',
  ndomain int(10) unsigned NOT NULL,
  mx varchar(255) DEFAULT NULL,
  mxip int(10) unsigned NOT NULL DEFAULT '0',
  neai tinyint(1) NOT NULL,
  n8bit tinyint(1) NOT NULL,
  mtasw varchar(20) DEFAULT NULL,
  scandate date DEFAULT NULL,
  PRIMARY KEY (tld,mxip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table eaitld
--

DROP TABLE IF EXISTS eaitld;
CREATE TABLE eaitld (
  tld varchar(65) NOT NULL,
  ndom int(10) unsigned DEFAULT NULL,
  nmx int(10) unsigned DEFAULT NULL,
  nname int(10) unsigned DEFAULT NULL,
  nwhen datetime DEFAULT CURRENT_TIMESTAMP,
  ntld tinyint(1) DEFAULT NULL,
  PRIMARY KEY (tld)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

