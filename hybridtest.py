from chase.session import ChaseSession

chase = ChaseSession(title="maxxrk", headless=False)
chase.login("mustang19r", "!M2vjtgpx2R!D", "4374")


# no at_check,
print(chase.session.cookies.get_dict())
chase.session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "sec-ch-ua-arch": "x86",
        "content-type": "application/json",
        "accept": "application/json, text/plain, */*",
        "sec-ch-ua-platform-version": "15.0.0",
        "origin": "https://secure.chase.com",
    }
)
data = {"filterOption": "ALL"}
response = chase.session.post(
    url="https://secure.chase.com/svc/rr/accounts/secure/v2/portfolio/account/options/list",
    data=data,
)
print(response)
print(response.text)
data = {
    "currencyCode": "",
    "intradayUpdateIndicator": True,
    "selectorCode": "ACCOUNT_GROUP",
    "selectorIdentifier": "group-cwm-investment-",
    "taxLotIndicator": False,
    "voluntaryCorporateActionIndicator": False,
}
response = chase.session.post(
    url="https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-investment-positions/v1/positions",
    json=data,
)
print(response)
print(response.text)
