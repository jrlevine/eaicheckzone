--
-- Table structure for table eaimail
--

-- Copyright 2019-2020 Standcore LLC
--
-- Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
--
-- 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
--
-- 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

-- THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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

