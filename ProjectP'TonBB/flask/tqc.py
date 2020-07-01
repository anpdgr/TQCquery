from flask import Flask, render_template
import cx_Oracle
import pandas as pd
from business_duration import businessDuration
import holidays as pyholidays
from datetime import time, date, datetime
import math

app = Flask(__name__)

# Business open hour must be in standard python time format-Hour,Min,Sec
biz_open_time = time(10, 0, 0)

# Business close hour must be in standard python time format-Hour,Min,Sec
biz_close_time = time(18, 0, 0)

# Business duration can be 'day', 'hour', 'min', 'sec'
unit_hour = 'hour'

# Thailand public holidays
Thai_holiday_list = {
    date(2019, 1, 1): "วันปีใหม่",
    date(2019, 2, 5): "ตรุษจีน",
    date(2019, 2, 6): "ตรุษจีน",
    date(2019, 2, 19): "มาฆบูชา",
    date(2019, 4, 8): "ชดเชยวันจักรี",
    date(2019, 4, 15): "สงกรานต์",
    date(2019, 4, 16): "สงกรานต์",
    date(2019, 5, 1): "แรงงาน",
    date(2019, 5, 6): "วันพระราชพิธีบรมราชาภิเษก",
    date(2019, 5, 20): "ชดเชยวันวิสาขบูชา",
    date(2019, 6, 3): "วันราชินี",
    date(2019, 7, 16): "ชดเชยอาสาฬหบูชา",
    date(2019, 7, 29): "ชดเชย ร10",
    date(2019, 8, 12): "วันแม่",
    date(2019, 10, 14): "ชดเชย ร9",
    date(2019, 10, 23): "ร5 ปิยมหาราช",
    date(2019, 12, 5): "วันพ่อ",
    date(2019, 12, 10): "วันรัฐธรรมนูญ",
    date(2019, 12, 31): "สิ้นปี",
    date(2020, 1, 1): "วันปีใหม่",
    date(2020, 1, 27): "ตรุษจีน",
    date(2020, 2, 10): "ชดเชยมาฆบูชา",
    date(2020, 4, 6): "วันจักรี",
    date(2020, 4, 13): "สงกรานต์",
    date(2020, 4, 14): "สงกรานต์",
    date(2020, 4, 15): "สงกรานต์",
    date(2020, 5, 1): "แรงงาน",
    date(2020, 5, 4): "ฉัตรมงคล",
    date(2020, 5, 6): "วันวิสาขบูชา",
    date(2020, 6, 3): "วันราชินี",
    date(2020, 7, 6): "ชดเชยอาสาฬหบูชา",
    date(2020, 7, 28): "ร10",
    date(2020, 8, 12): "วันแม่",
    date(2020, 10, 13): "ร9",
    date(2020, 10, 23): "ร5 ปิยมหาราช",
    date(2020, 12, 7): "ชดเชยวันพ่อ",
    date(2020, 12, 31): "สิ้นปี"
}

dsn_string = """(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.19.195.170)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=TQCPRD)))"""
try:
    connect = cx_Oracle.connect(
        user="QAQCAPPO", password="QAQCAPPO#123", dsn=dsn_string, encoding="UTF-8")
except:
    print("connect failed")

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
where  row_num=1 and rownum <= 30
"""


@app.route("/")
def mainTable():
    cur = connect.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    connect.commit()

    return render_template('tqcPage.html', datas=rows)


if __name__ == "__main__":
    app.run(debug=True)
