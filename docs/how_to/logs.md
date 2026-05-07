# Logs
This page goes over what is required log-wise to run the analytics tool

## Where to find your Eve Logs
You can find these in your Documents folder under Eve. The chat logs and game logs are in different folders. 
both tq and tdome drop to the same folder and there is no good way to know what is what other than timestamps

### Local Log Details
You need 1 pilots Local log file. you can see an example of a local log file [here](https://github.com/ender-locke/eve-analytics/blob/dev/sample_logs/2026-04-25/Local_20260425_180048_2112017084.txt)

The local log dictates the timestamps that are used to generate the combat logs that are added to the database and generated on the analytics

The start timestamp is dictated as follows: 
- the first one of ["go", "gooo", "0", "goo", "goooo", "googogo", "gogogo!"] is match start ts
- the following one of ["gf", "wf", "gg", "time", "match completed!"] is the end ts
- more than one match can be found per local file

**Note**: if you want to change the timestamps before uploading the easiest thing to do is quickly change your local log

### Combat Logs Details
You need 1 to n pilot combat logs. you can see examples of combat logs [here](https://github.com/ender-locke/eve-analytics/blob/dev/sample_logs/2026-04-25/)

**Notes**:
- if you get disconnected during a scrim youll have multiple logs. you can upload multiple logs per pilot if need be
- 

