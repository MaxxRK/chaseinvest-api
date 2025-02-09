import blpapi 
from datetime import datetime 
 
# Create a session 
session = blpapi.Session() 
if not session.start(): 
    print("Failed to start session.") 
    exit() 
 
if not session.openService("//blp/refdata"): 
    print("Failed to open service.") 
    exit() 
 
# Prepare the request 
service = session.getService("//blp/refdata") 
request = service.createRequest("HistoricalDataRequest") 
 
# Add securities and fields to the request 
request.append("securities", "AAPL US Equity")  # Example: Apple Inc. 
request.append("fields", "PX_LAST")  # Last price 
request.set("startDate", "2022-01-01") 
request.set("endDate", datetime.now().strftime("%Y-%m-%d")) 
request.set("periodicitySelection", "DAILY") 
 
# Send the request 
session.sendRequest(request) 
 
# Process the response 
while True: 
    ev = session.nextEvent() 
    for msg in ev: 
        if msg.hasElement("responseError"): 
            print("Error:", msg.getElement("responseError")) 
        elif msg.hasElement("securityData"): 
            data = msg.getElement("securityData") 
            for i in range(data.numValues()): 
                security = data.getValueAsElement(i) 
                print(security) 
    if ev.eventType() == blpapi.Event.RESPONSE: 
        break 