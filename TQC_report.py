""" Query from TQC and calcuate days

ใช้สำหรับดึงข้อมูล defect ออกมาจาก TQC และคำนวณระยะเวลาในแต่ละช่วง

Prerequistic:
    * required python version: 3.x
    * pip install holidays
    * pip install business-duration
    * pip install pandas
    * pip install cx-Oracle

Settings:
    * เวลาเข้างาน เช่น เวลาเริ่มคือ 10 โมง คือ biz_open_time=time(10,0,0) 
    * เวลาเลิกกงาน เช่น เวลาเลิกกงานคือ 6 โมงเย็น => biz_open_time="time(18,0,0)
    * หน่วยระยะเวลา เช่น หน่วยเป็นชัั่วโมง => unit_hour='hour' , หน่วยเป็นวัน -> unit_hour='day'
    * ใส่รายการวันหยุดใน Thai_holiday_list

How to run:
    * > python TQC_report.py

Results:
    * ผลจากการรัน script จะได้ไฟล์ csv ที่ชื่อว่า TQC_Query_results_<datetime>.csv

็็Version: 0.1 - initial version
         0.5 - update sql and add calculation
Auther: Kittisak Srijankul (kittisak_sri@truecorp.co.th)
"""

import cx_Oracle
import pandas as pd
from business_duration import businessDuration
import holidays as pyholidays
from datetime import time,date,datetime
import math


#Business open hour must be in standard python time format-Hour,Min,Sec
biz_open_time=time(10,0,0)

#Business close hour must be in standard python time format-Hour,Min,Sec
biz_close_time=time(18,0,0)

#Business duration can be 'day', 'hour', 'min', 'sec'
unit_hour='hour'

#Thailand public holidays
Thai_holiday_list = {
    date(2019,1,1):"วันปีใหม่",
    date(2019,2,5):"ตรุษจีน",
	date(2019,2,6):"ตรุษจีน",
	date(2019,2,19):"มาฆบูชา",
	date(2019,4,8):"ชดเชยวันจักรี",
	date(2019,4,15):"สงกรานต์",
	date(2019,4,16):"สงกรานต์",
	date(2019,5,1):"แรงงาน",
	date(2019,5,6):"วันพระราชพิธีบรมราชาภิเษก",
	date(2019,5,20):"ชดเชยวันวิสาขบูชา",
	date(2019,6,3):"วันราชินี",
	date(2019,7,16):"ชดเชยอาสาฬหบูชา",
	date(2019,7,29):"ชดเชย ร10",
	date(2019,8,12):"วันแม่",
	date(2019,10,14):"ชดเชย ร9",
	date(2019,10,23):"ร5 ปิยมหาราช",
	date(2019,12,5):"วันพ่อ",
	date(2019,12,10):"วันรัฐธรรมนูญ",
	date(2019,12,31):"สิ้นปี",
	date(2020,1,1):"วันปีใหม่",
	date(2020,1,27):"ตรุษจีน",
	date(2020,2,10):"ชดเชยมาฆบูชา",
	date(2020,4,6):"วันจักรี",
	date(2020,4,13):"สงกรานต์",
	date(2020,4,14):"สงกรานต์",
	date(2020,4,15):"สงกรานต์",
	date(2020,5,1):"แรงงาน",
	date(2020,5,4):"ฉัตรมงคล",
	date(2020,5,6):"วันวิสาขบูชา",
	date(2020,6,3):"วันราชินี",
	date(2020,7,6):"ชดเชยอาสาฬหบูชา",
	date(2020,7,28):"ร10",
	date(2020,8,12):"วันแม่",
	date(2020,10,13):"ร9",
	date(2020,10,23):"ร5 ปิยมหาราช",
	date(2020,12,7):"ชดเชยวันพ่อ",
	date(2020,12,31):"สิ้นปี"
}

# 0. database connection

dsn_string = """(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.19.195.170)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=TQCPRD)))"""
try:
    connect = cx_Oracle.connect(user="QAQCAPPO", password="QAQCAPPO#123", dsn=dsn_string, encoding="UTF-8")
except:
    print("connect failed")


# 1. Query raw data from TQC
sql = """\
SELECT * FROM (
SELECT
project.project_name, 
test_release.test_release_name,
test_cycle.test_cycle_name, 
test_set.test_set_name,
project.status As Project_Status,
defect.defect_id as Defect_Id,
defect.defect_run_id As Defect_No, 
sub_defect.sub_run_id As Sub_Defect_No,
defect.defect_summary, 
ROW_NUMBER() OVER (PARTITION By defect.project_id,defect.defect_run_id,sub_defect.application_id Order by defect.detected_date DESC) row_num, 
defect_status.main_defect_status_name As main_defect_status,
defect_status.sub_defect_status_name As sub_defect_status,
defect_severity.severity_name, 
defect_priority.priority_name,
detect_user.firstname As DETECT_FIRSTNAME, 
detect_user.lastname As DETECT_LASTNAME, 
qa_lead_user.firstname As QA_LEAD_FIRSTNAME,
qa_lead_user.lastname AS QA_LEAD_LASTNAME, 
environment.environment_name,
defect_category.category_name, 
sub_defect.rca,
return_reason.reason_name, 
defect.additional_detail,
application.application_name,
manager_user.firstname Manager_firstname,
manager_user.lastname manager_lastname,
application.application_name Responsible_Application,
assigned_user.firstname assigned_to_firstname,
assigned_user.lastname assigned_to_lastname,
defect.detected_date,
defect_log.last_modified as New_Date,
defect_log_assigned.last_modified as Assigned_Date,
defect_log_renew.last_modified as ReNew_Date,
defect_log_fixed.last_modified as Fixed_Date,
defect_log_request.last_modified as Request_To_Deploy_Date,
defect_log_ready.last_modified as Ready_To_Test_Date,
defect_log_closed.last_modified as Closed_Date,
NULL as Defect_New_Duration,
NULL as Defect_Fixed_New_Duration,
NULL as Defect_Fixed_Assigned_Duration,
NULL as Defect_Test_Duration,
NULL as Defect_Age_Duration, 
(SELECT count(*) FROM defect_log WHERE defect_log.defect_id=sub_defect.defect_id AND defect_log.new_value='Re-Assigned') as ReOpen_Count,
(SELECT count(*) FROM defect_log WHERE defect_log.defect_id=sub_defect.defect_id AND defect_log.new_value='Returned') as Returned_Count
FROM defect 
JOIN sub_defect ON (defect.defect_id = sub_defect.defect_id)
JOIN project ON (project.project_id = defect.project_id)
JOIN defect_status ON (sub_defect.sub_defect_status_id = defect_status.defect_status_id)
LEFT OUTER JOIN user_ detect_user ON (defect.detected_by = detect_user.user_id)
LEFT OUTER JOIN user_ qa_lead_user ON (qa_lead_user.user_id = project.qa_lead)
LEFT OUTER JOIN defect_severity ON (defect_severity.severity_id = defect.defect_severity_id)
LEFT OUTER JOIN defect_priority ON (defect_priority.priority_id = defect.defect_priority_id) 
LEFT OUTER JOIN defect_category ON (defect_category.category_id = sub_defect.defect_category_id)
LEFT OUTER JOIN return_reason ON (return_reason.reason_id = sub_defect.return_reason_id)
LEFT OUTER JOIN environment ON (environment.environment_id = defect.environment_id)
JOIN application ON (sub_defect.application_id = application.application_id)
LEFT OUTER JOIN user_ manager_user ON (project.qa_manager = manager_user.user_id)
JOIN test_release ON (test_release.test_release_id = defect.test_release_id)
JOIN test_cycle ON (test_cycle.test_cycle_id = defect.test_cycle_id)
JOIN test_set ON (test_set.test_set_id = defect.test_set_id)
JOIN defect_application ON (defect.defect_id = defect_application.defect_id)
JOIN application defect_app ON (defect_application.application_id = defect_app.application_id)
LEFT OUTER JOIN defect_log on defect_log.defect_id = defect.defect_id and defect_log.new_value='New'
LEFT OUTER JOIN defect_log defect_log_fixed ON (defect_log_fixed.defect_id = defect.defect_id) and (defect_log_fixed.sub_id = sub_defect.sub_run_id)  AND (defect_log_fixed.new_value = 'Fixed') 
LEFT OUTER JOIN defect_log defect_log_renew ON (defect_log_renew.defect_id = defect.defect_id) and (defect_log_renew.sub_id = sub_defect.sub_run_id) AND (defect_log_renew.new_value = 'Re-New') AND (defect_log_renew.old_value = 'Returned')
LEFT OUTER JOIN user_ assigned_user ON ( assigned_user.user_id = defect_log_fixed.user_id)
LEFT OUTER JOIN defect_log defect_log_assigned ON (defect_log_assigned.defect_id = defect.defect_id) and (defect_log_assigned.sub_id = sub_defect.sub_run_id) AND (defect_log_assigned.new_value = 'Assigned')
LEFT OUTER JOIN defect_log defect_log_request ON (defect_log_request.defect_id = defect.defect_id) and (defect_log_request.sub_id = sub_defect.sub_run_id) AND (defect_log_request.new_value = 'Request to Deploy')
LEFT OUTER JOIN defect_log defect_log_ready ON (defect_log_ready.defect_id = defect.defect_id) and (defect_log_ready.sub_id = sub_defect.sub_run_id) AND (defect_log_ready.new_value = 'Ready to Test')
LEFT OUTER JOIN defect_log defect_log_closed ON (defect_log_closed.defect_id = defect.defect_id) and (defect_log_closed.sub_id = sub_defect.sub_run_id) AND (defect_log_closed.new_value = 'Closed')
order by project.project_id, defect.defect_run_id , sub_defect.SUB_RUN_ID
) 
where  row_num=1 
"""

SQL_Query = pd.read_sql_query(sql,connect)
df = pd.DataFrame(SQL_Query)
# print(df)

# defect_log
sql_defect_log = pd.read_sql_query("""select Defect_ID,SUB_ID,New_Value,LAST_MODIFIED from defect_log where field_id=10017""",connect)
df_log = pd.DataFrame(sql_defect_log)

defect_new_list = []   
defect_fixed_new_list = []
defect_fixed_assigned_list = []
defect_test_list = []
defect_age_list = []
meet_sla_list = []
#defect_reassigned_list = [None]*10
defect_reassigned_list1 = []
defect_reassigned_list2 = []
defect_reassigned_list3 = []
defect_reassigned_list4 = []
defect_reassigned_list5 = []
defect_reassigned_list6 = []
defect_reassigned_list7 = []
defect_reassigned_list8 = []
defect_reassigned_list9 = []
defect_reassigned_list10 = []

# main loop
for index, row in df.iterrows():
    current_defect_id = row['DEFECT_ID']
    current_sub_defect_no = row['SUB_DEFECT_NO']
    current_main_defect_status = row['MAIN_DEFECT_STATUS']
    current_severity_name = row['SEVERITY_NAME']
    current_priority_name = row['PRIORITY_NAME']
    current_project_name = row['PROJECT_NAME']
    # current_defect_id = 2778
    # current_sub_defect_no = 1
    # print(current_defect_id) 
    # print(current_sub_defect_no)


    df_log_temp = df_log.query('DEFECT_ID == ' + str(current_defect_id) + ' and (SUB_ID == '  + str(current_sub_defect_no) + ' or SUB_ID == "NaN")' ).sort_values(by='LAST_MODIFIED')
    #df_log_temp = df_log.query('DEFECT_ID == ' + str(current_defect_id) ).sort_values(by='LAST_MODIFIED')
    #print(df_log_temp)
    

    new_date = assigned_date = ready_to_test_date = closed_date = ""
    reassigned_flag = False
    reassigned_date_list = []
    ready_to_test_date_list = []

    for index, row in df_log_temp.iterrows():
        if row['NEW_VALUE'] == 'New':
            new_date = pd.to_datetime(row['LAST_MODIFIED'],dayfirst=True)
        if row['NEW_VALUE'] == 'Assigned':
            assigned_date = pd.to_datetime(row['LAST_MODIFIED'],dayfirst=True)
        if row['NEW_VALUE'] == 'Request to Deploy':      # ของเดิมคิดที่ Ready to Test
            ready_to_test_date = pd.to_datetime(row['LAST_MODIFIED'],dayfirst=True)
            if (reassigned_flag):
                ready_to_test_date_list.append(ready_to_test_date)
        if row['NEW_VALUE'] == 'Re-Assigned':
            reassigned_date = pd.to_datetime(row['LAST_MODIFIED'],dayfirst=True)
            reassigned_date_list.append(reassigned_date)
            reassigned_flag = True
        if row['NEW_VALUE'] == 'Closed':
            closed_date = pd.to_datetime(row['LAST_MODIFIED'],dayfirst=True)
        if row['NEW_VALUE'] == 'Re-New': # ถ้ามีการ renew ให้วันที่เริ่มต้นเจอ defect ป็น renew date แทน`
            new_date = pd.to_datetime(row['LAST_MODIFIED'],dayfirst=True) 

    # if no closed_date, then it's now.
    if closed_date == '':
        closed_date = datetime.now()

    # calculate new duration



    defect_new_duration = 0
    if new_date != '' and assigned_date != '':
        if current_project_name.startswith('CPC'):
            defect_new_duration = businessDuration(startdate=new_date,enddate=assigned_date,weekendlist=[],unit=unit_hour)
        else:
            defect_new_duration = businessDuration(startdate=new_date,enddate=assigned_date,starttime=biz_open_time,endtime=biz_close_time,holidaylist=Thai_holiday_list,unit=unit_hour)
        
        #print("defect_new_duration: {}".format(defect_new_duration))
        if math.isnan(defect_new_duration):
            defect_new_duration = 0
            # print("defect_new_duration_issue")
            # print("new_date: {}".format(new_date))
            # print("assigned_date: {}\n".format(assigned_date))
    defect_new_list.append(defect_new_duration)

    # calculate fixed days ( detected_date -> ready_to_test_date )
    defect_fixed_new_duration = 0
    # ในกรณีที่ยังมีวัน ready to test  ให้เอาวันที่ปัจจุบันแทน
    if ready_to_test_date == '':
        ready_to_test_date = datetime.now()
    if new_date != '' and ready_to_test_date != '':
        if current_project_name.startswith('CPC'):
            defect_fixed_new_duration = businessDuration(startdate=new_date,enddate=ready_to_test_date,weekendlist=[],unit=unit_hour)
        else:
            defect_fixed_new_duration = businessDuration(startdate=new_date,enddate=ready_to_test_date,starttime=biz_open_time,endtime=biz_close_time,holidaylist=Thai_holiday_list,unit=unit_hour)
        if math.isnan(defect_fixed_new_duration):
            defect_fixed_new_duration = 0

    defect_fixed_new_list.append(defect_fixed_new_duration)

    # calculate test days ( ready_to_test_date -> closed_date )
    defect_test_duration = 0

    if ready_to_test_date != '' and closed_date != '':
        
        if current_project_name.startswith('CPC'):
            defect_test_duration = businessDuration(startdate=ready_to_test_date,enddate=closed_date,weekendlist=[],unit=unit_hour)
        else:
            defect_test_duration = businessDuration(startdate=ready_to_test_date,enddate=closed_date,starttime=biz_open_time,endtime=biz_close_time,holidaylist=Thai_holiday_list,unit=unit_hour)
        
        if math.isnan(defect_test_duration):
            defect_test_duration = 0
    defect_test_list.append(defect_test_duration)

    # calculate age days ( detected_date -> closed_date)
    defect_age_duration = 0
    if new_date != '' and closed_date != '':
        if current_project_name.startswith('CPC'):
            defect_age_duration =  businessDuration(startdate=new_date,enddate=closed_date,weekendlist=[],unit=unit_hour)
        else:
            defect_age_duration =  businessDuration(startdate=new_date,enddate=closed_date,starttime=biz_open_time,endtime=biz_close_time,holidaylist=Thai_holiday_list,unit=unit_hour)
        if math.isnan(defect_age_duration):
            defect_age_duration = 0
    defect_age_list.append(defect_age_duration)

    # ( assigned_date -> ready_to_test_date ) 
    defect_fixed_assigned_duration = 0
    if assigned_date != '' and ready_to_test_date != '':
        if current_project_name.startswith('CPC'):
            defect_fixed_assigned_duration = businessDuration(startdate=assigned_date,enddate=ready_to_test_date,weekendlist=[],unit=unit_hour)
        else:
            defect_fixed_assigned_duration = businessDuration(startdate=assigned_date,enddate=ready_to_test_date,starttime=biz_open_time,endtime=biz_close_time,holidaylist=Thai_holiday_list,unit=unit_hour)
        
        if math.isnan(defect_fixed_assigned_duration):
            defect_fixed_assigned_duration = 0
    defect_fixed_assigned_list.append(defect_fixed_assigned_duration)

    # calculate SLA
    sla_status = ''
    if (current_severity_name == None):
        current_severity_name = current_priority_name

    # Default SLA
    if (current_severity_name == 'Low' or current_severity_name == None ):
        sla_status = 'Low'
    elif (current_main_defect_status == 'Cancelled'):
        sla_status = 'Cancelled'
    elif (current_severity_name == 'Critical' and defect_fixed_new_duration > 4):
        sla_status = 'N'
    elif (current_severity_name == 'High' and defect_fixed_new_duration > 8):
        sla_status = 'N'
    elif (current_severity_name == 'Medium' and defect_fixed_new_duration > 16):
        sla_status = 'N'
    else:
        #print("severity: {}".format(current_severity_name)) 
        sla_status = 'Y'

    meet_sla_list.append(sla_status)
    # if (defect_age_duration > 0 and defect_age_duration <= 4):
    #     meet_sla_list.append("Y")
    # else:
    #     meet_sla_list.append("N")


    # calculate loop for reassigned_date to ready_to_test_date
    reassign_duration_list=[None]*10
    for i in range(len(reassigned_date_list)):
        a = reassigned_date_list[i]
        try:
            b = ready_to_test_date_list[i]
        except IndexError:
            # print('sorry, not yet ready to test')
            b = a
        
        reassign_duration = businessDuration(startdate=a,enddate=b,starttime=biz_open_time,endtime=biz_close_time,holidaylist=Thai_holiday_list,unit=unit_hour)    
        reassign_duration_list[i] = reassign_duration
    
    defect_reassigned_list1.append(reassign_duration_list[0])
    defect_reassigned_list2.append(reassign_duration_list[1])
    defect_reassigned_list3.append(reassign_duration_list[2])
    defect_reassigned_list4.append(reassign_duration_list[3])
    defect_reassigned_list5.append(reassign_duration_list[4])
    defect_reassigned_list6.append(reassign_duration_list[5])
    defect_reassigned_list7.append(reassign_duration_list[6])
    defect_reassigned_list8.append(reassign_duration_list[7])
    defect_reassigned_list9.append(reassign_duration_list[8])
    defect_reassigned_list10.append(reassign_duration_list[9])

# print(defect_new_list)

df['DEFECT_NEW_DURATION'] =  defect_new_list
df['DEFECT_FIXED_NEW_DURATION'] = defect_fixed_new_list
df['DEFECT_FIXED_ASSIGNED_DURATION'] = defect_fixed_assigned_list
df['DEFECT_TEST_DURATION'] = defect_test_list
df['DEFECT_AGE_DURATION'] = defect_age_list
df['MEET_SLA'] = meet_sla_list
df['DFECCT_REASSIGNED1_DURATION'] = defect_reassigned_list1
df['DFECCT_REASSIGNED2_DURATION'] = defect_reassigned_list2
df['DFECCT_REASSIGNED3_DURATION'] = defect_reassigned_list3
df['DFECCT_REASSIGNED4_DURATION'] = defect_reassigned_list4
df['DFECCT_REASSIGNED5_DURATION'] = defect_reassigned_list5
df['DFECCT_REASSIGNED6_DURATION'] = defect_reassigned_list6
df['DFECCT_REASSIGNED7_DURATION'] = defect_reassigned_list7
df['DFECCT_REASSIGNED8_DURATION'] = defect_reassigned_list8
df['DFECCT_REASSIGNED9_DURATION'] = defect_reassigned_list9
df['DFECCT_REASSIGNED10_DURATION'] = defect_reassigned_list10


#  3. Save to file
df.to_csv("TQC_query_results_"+str(datetime.now().strftime("%Y-%m-%d %H%M%S"))+".csv",index=False,header=True,encoding='utf-8-sig')





def calculate_sla(project_group,severity_name,priority_name,defect_status,defect_fixed_new_duration):
    sla_status = ''
    critical_point = 4      # default value of critical point
    high_point = 8          # default value of high point
    medium_point = 16       # default value of medium point

    # specific value for CPC project group
    if (project_group == 'CPC'):   
        critical_point = 24
        high_point = 48
        medium_point = 120

    if (severity_name == None):
        severity_name = priority_name

    if (severity_name == 'Low' or severity_name == None ):
        sla_status = 'Low'
    elif (defect_status == 'Cancelled'):
        sla_status = 'Cancelled'
    elif (severity_name == 'Critical' and defect_fixed_new_duration > critical_point):
        sla_status = 'N'
    elif (severity_name == 'High' and defect_fixed_new_duration > high_point):
        sla_status = 'N'
    elif (severity_name == 'Medium' and defect_fixed_new_duration > medium_point):
        sla_status = 'N'
    else:
        #print("severity: {}".format(severity_name)) 
        sla_status = 'Y'
    return sla_status