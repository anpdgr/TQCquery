from flask import Flask, render_template, redirect, url_for, flash, session,request
import cx_Oracle
import pandas as pd
from business_duration import businessDuration
import holidays as pyholidays
from datetime import time, date, datetime
import math
import TQC_report_v5

app = Flask(__name__)
app.secret_key = "super secret key"


dsn_string = """(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.19.195.170)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=TQCPRD)))"""
try:
    connect = cx_Oracle.connect(user="QAQCAPPO", password="QAQCAPPO#123", dsn=dsn_string, encoding="UTF-8")
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
RELEASE_START as Start_Date,
RELEASE_End as End_Date,
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

#completed
DurSLA = TQC_report_v5.tqcCalculate(sql,connect)
defect_new_list = DurSLA[0]
defect_fixed_new_list = DurSLA[1]
defect_fixed_assigned_list = DurSLA[2]
defect_test_list = DurSLA[3]
defect_age_list = DurSLA[4]
meet_sla_list = DurSLA[5]
dfExport = DurSLA[6]

#completed
@app.route("/")
def mainTable():
    cur = connect.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    connect.commit()
    return render_template('tqcPage.html', datas=rows, new_durations=defect_new_list,fixed_new=defect_fixed_new_list,fixed_assigned=defect_fixed_assigned_list,test=defect_test_list,age=defect_age_list,meetsla=meet_sla_list)

#completed
@app.route("/exportall")
def export():
    filename = "TQC_query_results_"+str(datetime.now().strftime("%Y-%m-%d %H%M%S"))+".csv"
    dfExport.to_csv(filename,index=False,header=True,encoding='utf-8-sig')
    flash("Exported as "+filename)
    return redirect(url_for('mainTable'))

#completed
@app.route("/filter",methods=["POST","GET"])
def filteredTable():
    pjName = sDate = eDate = checkTab = ''
    cur = connect.cursor()
    if request.method=="POST":
        pjName = request.form['pjName']
        sDate = request.form['start']
        eDate = request.form['end']
        if pjName:
            sDate = eDate = ''
            pjSQL = sql+ " and project_name ='"+pjName+"'"
            pjList = TQC_report_v5.tqcCalculate(pjSQL,connect)
            defect_new_list = pjList[0]
            defect_fixed_new_list = pjList[1]
            defect_fixed_assigned_list = pjList[2]
            defect_test_list = pjList[3]
            defect_age_list = pjList[4]
            meet_sla_list = pjList[5]
            cur.execute(pjSQL)
            #search similar
            #            pjNameLike = '%'+pjName+'%'
            #            cur.execute(sql+ " and project_name LIKE :0",(pjNameLike,))
            checkTab = 'pj'
        elif sDate and eDate:
            pjName =''
            sToDate = "TO_DATE('"+sDate+"','yyyy-mm-dd')"
            eToDate = "TO_DATE('"+eDate+"','yyyy-mm-dd')"
            dateSQL = sql+" and ( (Start_Date BETWEEN "+sToDate+" AND "+eToDate+" ) OR (End_Date BETWEEN "+sToDate+" AND "+eToDate+" ) )"
            dateList = TQC_report_v5.tqcCalculate(dateSQL,connect)
            defect_new_list = dateList[0]
            defect_fixed_new_list = dateList[1]
            defect_fixed_assigned_list = dateList[2]
            defect_test_list = dateList[3]
            defect_age_list = dateList[4]
            meet_sla_list = dateList[5]
            cur.execute(dateSQL)
            checkTab = 'date'
    rows = cur.fetchall()
    connect.commit()
    return render_template('tqcPage.html', datas=rows, new_durations=defect_new_list,fixed_new=defect_fixed_new_list,fixed_assigned=defect_fixed_assigned_list,test=defect_test_list,age=defect_age_list,meetsla=meet_sla_list,pjName=pjName,sDate=sDate,eDate=eDate,checkTab=checkTab)


@app.route("/exportsome/<string:pjName>",methods=["GET"])
def exportsomePj(pjName):
    filename = "TQC_query_results_"+str(datetime.now().strftime("%Y-%m-%d %H%M%S"))+".csv"
    #pjName = sDate = eDate = ''
        #pjName = request.form['pjName']
    #sDate = request.form['start']
    #eDate = request.form['end']
    if pjName:
        pjSQL = sql+ " and project_name ='"+pjName+"'"
        pjList = TQC_report_v5.tqcCalculate(pjSQL,connect)
        pjExport = pjList[6]
        pjExport.to_csv(filename,index=False,header=True,encoding='utf-8-sig')
    else:
        DurSLA = TQC_report_v5.tqcCalculate(sql,connect)
        dfExport = DurSLA[6]
        dfExport.to_csv(filename,index=False,header=True,encoding='utf-8-sig')
    flash("Exported as "+filename+pjName)
    return redirect(url_for('mainTable'))

@app.route("/exportsome/<string:sDate>/<string:eDate>",methods=["GET"])
def exportsomeDate(sDate,eDate):
    filename = "TQC_query_results_"+str(datetime.now().strftime("%Y-%m-%d %H%M%S"))+".csv"
    #sDate = request.form['start']
    #eDate = request.form['end']
    if sDate and eDate:
        sToDate = "TO_DATE('"+sDate+"','yyyy-mm-dd')"
        eToDate = "TO_DATE('"+eDate+"','yyyy-mm-dd')"
        dateSQL = sql+" and ( (Start_Date BETWEEN "+sToDate+" AND "+eToDate+" ) OR (End_Date BETWEEN "+sToDate+" AND "+eToDate+" ) )"
        dateList = TQC_report_v5.tqcCalculate(dateSQL,connect)
        dateExport = dateList[6]
        dateExport.to_csv(filename,index=False,header=True,encoding='utf-8-sig')
    else:
        DurSLA = TQC_report_v5.tqcCalculate(sql,connect)
        dfExport = DurSLA[6]
        dfExport.to_csv(filename,index=False,header=True,encoding='utf-8-sig')
    flash("Exported as "+filename)
    return redirect(url_for('mainTable'))


if __name__ == "__main__":
    app.run(debug=True)
