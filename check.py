import requests
import secrets
from threading import Thread
from tqdm import tqdm


def make_request_id():
    part1 = secrets.token_hex(16)
    part2 = secrets.token_hex(8)
    return f"|{part1}.{part2}"


def get_aloc(address, proxy):
    try:
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "clq-app-id": "0g",
            "clq-jwt": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOiI2OGM5OWMyOTEwYjBmNWM1Nzc3Njc5ZjQiLCJleHAiOjE3NTgwNTAzNzc2MTl9.g1k04dnb3qb67JXzk0_sxUU_hh31fzxeucMYCeGaBj0",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-kl-saas-ajax-request": "Ajax_Request",
            "referer": "https://airdrop.0gfoundation.ai/flow"
        }
        proxies = {
            "http":proxy,
            "https": proxy
        }

        url = "https://airdrop.0gfoundation.ai/api/eligibility"
        params = {
            "walletAddresses": f"{address}"
        }

        rid = make_request_id()

        headers['request-id']=f"|{rid}"
        headers['traceparent']=f"00-{rid}-01"

        response = requests.get(url, headers=headers, params=params, proxies = proxies, timeout=5)

#        print(response.status_code)
#        print(response.json())
        aloc = response.json()['total']
        return aloc
    except Exception as err:
        return "ERROR"


with open("addresslist", "r") as f:
    addresslst = [row.strip() for row in f]

with open("proxylist", "r") as f:
    proxylist = [row.strip() for row in f]

if len(addresslst) == 0:
    print(f"ERROR: Файл addresslist не заполенен")
    exit(0)

if len(proxylist) == 0:
    print(f"ERROR: Файл proxylist  не заполенен")
    exit(0)

if len(proxylist) != 1 and len(addresslst) != len(proxylist):
    print(f"ERROR: Кол-во адресов ({len(addresslst)}) не совпадает с кол-вом прокси ({len(proxylist)})")
    exit(0)

if len(proxylist) == 1:
    proxy = proxylist[0]
    print(f"Указан лишь один прокси - использую его для всех кошельков")
    for i in range(len(addresslst)):
        proxylist.append(proxy)


elig_c = 0
total_aloc = 0
def check(address, proxy):
    global elig_c, total_aloc
#    print(f"[{i}] Проверяю {address} | {proxy}")
    aloc = get_aloc(address, proxy)
    trc=1
    while aloc == "ERROR" and trc < 3:
        aloc = get_aloc(address, proxy)
        trc+=1
    if aloc != "ERROR":
        if int(aloc) > 0:
            elig_c+=1
        total_aloc +=int(aloc)
 #   print(f"[{i}] {address} | {aloc}")
    res_str = f"{address};{aloc}\n"
    with open(f'0g_checkres.csv', "a") as f:
        f.write(res_str)


threads = []

for i, address in enumerate(addresslst):
    thname = f"{i}"
    th = Thread(target=check, args=(address, proxylist[i]), name=thname)
    threads.append(th)


st_threads = []
st = 0
for th in tqdm(threads):
    th.start()
    st_threads.append(th)
    st+=1
    if st == 1000:
        st = 0
        for stth in st_threads:
            stth.join()


for th in threads:
    th.join()

print(f"{elig_c} адресов Eligible, Тотал алока: {total_aloc}")
print(f"Данные сохранены в файл 0g_checkres.csv")
