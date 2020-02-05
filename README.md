# twilioCall

## Project CAll (twilio,gupshup)
[Twilio blog link](https://www.twilio.com/blog/2015/05/introducing-call-progress-events-flexibly-track-and-control-your-outbound-calls.html)
  
### ======================Twilio on call support===========================================================

```
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
```

