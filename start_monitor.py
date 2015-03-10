#!/usr/bin/python
#coding=utf-8
import MySQLHandler,SendMsgHandler,MonItems,os,sys,time,string,threading
log_db = MySQLHandler.MySQLHandler('dba-log-ku',3306)
send_msg = SendMsgHandler.SendMsg()

if __name__ == '__main__':
    get_mon_data_sql = 'select id,host,port,is_master,class,is_mon,usefor from dba_stats.monitor_conf;'
    all_data = log_db.get_mysql_data(get_mon_data_sql)
    #all_data=(('1','g1-off-ku-real02',3840,4,'offku',1),)
    threads = []
    if all_data != 0:
        for data in all_data:
            mysql_id = data[0]
            mysql_host = data[1]
            mysql_port = data[2]
            mysql_role = data[3]
            mysql_class = data[4]
            is_mon = data[5]
            usefor = data[6]
            #mysql_id,mysql_host,mysql_port,mysql_role,mysql_class,is_mon,usefor = data
            ##每一个实例启动一个监控线程
            mysql_mon = MonItems.MySQLItems(mysql_host,mysql_port,mysql_class,mysql_role,is_mon,usefor)
            th_name = '%s_%s_%s' % (mysql_host,mysql_port,mysql_class)
            th = threading.Thread(target=mysql_mon.start_mon,name=th_name)
            threads.append(th)
            th.start()

        ##等待30s,然后判断监控线程是否还存活,如果还存活着,则报警假死后强制退出
        time.sleep(30)
        for ths in threads:
            is_alive = ths.isAlive()
            ths_name = ths.getName()
            host = string.split(ths_name,'_')[0]
            port = string.split(ths_name,'_')[1]
            Class = string.split(ths_name,'_')[2]
            if is_alive is True:
                now_time = time.strftime('%Y-%m-%d %X', time.localtime())
                now_msg = '%s %s:%s MySQL has been dead %s @new_mon' % (Class,host,port,now_time)
                send_msg.send_sms_class(Class,now_msg)
            else:
                continue
        os._exit(1)
