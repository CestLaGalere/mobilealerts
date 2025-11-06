Mobile Alerts REST API
The REST API provides read access to the most recent received measurement for ID01,
ID02, ID03, ID04, ID05, ID06, ID07, ID08, ID09, ID0A, ID0B, ID0E, ID0F, ID10, ID11, ID12,
ID15, ID17, ID18 and ID20 sensors.
Overview
Requests are made using HTTPS. All requests are POST request. Request parameters are
encoded in the “application/x-www-form-urlencoded” format. All requests return data
encoded in json. Datetime values are encoded as the number of seconds since 1.1.1970.
The base url of the REST API is https://www.data199.com/api/pv1.
Successfull calls return json using the following structure:
{
"success" : true,
[Response data],
}
Calls with errors return json using the following structure:
{
"success" : false,
"errorcode" : 1,
"errormessage" : "Some error message",
}
API Rate Limits
Rate limiting is considered on a per sensor basis. Allowed are up to 3 calls for a sensor
within one minute. If more than 3 calls are made within one minute further calls are
blocked for 7 minutes.
If rate limiting is applied the server returns the HTTP response code “429 Too Many
Requests”.
Invalid call blocking
To prevent misuse, if more than 5 calls with invalid parameters are made from the same ip
address within 15 minutes, further calls from the same ip address within the 15 minute
time window will be blocked.
If invalid call blocking is applied the server returns the HTTP response code “403
Forbidden”.
Last Measurement Query
Request Url
https://www.data199.com/api/pv1/device/lastmeasurement
Request Parameters
deviceids=0E7EA4A71203,09265A8A3503&phoneid=880071013613
deviceids: One or more sensor ids, separated by colons.
phoneid: The phone id of an app where the provided sensor ids are part of the dashboard.
This parameter can be ommited. If the phone id is provided alert flags will be added to
returned measurements that have active alert conditions and to measurements that ended
active alert condition. Otherwise no alert flags are added to the measurements even if a
phoneid has been provided.
Response
{
"success": true,
"phoneid": "880071013613",
"devices": [
{
"deviceid": "0E7EA4A71203",
"lastseen": 1466501944,
"lowbat": false,
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
[Sensor type specific alert flags]
}
},
{
"deviceid": "09265A8A3503",
"lastseen": 1466768149,
"lowbat": false,
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
[Sensor type specific alert flags]
}
}
]
}
success: If the request was successful.
phoneid: The phone id of an app where the sensor is part of the dashboard. May be ommited
if no phoneid has been provided in the request.
devices: Array of sensors, one for each queried sensor id.
deviceid: The id of a sensor.
lastseen: The timestamp when a sensor was last seen by the server in epoch time.
lowbat: If a sensor was low on battery when sending the measurement.
measurement: The last received measurement of a sensor. General measurement properties
are returned for all sensor types. Sensor type specific measurement properties and alert
flags are different from sensor type to sensor type. The alert flags are only part of the
response if a phone id has been provided when requesting. Also, alert flags will be added
only if there is currently an active alert condition for a measurement or a measurement
ended an active alert condition. Otherwise no alert flags are added to the response even if a
phoneid has been provided.
General measurement properties
"measurement": {
"idx": 3935,
"ts": 123123123,
"c": 1466501944,
[Sensor type specific measurement properties]
[Sensor type specific alert flags]
}
idx: Unique id of the measurement.
ts: Timestamp of the measurement in epoch time.
c: Timestamp when the measurement was received by the server.
Special measurement values
• If a sensor was not connected the value 43530 is returned.
• If the measurement of a sensor was out of range the value 65295 is returned.
ID01 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"t2": 20.4,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
t2: The measured temperature in celsius of the cable sensor.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"t2hi": true,
"t2hise": true,
"t2hiee": false,
"t2his": 20.0,
"t2lo": false,
"t2lose": false,
"t2loee": false,
"t2los": 0.0
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active alert
condition.
Temperature Low Alert
t1lo: If there is an active cable sensor temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active cable sensor
low alert condition.
Cable Sensor Temperature High Alert
t2hi: If there is an active cable sensor temperature high alert condition.
t2hise: If the cable sensor alert condition started because of this measurement.
t2hiee: If an cable sensor alert condition ended because of this measurement.
t2his: The alert treshhold. Measurements above this treshhold have an active cable sensor
alert condition.
Cable Sensor Temperature Low Alert
t2lo: If there is an active cable sensor temperature low alert condition.
t2lose: If the cable sensor alert condition started because of this measurement.
t2loee: If an cable sensor alert condition ended because of this measurement.
t2los: The alert treshhold. Measurements below this treshhold have an active cable sensor
low alert condition.
ID02 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active alert
condition.
Temperature Low Alert
t1lo: If there is an active cable sensor temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active cable sensor
low alert condition.
ID03 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"h": 53.8,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
h: The measured humidity.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"hhi": true,
"hhise": true,
"hhiee": false,
"hhis": 40,

"hlo": false,
"hlose": false,
"hloee": false,
"hlos": 10
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active alert
condition.
Temperature Low Alert
t1lo: If there is an active temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Humidity High Alert
hhi: If there is an active humidity high alert condition.
hhise: If the alert condition started because of this measurement.
hhiee: If an alert condition ended because of this measurement.
hhis: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Humidity Low Alert
hlo: If there is an active humidity high alert condition.
hlose: If the alert condition started because of this measurement.
hloee: If an alert condition ended because of this measurement.
hlos: The alert treshhold. Measurements above this treshhold have an active low alert
condition.
ID04 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"t2": 20.4,
"h": 53.8,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
t2: The measured temperature in celsius of the cable sensor.
h: The measured humidity.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"t2hi": true,
"t2hise": true,
"t2hiee": false,
"t2his": 20.0,
"t2lo": false,
"t2lose": false,
"t2loee": false,
"t2los": 0.0,

"hhi": true,
"hhise": true,
"hhiee": false,
"hhis": 40,

"hlo": false,
"hlose": false,
"hloee": false,
"hlos": 10
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Temperature Low Alert
t1lo: If there is an active temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Cable Sensor Temperature High Alert
t2hi: If there is an active cable sensor temperature high alert condition.
t2hise: If the cable sensor alert condition started because of this measurement.
t2hiee: If an cable sensor alert condition ended because of this measurement.
t2his: The alert treshhold. Measurements above this treshhold have an active cable sensor
alert condition.
Cable Sensor Temperature Low Alert
t2lo: If there is an active cable sensor temperature low alert condition.
t2lose: If the cable sensor alert condition started because of this measurement.
t2loee: If an cable sensor alert condition ended because of this measurement.
t2los: The alert treshhold. Measurements below this treshhold have an active cable sensor
low alert condition.
Humidity High Alert
hhi: If there is an active humidity high alert condition.
hhise: If the alert condition started because of this measurement.
hhiee: If an alert condition ended because of this measurement.
hhis: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Humidity Low Alert
hlo: If there is an active humidity high alert condition.
hlose: If the alert condition started because of this measurement.
hloee: If an alert condition ended because of this measurement.
hlos: The alert treshhold. Measurements above this treshhold have an active low alert
condition.
ID05 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"t2": 20.4,
"h": 53.8,
"ppm": 1750.0,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
t2: The measured temperature in celsius of the external sensor.
h: The measured humidity.
ppm: The measured air quality.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"t2hi": true,
"t2hise": true,
"t2hiee": false,
"t2his": 20.0,
"t2lo": false,
"t2lose": false,
"t2loee": false,
"t2los": 0.0,

"hhi": true,
"hhise": true,
"hhiee": false,
"hhis": 40,

"hlo": false,
"hlose": false,
"hloee": false,
"hlos": 10,
"ppmhi": false,
"ppmhise": false,
"ppmhiee": false,
"ppmhis": 1050
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active alert
condition.
Temperature Low Alert
t1lo: If there is an active temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active sensor low
alert condition.
External Sensor Temperature High Alert
t2hi: If there is an active external sensor temperature high alert condition.
t2hise: If the external sensor alert condition started because of this measurement.
t2hiee: If an external sensor alert condition ended because of this measurement.
t2his: The alert treshhold. Measurements above this treshhold have an active external
sensor alert condition.
External Sensor Temperature Low Alert
t2lo: If there is an active external sensor temperature low alert condition.
t2lose: If the external sensor alert condition started because of this measurement.
t2loee: If an external sensor alert condition ended because of this measurement.
t2los: The alert treshhold. Measurements below this treshhold have an active external
sensor low alert condition.
Humidity High Alert
hhi: If there is an active humidity high alert condition.
hhise: If the alert condition started because of this measurement.
hhiee: If an alert condition ended because of this measurement.
hhis: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Humidity Low Alert
hlo: If there is an active humidity high alert condition.
hlose: If the alert condition started because of this measurement.
hloee: If an alert condition ended because of this measurement.
hlos: The alert treshhold. Measurements above this treshhold have an active low alert
condition.
Air Quality Alert
ppmhi: If there is an active air quality alert condition.
ppmhise: If the alert condition started because of this measurement.
ppmhiee: If an alert condition ended because of this measurement.
ppmhis: The alert treshhold. Measurements above this treshhold have an active alert
condition.
ID06 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"t2": 20.4,
"h": 53.8,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
t2: The measured temperature in celsius of the cable sensor.
h: The measured humidity.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"t2hi": true,
"t2hise": true,
"t2hiee": false,
"t2his": 20.0,
"t2lo": false,
"t2lose": false,
"t2loee": false,
"t2los": 0.0,

"hhi": true,
"hhise": true,
"hhiee": false,
"hhis": 40,

"hlo": false,
"hlose": false,
"hloee": false,
"hlos": 10
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Temperature Low Alert
t1lo: If there is an active temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Cable Sensor Temperature High Alert
t2hi: If there is an active cable sensor temperature high alert condition.
t2hise: If the cable sensor alert condition started because of this measurement.
t2hiee: If an cable sensor alert condition ended because of this measurement.
t2his: The alert treshhold. Measurements above this treshhold have an active cable sensor
high alert condition.
Cable Sensor Temperature Low Alert
t2lo: If there is an active cable sensor temperature low alert condition.
t2lose: If the cable sensor alert condition started because of this measurement.
t2loee: If an cable sensor alert condition ended because of this measurement.
t2los: The alert treshhold. Measurements below this treshhold have an active cable sensor
low alert condition.
Humidity High Alert
hhi: If there is an active humidity high alert condition.
hhise: If the alert condition started because of this measurement.
hhiee: If an alert condition ended because of this measurement.
hhis: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Humidity Low Alert
hlo: If there is an active humidity high alert condition.
hlose: If the alert condition started because of this measurement.
hloee: If an alert condition ended because of this measurement.
hlos: The alert treshhold. Measurements above this treshhold have an active low alert
condition.
ID07 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"t2": 20.4,
"h": 53.8,
"h2": 33.5,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
t2: The measured temperature in celsius of the external sensor.
h: The measured humidity.
h: The measured humidity of the external sensor.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"t2hi": true,
"t2hise": true,
"t2hiee": false,
"t2his": 20.0,
"t2lo": false,
"t2lose": false,
"t2loee": false,
"t2los": 0.0,

"hhi": true,
"hhise": true,
"hhiee": false,
"hhis": 40,

"hlo": false,
"hlose": false,
"hloee": false,
"hlos": 10,
"h2hi": true,
"h2hise": true,
"h2hiee": false,
"h2his": 40,

"h2lo": false,
"h2lose": false,
"h2loee": false,
"h2los": 10
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Temperature Low Alert
t1lo: If there is an active temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
External Sensor Temperature High Alert
t2hi: If there is an active external sensor temperature high alert condition.
t2hise: If the external sensor alert condition started because of this measurement.
t2hiee: If an external sensor alert condition ended because of this measurement.
t2his: The alert treshhold. Measurements above this treshhold have an active external
sensor high alert condition.
External Sensor Temperature Low Alert
t2lo: If there is an active external sensor temperature low alert condition.
t2lose: If the external sensor alert condition started because of this measurement.
t2loee: If an external sensor alert condition ended because of this measurement.
t2los: The alert treshhold. Measurements below this treshhold have an active external
sensor low alert condition.
Humidity High Alert
hhi: If there is an active humidity high alert condition.
hhise: If the alert condition started because of this measurement.
hhiee: If an alert condition ended because of this measurement.
hhis: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Humidity Low Alert
hlo: If there is an active humidity high alert condition.
hlose: If the alert condition started because of this measurement.
hloee: If an alert condition ended because of this measurement.
hlos: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
External Humidity High Alert
h2hi: If there is an active humidity high alert condition.
h2hise: If the alert condition started because of this measurement.
h2hiee: If an alert condition ended because of this measurement.
h2his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
External Humidity Low Alert
h2lo: If there is an active humidity low alert condition.
h2lose: If the alert condition started because of this measurement.
h2loee: If an alert condition ended because of this measurement.
h2los: The alert treshhold. Measurements above this treshhold have an active low alert
condition.
ID08 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"r": 11.352,
"rf": 44,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
r: The rain value in mm. 0.258 mm of rain are equal to one flip.
rf: The flip count of the rain sensor. A flip equals 0.258 mm of rain.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"rhi": true,
"rhis": 20.0,
"rhist": 12,

"rlo": false,
"rlos": 1.0,
"rlost": 168,

"rb": false
}
rhi: If this measurement triggered a rain max alert.
rhis: The amount of rain that will trigger a rain max alert.
rhist: The timespan in hours within which the rain must fall to trigger a rain max alert.
rlo: If this measurement represents a rain lo alert.
rlos: The low rain treshhold in mm. If the rain is below this value for a longer period of time
than the configured timespan rlost, a low rain alert will be triggered.
rlost: The timespan in hours the fallen rain must stay below the rlos treshhold before a low
rain alert is triggered.
rb: If this measurement triggered a rain begin alert.
ID09 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"t2": 20.4,
"h": 53.8,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
t2: The measured temperature in celsius of the cable sensor.
h: The measured humidity.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"t2hi": true,
"t2hise": true,
"t2hiee": false,
"t2his": 20.0,
"t2lo": false,
"t2lose": false,
"t2loee": false,
"t2los": 0.0,

"hhi": true,
"hhise": true,
"hhiee": false,
"hhis": 40,

"hlo": false,
"hlose": false,
"hloee": false,
"hlos": 10
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If the alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Temperature Low Alert
t1lo: If there is an active temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If the alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Cable Sensor Temperature High Alert
t2hi: If there is an active cable sensor temperature high alert condition.
t2hise: If the alert condition started because of this measurement.
t2hiee: If the alert condition ended because of this measurement.
t2his: The alert treshhold. Measurements above this treshhold have an active cable sensor
high alert condition.
Cable Sensor Temperature Low Alert
t2lo: If there is an active cable sensor temperature low alert condition.
t2lose: If the alert condition started because of this measurement.
t2loee: If the alert condition ended because of this measurement.
t2los: The alert treshhold. Measurements below this treshhold have an active cable sensor
low alert condition.
Humidity High Alert
hhi: If there is an active humidity high alert condition.
hhise: If the alert condition started because of this measurement.
hhiee: If the alert condition ended because of this measurement.
hhis: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Humidity Low Alert
hlo: If there is an active humidity low alert condition.
hlose: If the alert condition started because of this measurement.
hloee: If the alert condition ended because of this measurement.
hlos: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
ID0A measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 20.3,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"a1": false,
"a2": false,
"a3": false,
"a4": false
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Temperature Low Alert
t1lo: If there is an active temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Smoke Detector Alerts
a1: If there is an active smoke alert condition for smoke detector 1.
a2: If there is an active smoke alert condition for smoke detector 2.
a3: If there is an active smoke alert condition for smoke detector 3.
a4: If there is an active smoke alert condition for smoke detector 4.
ID0B measurement and alerts properties
Measurement properties
"measurement": {
[General measurement properties]
"ws": 0.0,
"wg": 0.0,
"wd": 6,
[Sensor type specific alert flags]
}
ws: The measured windspeed in m/s.
wg: The measured gust in m/s.
wd: The wind direction. 0: North, 1: North-northeast, 2: Northeast, 3: East-northeast, 4:
East, 5: East-southeast, 6: Southeast, 7: South-Southeast, 8: South, 9: South-southwest, 10:
Southwest, 11: West-southwest, 12: West, 13: West-northwest, 14: Northwest, 15: Northnorthwest
Alert Flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"wsa": false,
"wsaactive": false,
"wsas": 20.0,
"wga": false,
"wgaactive": false,
"wgas": 20.0,
"wds": 0
}
wsa: If there is an active windspeed alert condition.
wsaactive: If the wind speed alert setting was active.
wsas: The configured wind speed alert treshhold.
wga: If there is an active gust alert condition.
wgaactive: If the gust alert setting was active.
wgas: The configured gust alert treshhold.
wds: The wind and gust alert direction setting flags. One bit per wind direction. From least
significant bit to most significant bit: N, NNE, NE, ENE, E, ESE, SE, SSE, S, SSW, SW, WSW, W,
WNW, NW, NNW.
ID0E measurement and alerts properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"h": 53.8,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
h: The measured humidity.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,

"hhi": true,
"hhise": true,
"hhiee": false,
"hhis": 40,

"hlo": false,
"hlose": false,
"hloee": false,
"hlos": 10
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active alert
condition.
Temperature Low Alert
t1lo: If there is an active temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Humidity High Alert
hhi: If there is an active humidity high alert condition.
hhise: If the alert condition started because of this measurement.
hhiee: If an alert condition ended because of this measurement.
hhis: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Humidity Low Alert
hlo: If there is an active humidity high alert condition.
hlose: If the alert condition started because of this measurement.
hloee: If an alert condition ended because of this measurement.
hlos: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
ID0F measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"t2": 20.4,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
t2: The measured temperature in celsius of the cable sensor.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"t2hi": true,
"t2hise": true,
"t2hiee": false,
"t2his": 20.0,
"t2lo": false,
"t2lose": false,
"t2loee": false,
"t2los": 0.0
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Temperature Low Alert
t1lo: If there is an active temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Cable Sensor Temperature High Alert
t2hi: If there is an active cable sensor temperature high alert condition.
t2hise: If the cable sensor alert condition started because of this measurement.
t2hiee: If an cable sensor alert condition ended because of this measurement.
t2his: The alert treshhold. Measurements above this treshhold have an active cable sensor
temperature high alert condition.
Cable Sensor Temperature Low Alert
t2lo: If there is an active cable sensor temperature low alert condition.
t2lose: If the cable sensor alert condition started because of this measurement.
t2loee: If an cable sensor alert condition ended because of this measurement.
t2los: The alert treshhold. Measurements below this treshhold have an active cable sensor
temperature low alert condition.
ID10 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"w": false,
[Sensor type specific alert flags]
}
w: If the window is opened or closed.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"wo": true,
"woa": true,
"wc": false,
"wca": false,
"wot": false,
"wota": false,
"wots": 1,
"wct": false,
"wcta": false,
"wcts": 1,
}
Window Alert Flags
wo: If there is an active window open alert condition.
woa: If the window open alert setting is active.
wc: If there is an active window closed alert condition.
wca: If the window closed alert setting is active.
wot: If there is an active window open timespan alert condition.
wota: If the window open timespan alert setting is active.
wots: How many hours after opening the alert will be triggered.
wct: If there is an active window closed timespan alert condition.
wcta: If the window closed timespan alert setting is active.
wcts: How many hours after closing the alert will be triggered.
ID11 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"t2": 20.4,
"t3": 18.1,
"t4": 5.1,
"h1": 53,
"h2": 48,
"h3": 77,
"h4": 12,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
t2: The measured temperature in celsius of temperature sensor 2.
t3: The measured temperature in celsius of temperature sensor 3.
t4: The measured temperature in celsius of temperature sensor 4.
h1: The measured humidity.
h2: The measured humidity of humidity sensor 2.
h3: The measured humidity of humidity sensor 3.
h4: The measured humidity of humidity sensor 4.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"t2hi": true,
"t2hise": true,
"t2hiee": false,
"t2his": 20.0,
"t2lo": false,
"t2lose": false,
"t2loee": false,
"t2los": 0.0,

"t3hi": false,
"t3hise": false,
"t3hiee": false,
"t3his": 20.0,
"t3lo": false,
"t3lose": false,
"t3loee": false,
"t3los": 0.0,
"t4hi": false,
"t4hise": false,
"t4hiee": false,
"t4his": 20.0,
"t4lo": false,
"t4lose": false,
"t4loee": false,
"t4los": 0.0,
"h1hi": true,
"h1hise": true,
"h1hiee": false,
"h1his": 40,

"h1lo": false,
"h1lose": false,
"h1loee": false,
"h1los": 10,
"h2hi": false,
"h2hise": false,
"h2hiee": false,
"h2his": 40,

"h2lo": false,
"h2lose": false,
"h2loee": false,
"h2los": 10,
"h3hi": false,
"h3hise": false,
"h3hiee": false,
"h3his": 40,

"h3lo": false,
"h3lose": false,
"h3loee": false,
"h3los": 10,
"h4hi": false,
"h4hise": false,
"h4hiee": false,
"h4his": 40,

"h4lo": false,
"h4lose": false,
"h4loee": false,
"h4los": 10
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Temperature Low Alert
t1lo: If there is an active temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Sensor 2 Temperature High Alert
t2hi: If there is an active sensor 2 temperature high alert condition.
t2hise: If the alert condition started because of this measurement.
t2hiee: If the alert condition ended because of this measurement.
t2his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Sensor 2 Temperature Low Alert
t2lo: If there is an active sensor 2 temperature low alert condition.
t2lose: If the alert condition started because of this measurement.
t2loee: If the alert condition ended because of this measurement.
t2los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Sensor 3 Temperature High Alert
t3hi: If there is an active sensor 3 temperature high alert condition.
t3hise: If the alert condition started because of this measurement.
t3hiee: If the alert condition ended because of this measurement.
t3his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Sensor 3 Temperature Low Alert
t3lo: If there is an active sensor 3 temperature low alert condition.
t3lose: If the alert condition started because of this measurement.
t3loee: If the alert condition ended because of this measurement.
t3los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Sensor 4 Temperature High Alert
t4hi: If there is an active sensor 4 temperature high alert condition.
t4hise: If the alert condition started because of this measurement.
t4hiee: If the alert condition ended because of this measurement.
t4his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Sensor 4 Temperature Low Alert
t4lo: If there is an active sensor 4 temperature low alert condition.
t4lose: If the alert condition started because of this measurement.
t4loee: If the alert condition ended because of this measurement.
t4los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Humidity High Alert
h1hi: If there is an active humidity high alert condition.
h1hise: If the alert condition started because of this measurement.
h1hiee: If the alert condition ended because of this measurement.
h1his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Humidity Low Alert
h1lo: If there is an active humidity low alert condition.
h1lose: If the alert condition started because of this measurement.
h1loee: If the alert condition ended because of this measurement.
h1los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Sensor 2 Humidity High Alert
h2hi: If there is an active sensor 2 humidity high alert condition.
h2hise: If the alert condition started because of this measurement.
h2hiee: If the alert condition ended because of this measurement.
h2his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Sensor 2 Humidity Low Alert
h2lo: If there is an active sensor 2 humidity low alert condition.
h2lose: If the alert condition started because of this measurement.
h2loee: If the alert condition ended because of this measurement.
h2los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Sensor 3 Humidity High Alert
h3hi: If there is an active sensor 3 humidity high alert condition.
h3hise: If the alert condition started because of this measurement.
h3hiee: If the alert condition ended because of this measurement.
h3his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Sensor 3 Humidity Low Alert
h3lo: If there is an active sensor 3 humidity low alert condition.
h3lose: If the alert condition started because of this measurement.
h3loee: If the alert condition ended because of this measurement.
h3los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Sensor 4 Humidity High Alert
h4hi: If there is an active sensor 4 humidity high alert condition.
h4hise: If the alert condition started because of this measurement.
h4hiee: If the alert condition ended because of this measurement.
h4his: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Sensor 4 Humidity Low Alert
h4lo: If there is an active sensor 4 humidity low alert condition.
h4lose: If the alert condition started because of this measurement.
h4loee: If the alert condition ended because of this measurement.
h4los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
ID12 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 22.2,
"h": 43.0,
"h3havg": 41.0,
"h24havg": 41.0,
"h7davg": 40.0,
"h30davg": 38.0
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
h: The measured humidity.
h3havg: Average humidity of the last 3 hours.
h24havg: Average humidity of the last 24 hours.
h7davg: Average humidity of the last 7 days.
h30davg: Average humidity of the last 30 days.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"hhi": true,
"hhise": true,
"hhiee": false,
"hhis": 40,

"hlo": false,
"hlose": false,
"hloee": false,
"hlos": 10,
"h3havghi": false,
"h3havghise": false,
"h3havghiee": false,
"h3havghis": 40,

"h3havglo": false,
"h3havglose": false,
"h3havgloee": false,
"h3havglos": 10,
"h3havgnsm": false,
"h3havgt": 480,
"h3havgtactive": false,
"h3havgr": 1,
"h24havghi": false,
"h24havghise": false,
"h24havghiee": false,
"h24havghis": 40,

"h24havglo": false,
"h24havglose": false,
"h24havgloee": false,
"h24havglos": 10,
"h24havgnsm": false,
"h24havgt": 480,
"h24havgtactive": false,
"h24havgr": 1,
"h7davghi": false,
"h7davghise": false,
"h7davghiee": false,
"h7davghis": 40,

"h7davglo": false,
"h7davglose": false,
"h7davgloee": false,
"h7davglos": 10,
"h7davgnsm": false,
"h7davgt": 480,
"h7davgtactive": false,
"h7davgr": 1,
"h30davghi": false,
"h30davghise": false,
"h30davghiee": false,
"h30davghis": 40,

"h30davglo": false,
"h30davglose": false,
"h30davgloee": false,
"h30davglos": 10,
"h30davgnsm": false,
"h30davgt": 480,
"h30davgtactive": false,
"h30davgr": 1
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active alert
condition.
Temperature Low Alert
t1lo: If there is an active cable sensor temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active cable sensor
low alert condition.
Humidity High Alert
hhi: If there is an active humidity high alert condition.
hhise: If the alert condition started because of this measurement.
hhiee: If an alert condition ended because of this measurement.
hhis: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Humidity Low Alert
hlo: If there is an active humidity high alert condition.
hlose: If the alert condition started because of this measurement.
hloee: If the alert condition ended because of this measurement.
hlos: The alert treshhold. Measurements above this treshhold have an active low alert
condition.
3 Hour Average Humidity Alert
h3havghi: If there is an active 3 hour average high alert condition.
h3havghise: If the alert condition started because of this measurement.
h3havghiee: If the alert condition ended because of this measurement.
h3havghis: The alert treshhold. Measurements above this treshhold have an active high
alert condition.
h3havglo: If there is an active 3 hour average low alert condition.
h3havglose: If the alert condition started because of this measurement.
h3havgloee: If the alert condition ended because of this measurement.
h3havglos: The alert treshhold. Measurements above this treshhold have an active low alert
condition.
h3havgnsm: If the alert is not triggered at saturday and sunday but on the following monday
instead.
h3havgt: The time of day in minutes when the alert will be triggered.
h3havgtactive: If the alert is activated.
h3havgr: The number of days after which the alert will be repeated.
24 Hour Average Humidity Alert
h24havghi: If there is an active 24 hour average high alert condition.
h24havghise: If the alert condition started because of this measurement.
h24havghiee: If the alert condition ended because of this measurement.
h24havghis: The alert treshhold. Measurements above this treshhold have an active high
alert condition.
h24havglo: If there is an active 24 hour average low alert condition.
h24havglose: If the alert condition started because of this measurement.
h24havgloee: If the alert condition ended because of this measurement.
h24havglos: The alert treshhold. Measurements above this treshhold have an active low
alert condition.
h24havgnsm: If the alert is not triggered at saturday and sunday but on the following
monday instead.
h24havgt: The time of day in minutes when the alert will be triggered.
h24havgtactive: If the alert is activated.
h24havgr: The number of days after which the alert will be repeated.
7 Days Average Humidity Alert
h7davghi: If there is an active 7 days average high alert condition.
h7davghise: If the alert condition started because of this measurement.
h7davghiee: If the alert condition ended because of this measurement.
h7davghis: The alert treshhold. Measurements above this treshhold have an active high
alert condition.
h7davglo: If there is an active 7 days average low alert condition.
h7davglose: If the alert condition started because of this measurement.
h7davgloee: If the alert condition ended because of this measurement.
h7davglos: The alert treshhold. Measurements above this treshhold have an active low alert
condition.
h7davgnsm: If the alert is not triggered at saturday and sunday but on the following monday
instead.
h7davgt: The time of day in minutes when the alert will be triggered.
h7davgtactive: If the alert is activated.
h7davgr: The number of days after which the alert will be repeated.
30 Days Average Humidity Alert
h30davghi: If there is an active 30 days average high alert condition.
h30davghise: If the alert condition started because of this measurement.
h30davghiee: If the alert condition ended because of this measurement.
h30davghis: The alert treshhold. Measurements above this treshhold have an active high
alert condition.
h30davglo: If there is an active 30 days average low alert condition.
h30davglose: If the alert condition started because of this measurement.
h30davgloee: If the alert condition ended because of this measurement.
h30davglos: The alert treshhold. Measurements above this treshhold have an active low
alert condition.
h30davgnsm: If the alert is not triggered at saturday and sunday but on the following
monday instead.
h30davgt: The time of day in minutes when the alert will be triggered.
h30davgtactive: If the alert is activated.
h30davgr: The number of days after which the alert will be repeated.
ID15 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"kp1t": 2,
"kp1c": 22,
"kp2t": 0,
"kp2c": 13,
"kp3t": 0,
"kp3c": 7,
"kp4t": 0,
"kp4c": 8,
"sc": true,
[Sensor type specific alert flags]
}
Each key has a type of key press value and a running counter. Key press type values are 0
for no key press, 1 for short key presses, 2 for double key presses and 3 for long key
presses. The running counter is increased for every key separately on each key press.
kp1t: The key press type.
kp1c: The running counter of key presses. kp2t: The key press type.
kp2c: The running counter of key presses. kp3t: The key press type.
kp3c: The running counter of key presses. kp4t: The key press type.
kp4c: The running counter of key presses.
sc: If the measurement occured because of a status change or if it is one of the repeating
status reports.
ID17 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 26.9,
"t2": 0.0,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
t2: If AC is on or off. On is encoded as 0.0, off is encoded as 1.0.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"t2hi": true,
"t2hise": true,
"t2hiee": true,
"t2his": 1.0,
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active alert
condition.
Temperature Low Alert
t1lo: If there is an active cable sensor temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active cable sensor
low alert condition.
Power Outage Alert
t2hi: If there is an active power outage alert condition.
t2hise: If the alert condition started because of this measurement.
t2hiee: If an alert condition ended because of this measurement.
t2his: Set to 1.0 if the power outage alert setting is activated. 0.0 otherwise.
ID18 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
"h": 53.8,
"ap": 1019.8,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
h: The measured humidity.
ap: The measured air pressure in hPa.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
"hhi": true,
"hhise": true,
"hhiee": false,
"hhis": 40,

"hlo": false,
"hlose": false,
"hloee": false,
"hlos": 10
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active alert
condition.
Temperature Low Alert
t1lo: If there is an active temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active low alert
condition.
Humidity High Alert
hhi: If there is an active humidity high alert condition.
hhise: If the alert condition started because of this measurement.
hhiee: If an alert condition ended because of this measurement.
hhis: The alert treshhold. Measurements above this treshhold have an active high alert
condition.
Humidity Low Alert
hlo: If there is an active humidity high alert condition.
hlose: If the alert condition started because of this measurement.
hloee: If the alert condition ended because of this measurement.
hlos: The alert treshhold. Measurements above this treshhold have an active low alert
condition.
Air Pressure Hi Alert
aphi: If there is an active air pressure high alert condition.
aphise: If the alert condition started because of this measurement.
aphiee: If the alert condition ended because of this measurement.
aphis: The alert treshhold. Measurements above this treshhold have an active alert
condition.
Air Pressure Low Alert
aplo: If there is an active air pressure low alert condition.
aplose: If the alert condition started because of this measurement.
aploee: If the alert condition ended because of this measurement.
aplos: The alert treshhold. Measurements below this treshhold have an active alert
condition.
Air Pressure Change Raising Alert
apcr: If there is an active air pressure change raising alert condition.
apcrse: If the alert condition started because of this measurement.
apcree: If the alert condition ended because of this measurement.
apcrdt: Timespan in hours (1-6) within the air pressure change must occur to trigger the
alert.
apcrt: The alert treshhold. Measurements above this treshhold in the specified time have an
active alert condition.
Air Pressure Change Negative Alert
apcf: If there is an active air pressure change falling alert condition.
apcfse: If the alert condition started because of this measurement.
apcfee: If the alert condition ended because of this measurement.
apcfdt: Timespan in hours (1-6) within the air pressure change must occur to trigger the
alert.
apcft: The alert treshhold. Measurements below this treshhold in the specified time have an
active alert condition.
ID20 measurement and alert properties
Measurement properties
"measurement": {
[General measurement properties]
"t1": 23.4,
[Sensor type specific alert flags]
}
t1: The measured temperature in celsius.
Alert flags
"measurement": {
[General measurement properties]
[Sensor type specific measurement properties]
"t1hi": true,
"t1hise": true,
"t1hiee": false,
"t1his": 20.0,
"t1lo": false,
"t1lose": false,
"t1loee": false,
"t1los": 0.0,
}
Temperature High Alert
t1hi: If there is an active temperature high alert condition.
t1hise: If the alert condition started because of this measurement.
t1hiee: If an alert condition ended because of this measurement.
t1his: The alert treshhold. Measurements above this treshhold have an active alert
condition.
Temperature Low Alert
t1lo: If there is an active cable sensor temperature low alert condition.
t1lose: If the alert condition started because of this measurement.
t1loee: If an alert condition ended because of this measurement.
t1los: The alert treshhold. Measurements below this treshhold have an active cable sensor
low alert condition.
