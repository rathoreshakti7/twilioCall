#!/usr/bin/python
import time , json , sys , re , requests , os , random , string , consul , datetime
from slacker import Slacker
#sys.stdout = open('/tmp/twilio.log', 'a')
date = datetime.datetime.today().strftime('%Y/%m/%-d')
fname='/tmp/python.lock'
while os.path.isfile(fname):
    print "in sleep mode"
    time.sleep(5)
os.system("touch "+ fname)

file_name = "/opt/twilio/triggerout/alarm.out"
file = open(file_name, 'r')
input_data = file.read()

alert_dict = json.loads(input_data)
alert=re.findall(r'"([^"]*)"', alert_dict["Subject"])[0]
print "=======alert========  "+ alert
parameters=alert_dict["Subject"].split("_")
environment=str(parameters[1])
module=str(parameters[2])
metrics=str(parameters[4])

print "env: "+ environment + " module: " + module + " metrics: " + metrics

####Function to get data from consul KV store
consulServer=['']
def getKeyData(dataKey,keys):
  connection="true"
  length=len(consulServer)
  for i in range(length + 1):
     try :
        if (i == length):
          connection="fail"
          break
        consulHost = consulServer[i]
        c = consul.Consul(host=consulHost, port=8500,dc='jcm',cert=None,scheme='http')
        index = None
        index, data = c.kv.get(dataKey, index=index,keys=keys)
        return  data
        break
     except :
        print("An exception was triggered while getKeyData from consulServer  "+consulHost+"... Trying another server")
        pass
  if (connection == "fail"):
     os.system("rm -f "+fname)
     exit("get key data failed for "+dataKey+", No connection to consul")

####getting config variables from consul
os.environ['token'] = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
data = getKeyData('app/phone_alert/config/twilio_accid',False)
if data is not None :
   accid = data['Value']
else :
   print "app/phone_alert/config/twilio_accid is None"
   os.system("rm -f "+fname)
   exit(0)

data = getKeyData('app/phone_alert/config/twilio_accpwd',False)
if data is not None :
   accpwd = data['Value']
else :
   print "app/phone_alert/config/twilio_accpwd is None"
   os.system("rm -f "+fname)
   exit(0)

data = getKeyData('app/phone_alert/config/twilioUrl',False)
if data is not None :
  twilioUrl = data['Value']
  twilioUrl = twilioUrl+accid+'/Calls.json'
else :
   print "app/phone_alert/config/twilioUrl is None"
   os.system("rm -f "+fname)
   exit(0)

data = getKeyData('app/phone_alert/config/metricUri',False)
if data is not None :
   metricUri = data['Value']
   metricUri = metricUri+metrics+'.xml'
else :
   print "app/phone_alert/config/metricUri is None"
   os.system("rm -f "+fname)
   exit(0)

data = getKeyData('app/phone_alert/config/callBackUrl',False)
if data is not None :
   callBackUrl = data['Value']
else :
   print "app/phone_alert/config/callBackUrl is None"
   os.system("rm -f "+fname)
   exit(0)

data = getKeyData('app/phone_alert/config/slack/channels',False)
if data is not None :
   slackChannel = data['Value']
else :
   print "app/phone_alert/config/slack/channels is None"
   os.system("rm -f "+fname)
   exit(0)

data = getKeyData('app/phone_alert/config/metric',False)
if data is not None :
   metricList = data['Value']
else :
   print "app/phone_alert/config/metric is None"
   os.system("rm -f "+fname)
   exit(0)


##### if current metrics not in  our list
if metrics not in metricList:
   os.system("rm -f "+fname)
   exit(metrics+" is not in our list")

#######Returns the shift name i.e second shift ss, first shift fs
def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

def getShiftName():
        hh=datetime.datetime.now().hour
        mm=datetime.datetime.now().minute
        if   (time_in_range(datetime.time(07, 0, 0), datetime.time(13, 0, 0), datetime.time(hh, mm, 0)) ) :
              shift='FS'
        elif (time_in_range(datetime.time(13, 01, 0), datetime.time(22, 0, 0), datetime.time(hh, mm, 0)) ):
              shift='SS'
        elif (time_in_range(datetime.time(22, 01, 0), datetime.time(06, 59, 0), datetime.time(hh, mm, 0)) ):
              shift='TS'
        else :
              print "Unexpected time slot shift not found"
        return shift

####team name to which alert should be reported
def getTeamName(alert):
    team_dict={'Process-HTTPD':'devops'}
    team= team_dict[alert]
    return team

#######replaces string in a file
def replacemetric(targetfile,srcStr,destStr):
      with open(targetfile) as f:
          s = f.read()
      s = s.replace(srcStr, destStr)
      with open(targetfile, "w") as f:
          f.write(s)

####Gets the supports persons list in team
def getSupportList(shift,team):
  supportList=[]
  supportKey = 'app/roster/'+date+'/'+shift+'/'+team+'/'
  data = getKeyData(supportKey,True)
  if data is not None :
    n = 0
    while n < len(data):
      dataSplit=data[n].split('/')
      user=dataSplit[len(dataSplit) - 1]
      supportList.append(user)
      n = n+1
  else  :
      print "No person alligned in shift in " + supportKey
  return supportList


##return support name and contact info
def getSupportInfo(shift,team,person):
    userkey = 'app/roster/'+date+'/'+shift+'/'+team+'/'+person+''
    data = getKeyData(userkey,False)
    if data is not None :
       onCallPerson = str(data['Value'])
       contactKey = 'teams/'+team+'/'+onCallPerson+'/mobile'
       data = getKeyData(contactKey,False)
       if data is not None :
          contactNo = str(data['Value'])
          print "getSupportInfo returned " + onCallPerson + "_" + contactNo
          return onCallPerson , contactNo
       else :
          print contactKey +" is not present ,Please update user contact info "
          return onCallPerson , "None"
    else :
       print userkey +' is not present in roster please allign someone'
       return "None","None"


##get the call status for dialled no
def getCalltStatus(sessId):
    callStatusKey='app/phone_alert/call_tracker/'+sessId+'/status'
    data = getKeyData( callStatusKey,False)
    if data is not None :
        callStatus = str(data['Value'])
        return callStatus
    else :
       return 'None'

###Getting userfeedback on phone
def getUserInput(sessId):
    userResponseKey='app/phone_alert/call_tracker/'+sessId+'/response'
    data = getKeyData( userResponseKey , False)
    if data is not None :
        userResponse = str(data['Value'])
        print "CallResponse for "+userResponseKey+" is "+ userResponse
        return userResponse
    else :
       print  "callresponse  not found for "+ userResponseKey
       return 'None'

##Function for slack notification
def slackNotificationSucess(onCallPerson,sessId,contactNo,alert,colorCode,callStatus,userResponse):
    try:
        token = os.environ['token']
        slack = Slacker(token)
        obj = slack.chat.post_message(
            channel=slackChannel,
            text='',
            username='Incident Call Notification',
            icon_url='https://i.imgur.com/s6d1CKS.png',
            attachments=[{
        "mrkdwn_in": ["text", "fallback"],
        "fallback": "Automated Incident Call: `'alert'`",
        "text": "Automated Incident Call Genrated Against "+'`'+ alert +'`',
        "fields": [{
                "title": "Call Tracker ID",
                "value": sessId,
                "short": "true"
        }, {
                "title": "Support Engineer",
                "value": onCallPerson,
                "short": "true"
        }, {
                "title": "Call Status",
                "value": callStatus,
                "short": "true"
        }, {
                "title": "User Input",
                "value": userResponse,
                "short": "true"
        }],
        "color": colorCode
}])
        notifyStatus = obj.successful, obj.__dict__['body']['channel'], obj.__dict__[
            'body']['ts']
        print obj.successful, obj.__dict__['body']['channel'], obj.__dict__[
            'body']['ts']
    except KeyError, ex:
        notifyStatus = 'Environment variable %s not set.' % str(ex)
        print 'Environment variable %s not set.' % str(ex)
    return notifyStatus


####Defining function for calling on support person
def callingSupport(onCallPerson,contactNo,team,supportLength,n,alert):
        print "calling to : "+ onCallPerson
        to = contactNo
        #to='+918178996458'
        #to='+918800395588'
        #to='+918452977354'
        phno='+16198320049'
        sourcefile='/opt/twilio/templates/'+metrics+'.xml'
        targetfile='/opt/twilio/alerts/'+metrics+'.xml'
        createAlertFile='cp "'+sourcefile+'" "'+targetfile+'"'
        os.system(createAlertFile)
        replacemetric(targetfile,"$module",module)

        sessId=''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))
        replacemetric(targetfile,"$sessId",sessId)

        print "sessId " + sessId
        key="JioBotqazQAZ"

        curl_command='curl -s -XPOST '+twilioUrl+' --data-urlencode "Url='+metricUri+'" --data-urlencode "To='+to+'" --data-urlencode "From='+phno+'" -u "'+accid+':'+accpwd+'" --data-urlencode "StatusCallback='+callBackUrl+'?key='+key+'&sessId='+sessId+'"  --data-urlencode "Method=GET" --data-urlencode "StatusCallbackMethod=POST" --data-urlencode "StatusCallbackEvent=initiated" --data-urlencode "StatusCallbackEvent=ringing" --data-urlencode "StatusCallbackEvent=answered" --data-urlencode "StatusCallbackEvent=completed"'

        print "=========Making Call=========="
        os.system(curl_command)
        callStatus=getCalltStatus(sessId)
        while (callStatus != "failed" and callStatus != "completed"):
            callStatus = getCalltStatus(sessId)
            time.sleep(5)

        if (callStatus == "completed"):
            userResponse = getUserInput(sessId)
            if userResponse == "1":
                slackNotify = slackNotificationSucess(onCallPerson,sessId,contactNo,alert,"#008000","Call answered","Issue acknowledged")
                #slack "support accepted the alert"
                os.system("rm -f "+fname)
                exit(0)
            elif userResponse == "2" :
                #slack "support rejected the alert"
                slackNotify = slackNotificationSucess(onCallPerson,sessId,contactNo,alert,"#ff0000","Call answered","Rejected")
                n=n+1
                if n < supportLength :
                    onCallPerson,contactNo = getSupportInfo(shift,team,supportList[n])
                    callingSupport(onCallPerson,contactNo,team,supportLength,n,alert)
                else :
                    slackNotify = slackNotificationSucess("None","None",alert,"#ff0000","No Support avilable","None")
                    #slack "No other person in shift present check for escalation"
            else :
                slackNotify = slackNotificationSucess(onCallPerson,sessId,contactNo,alert,"#ff0000",callStatus,userResponse)
                #slack "support person entered wrong input : userinput"

        elif (callStatus == "failed"):
                #slack "Call failed for user :SupportPerson"
                slackNotify = slackNotificationSucess(onCallPerson,sessId,contactNo,alert,"#ff0000","User unreachable/No response","None")
                n=n+1
                print "called status : "+ callStatus
                if n < supportLength :
                    onCallPerson,contactNo = getSupportInfo(shift,team,supportList[n])
                    callingSupport(onCallPerson,contactNo,team,supportLength,n,alert)
                else :
                    #slack "No other person in shift present check for escalation"
                    slackNotify = slackNotificationSucess("None",sessId,"None",alert,"#ff0000","No more support avilable","None")
        else :
             slackNotify = slackNotificationSucess(onCallPerson,sessId,contactNo,alert,"#ff0000","No Call Status returned",callResponse)
             print "No Call Status returned "+ callstatus


#Initiating call
n = 0
shift = getShiftName()
team = getTeamName(metrics)
supportList = getSupportList(shift,team)
supportLength= len(supportList)
print "No of persons in shift : " + shift +" = " + str(supportLength)

if (supportLength <= 0):
    slackNotify = slackNotificationSucess("None","None","None",alert,"#ff0000","No person alligned for shift: "+shift,"None")
    os.system("rm -f "+fname)
    exit(0)

print supportList

onCallPerson,contactNo = getSupportInfo(shift,team,supportList[n])
if (onCallPerson != "None" and contactNo != "None"):
    callingSupport(onCallPerson,contactNo,team,supportLength,n,alert)
else :
    os.system("rm -f "+fname)
    exit("Either onCallPerson or contactNo missing")

os.system("rm -f "+fname)
