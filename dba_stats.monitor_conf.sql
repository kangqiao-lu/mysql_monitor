create database dba_stats;
use dba_stats;
Create Table: CREATE TABLE `monitor_conf` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID自动增长',
  `class` char(20) NOT NULL,
  `is_master` int(11) NOT NULL DEFAULT '0' COMMENT '0 is Slave,1 is Master,2 is Vmaster,3 is Vslave,4 is realku,5 is Mslave',
  `host` char(255) NOT NULL DEFAULT '',
  `realserver` varchar(50) NOT NULL DEFAULT 'vipserver' COMMENT 'mysql实例所在的宿主机,以hostname为准',
  `port` int(11) NOT NULL DEFAULT '3306',
  `usefor` varchar(255) NOT NULL DEFAULT '' COMMENT '用途',
  `day_lag` int(11) NOT NULL COMMENT '白天延迟报警值',
  `night_lag` int(11) NOT NULL COMMENT '夜晚延迟报警值',
  `is_mon` int(11) NOT NULL DEFAULT '0' COMMENT '是否监控：1监控 0不监控',
  `mon_one` int(11) NOT NULL DEFAULT '0' COMMENT '1分钟监控：1监控 0不监控',
  `mon_ten` int(11) NOT NULL DEFAULT '0' COMMENT '10分钟监控：1监控 0不监控',
  `idc` varchar(30) DEFAULT '' COMMENT '机房',
  `one_starttime` datetime NOT NULL COMMENT '开启1分钟监控时间',
  `ten_starttime` datetime NOT NULL COMMENT '开启10分钟监控时间',
  `is_avail` int(11) NOT NULL DEFAULT '1' COMMENT '机器是否下线：0下线，1在用',
  `com` varchar(512) NOT NULL DEFAULT 'comment',
  `modified_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_host_port` (`host`,`port`),
  KEY `idx_class` (`class`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
