#!/usr/bin/python
#coding=utf-8
import MySQLdb
import time
import sys
import datetime
import os
import string
import MySQLHandler
import SendMsgHandler
import exceptions

'''定义自己异常'''
class MyException(Exception):
    def __init__(self):
        Exception.__init__(self)

class MySQLItems(object):
    sendmsg = SendMsgHandler.SendMsg()
    def __init__(self,host,port,mysql_class,role_id,is_mon,usefor):
        self.host = host
        self.port = port
        self.mysql_class = mysql_class
        self.is_mon = is_mon
        self.usefor = usefor
        
        self.user = 'dba_monitor'
        self.pw = 'XXXXXXX'
        self.dbhandler = MySQLHandler.MySQLHandler(self.host,self.port)
        self.logkuhandler = MySQLHandler.MySQLHandler('yz-log-ku-m00.dns.ganji.com',3306)
        if role_id == 0:
            self.role = 'Slave'
        elif role_id == 1:
            self.role = 'Master'
        elif role_id == 2:
            self.role = 'Vmaster'
        elif role_id == 3:
            self.role = 'Vslave'
        elif role_id == 4:
            self.role = 'realku'
        elif role_id == 5:
            self.role = 'Mslave'

    def get_now_date(self):
        time_format = '%m-%d %H:%M'
        now_date = time.strftime(time_format, time.localtime())
        return now_date

    '''检查mysql是否能连接上'''
    def check_mysql_status(self):
        ret = self.dbhandler.get_mysql_data('select @@PORT;')
        if ret == 0:
            now_date = self.get_now_date()
            now_msg = "%s (%s) %s %s:%s Cannot Connect MySQL %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,now_date)
            self.sendmsg.send_sms_class(self.mysql_class,now_msg)
            raise MyException()
        else:
            return 1

	'''主从同步,跳过当前sql'''
    def set_skip_counter(self):
        sql = "set global sql_slave_skip_counter=1;"
        ret = self.dbhandler.execute_sql(sql)
        if ret == 0:
            now_date = self.get_now_date()
            now_msg = "%s (%s) %s %s:%s excute sql(set global sql_slave_skip_counter) failed %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,now_date)        
            self.sendmsg.send_sms_class(self.mysql_class,now_msg)            

	'''start slave'''
    def start_slave(self):
        sql = 'start slave;'
        ret = self.dbhandler.execute_sql(sql)
        if ret == 0:
            now_date = self.get_now_date()
            now_msg = "%s (%s) %s %s:%s excute sql faild while start slave %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,now_date) 
            self.sendmsg.send_sms_class(self.mysql_class,now_msg)

	'''stop slave'''
    def stop_slave(self):
        sql = 'stop slave;'
        ret = self.dbhandler.execute_sql(sql)
        if ret  == 0:
            now_date = self.get_now_date()
            now_msg = "%s (%s) %s %s:%s excute sql faild while stop slave %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,now_date)
            self.sendmsg.send_sms_class(self.mysql_class,now_msg)

	'''根据产品线获取连接数的阀值'''
    def get_connections_threshold(self):
        sql = "select thread_threshold from dba_stats.monitor_class where class='%s' limit 1" % self.mysql_class
        sql_data = self.logkuhandler.get_mysql_data(sql)        
        if sql_data == 0:
            now_date = self.get_now_date()
            now_msg = "log Vip-master yz-log-ku-m00:3306 Cannot Connect MySQL while get_connections_threshold %s @new_mon" % now_date
            self.sendmsg.send_sms_class('log',now_msg)
            return sql_data
        else:
            thread_ttl = sql_data[0][0]
            return thread_ttl

	'''检查连接数有没有超过指定阀值'''
    def check_mysql_connections(self):
        sql = "show global status like 'Threads_connected';"
        data = self.dbhandler.get_mysql_data(sql)
        if data == 0:
            now_date = self.get_now_date()
            now_msg = "%s (%s) %s %s:%s Cannot Connect MySQL %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,now_date)
            self.sendmsg.send_sms_class(self.mysql_class,now_msg)
        else:
            count = int(data[0][1])
            thread_ttl = self.get_connections_threshold()
            if thread_ttl != 0:
                if count >= thread_ttl:
                    now_date = self.get_now_date()
                    now_msg = "%s (%s) %s %s:%s now Threads %s %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,count,now_date)
                    self.sendmsg.send_sms_class(self.mysql_class,now_msg)

	'''获取当前时间的mysql主从延迟阀值'''
    def get_now_lag_ttl(self):
        hour = '%H'
        now_hour = int(time.strftime(hour, time.localtime()))
        if now_hour >= 6:
            lag_type = 'day_lag'
        else:
            lag_type = 'night_lag'
        sql = "select %s from dba_stats.monitor_conf where host='%s' and port=%s limit 1;" % (lag_type,self.host,self.port)
        sql_data = self.logkuhandler.get_mysql_data(sql)
        if sql_data == 0:
            now_date = self.get_now_date()
            now_msg = "log Vip-master yz-log-ku-m00:3306 Cannot Connect MySQL while get_now_lag_ttl %s @new_mon" % now_date
            self.sendmsg.send_sms_class('log',now_msg)
            return 0
        else:        
            now_lag_ttl = sql_data[0][0]
            return now_lag_ttl
    
	'''返回'show slave status'的数据'''
    def get_slave_data(self):
        sql = 'show slave status'
        all_data  = self.dbhandler.get_mysql_data(sql)
        if all_data == 0:
            now_date = self.get_now_date()
            now_msg = "%s (%s) %s %s:%s Cannot Connect MySQL %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,now_date)
            self.sendmsg.send_sms_class(self.mysql_class,now_msg)
            return 0
        else:
            return all_data[0]
    
	'''检查是否有主从同步错误,有就根据错误类型执行相关操作并报警,没有就返回延迟数值'''
    def check_slave_err(self):
        slave_data = self.get_slave_data()
        if slave_data != 0:
            errno = slave_data[36]
            if errno == 0:
                Slave_IO_Running = slave_data[10]
                Slave_SQL_Running = slave_data[11]
                if Slave_IO_Running == 'No' or Slave_SQL_Running == 'No':
                    now_date = self.get_now_date()
                    now_msg = "%s (%s) %s %s:%s Slave Error %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,now_date)
                    self.sendmsg.send_sms_class(self.mysql_class,now_msg)
                    raise MyException()
                else:
                    now_lag = slave_data[32]
                    return now_lag
            elif errno == 1062 or errno == 1317 or errno == 1053:
                err_msg = string.split(slave_data[37],'.')[0]
                self.set_skip_counter()
                self.stop_slave()
                self.start_slave()
                now_date = self.get_now_date()
                now_msg = "%s (%s) %s %s:%s !!!SKIP Slave; Err-msg:%s %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,err_msg,now_date)
                self.sendmsg.send_sms_class(self.mysql_class,now_msg)
                raise MyException()
            elif errno == 1213 or errno == 1114 or errno == 1205:
                err_msg = string.split(slave_data[37],'.')[0]
                self.stop_slave()
                self.start_slave()
                now_date = self.get_now_date()
                now_msg = "%s (%s) %s %s:%s !!!RESTART Slave Err-msg:%s %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,err_msg,now_date)
                self.sendmsg.send_sms_class(self.mysql_class,now_msg)
                raise MyException()
            else:
                err_msg = string.split(slave_data[37],'.')[0]
                now_date = self.get_now_date()
                now_msg = "%s (%s) %s %s:%s Slave Error Err-msg:%s %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,err_msg,now_date)
                self.sendmsg.send_sms_class(self.mysql_class,now_msg)
                raise MyException()
                

	'''检查主从延迟是否超过阀值'''
    def check_slave_lag(self):
        ret = self.check_slave_err()
        if ret is not None:
            now_lag = ret
            lag_ttl = self.get_now_lag_ttl()
            if lag_ttl != 0:
                if now_lag >= lag_ttl:
                    now_date = self.get_now_date()
                    now_msg = "%s (%s) %s %s:%s SecBehMaster %s %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,now_lag,now_date)
                    self.sendmsg.send_sms_class(self.mysql_class,now_msg)

	'''根据角色的不同,判断read_only状态是否正确'''
    def check_read_only(self):
        sql = 'select @@read_only;'
        sql_data = self.dbhandler.get_mysql_data(sql)
        if sql_data == 0:
            now_date = self.get_now_date()
            now_msg = "%s (%s) %s %s:%s Cannot Connect MySQL %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,now_date)
            self.sendmsg.send_sms_class(self.mysql_class,now_msg)       
        else:
            read_only = sql_data[0][0]
            if self.role == 'Slave' or self.role == 'Vslave':
                if read_only == 0:
                    now_date = self.get_now_date()
                    now_msg = "%s (%s) %s %s:%s read_only Must Be 1 %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,now_date)
                    self.sendmsg.send_sms_class(self.mysql_class,now_msg)
            elif self.role == 'Master' or self.role == 'Vmaster' or self.role == 'Mslave' or self.role == 'realku':
                if read_only == 1:
                    now_date = self.get_now_date()
                    now_msg = "%s (%s) %s %s:%s read_only Must Be 0 %s @new_mon" % (self.mysql_class,self.usefor,self.role,self.host,self.port,now_date)
                    self.sendmsg.send_sms_class(self.mysql_class,now_msg)
    
	'''检查关闭监控的主机端口是否到了开启监控的时间,到则打开,没到则跳过监控'''
    def open_monitor(self):
        get_sql = "select UNIX_TIMESTAMP(one_starttime) from dba_stats.monitor_conf where host='%s' and port=%s limit 1" % (self.host,self.port)
        update_sql = "update dba_stats.monitor_conf set is_mon=1 where host='%s' and port=%s limit 1" % (self.host,self.port)
        all_start_time = self.logkuhandler.get_mysql_data(get_sql)
        if all_start_time != 0:
            start_time = int(all_start_time[0][0])
            now_unixtime = int(time.time())
            if now_unixtime >= start_time:
                print update_sql
                ret = self.logkuhandler.execute_sql(update_sql)
                if ret == 0:
                    now_time = self.get_now_date()
                    now_msg = 'log Vmaster yz-log-ku-m00:3306 excute sql failed while open monitor %s @new_mon' % now_time
                    self.sendmsg.send_sms_class('log',now_msg)
        else:
            now_time = self.get_now_date()
            now_msg = 'log Vmaster yz-log-ku-m00:3306 Cannot Connect MySQL while get one_starttime %s @new_mon' % now_time
            self.sendmsg.send_sms_class('log',now_msg)


	'''根据角色的不同,分配不同的监控项'''
    def start_mon(self):
        if self.is_mon == 0:
            self.open_monitor()
        else:
            if self.role == 'Master':
                try:
                    self.check_mysql_status()
                    self.check_mysql_connections()
                    self.check_read_only()
                except MyException:
                    print "I have excepted the MyException"
            elif self.role == 'Vmaster':
                try:
                    self.check_mysql_status()
                    self.check_read_only()
                except MyException:
                    print "I have excepted the MyException"
            elif self.role == 'Slave' or self.role == 'realku':
                try:
                    self.check_mysql_status()
                    self.check_mysql_connections()
                    self.check_read_only()
                    self.check_slave_err()
                    self.check_slave_lag()
                except MyException:
                    print "I have excepted the MyException"
            elif self.role == 'Vslave':
                try:
                    self.check_mysql_status()
                except MyException:
                    print "I have excepted the MyException"
