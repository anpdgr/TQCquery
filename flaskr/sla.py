def calculate_sla(severity_name,priority_name,defect_status,defect_fixed_new_duration,project_group=""):
    """calculate the SLA and check whether it meet SLA criteria or not

    Parameters
    ----------
    project_group : str
        The specific project group (default is blank).
    severity_name : str
        The severity name (Critical,High,Medium).
    priority_name : str
        The priority name will be used if the severity name is none.
    defect_status : str
        The defect status (Open,Fixed,Closed,Cancelled)
    defect_fixed_new_duration : int
        The defect duration from new status to fixed status

    Returns
    -------
    str
        Status: Y or N

    """
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

    if (defect_status == 'Cancelled'):
        sla_status = 'Cancelled'
    elif (severity_name == 'Low' or severity_name == None ):
        sla_status = 'Low'
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