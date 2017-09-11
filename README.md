# twiliCall
twillicall
#####Project CAll (twilio,gupshup)#######
https://www.twilio.com/blog/2015/05/introducing-call-progress-events-flexibly-track-and-control-your-outbound-calls.html
  
======================Twilio on call support========================================================================
+----------------+     +----------------+   +--------------+
|   CloudWatch   +---->+  SQS/RabbitMQ  +--->  Stackstorm  |
|      alarm     |     |                |   |              |
+----------------+     +----------------+   +------+-------+
                                                   |
                                                   |
                                                   |
                                                   |
                                           +-------v--------+
                      +---------------+    |  Python script |       +------------------+
                      | Slack Notify  +<---+  Triggered By  +------>|  Consul KV Storm |
                      +---------------+    |   Stackstorm   |       +------------------+
                                           +-------+--------+
                                                   |
                                                   v
                                            +------+--------+
                                            |  Trigger Call |
                                            +---------------+

=====================================================================================================================
===============================================StackStorm Rule=======================================================
---
description: 'Twilio oncall'
tags: []
type:
  ref: standard
  parameters:
enabled: true
name: Callout
trigger:
  ref: aws.sqs_new_message
  type: aws.sqs_new_message
  parameters:
criteria:
  trigger.body:
    pattern: tggnotification
    type: contains
action:
  ref: core.local_sudo
  parameters:
    cmd: 'echo -e  ''{{trigger.body}}'' > /opt/twilio/triggerout/alarm.out && stdbuf -oL python  /opt/twilio/scripts/twilioCall.py  >> /tmp/twilio.log &'
pack: aws
ref: aws.Callout
id: xxxxxxxxxxxxxxxxxxxx
uid: 'rule:aws:Callout'
========================================================================================================================================================
==========Consul KV store And configs==================================================== 
app/roster/2017/09/8/FS/devops/Shaktis.Rathore
teams/devops/Shaktis.Rathore/mobile
app/phone_alert/config/metric/m1
app/phone_alert/config/metric/m2
app/phone_alert/config/twilio_accid='xxxxxxxxxxxxxxxxxxx'
app/phone_alert/config/twilio_accpwd='xxxxxxxxxxxxxxxxxxx'
app/phone_alert/config/twilioUrl='https://api.twilio.com/2010-04-01/Accounts/'
app/phone_alert/config/metricUri='http://xxxxxxxxx:9191/'
app/phone_alert/config/callBackUrl='http://xxxxxxxxxxxxxx:8082/callstatus.php'
app/phone_alert/config/slack/channels='C6MTRBVT8'

slack api token = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
consulServer=['']
================Twilio  Use cases==================================================================
1.No one available for support : done
2.1st one accepted : done
3.1st one rejected 2nd accepeted   : done 
4.both rejected : done
5.1st failed 2nd accepted  : done
6.both failed : done

failed : User unreachable/No response
Rejected : call answered 
Accepted : call answered and issue acknowledged


curl -XPOST https://api.twilio.com/2010-04-01/Accounts/xxxxxxxxxxxxxxxxxxxxxxxxx/Calls.json \
   --data-urlencode "Url=http://demo.twilio.com/docs/voice.xml" \
   --data-urlencode "To=+91817xxxxx" \
   --data-urlencode "From=+16xxxxxxxx9" \
   -u 'Axxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxa9:3d7bxxxxxxxxxx'


curl -XPOST https://api.twilio.com/2010-04-01/Accounts/ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/Calls.json \
    --data-urlencode "Url=http://demo.twilio.com/docs/voice.xml" \
    --data-urlencode "To=+xxxxxxxxxxxxxxxxxx" \
    --data-urlencode "From=+xxxxxxxxxxxxx" \
    --data-urlencode "Method=GET" \
    --data-urlencode "StatusCallback=https://www.myapp.com/events" \
    --data-urlencode "StatusCallbackMethod=POST" \
    --data-urlencode "StatusCallbackEvent=initiated" \
    --data-urlencode "StatusCallbackEvent=ringing" \
    --data-urlencode "StatusCallbackEvent=answered" \
    --data-urlencode "StatusCallbackEvent=completed" \
    -u 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX:your_auth_token'
