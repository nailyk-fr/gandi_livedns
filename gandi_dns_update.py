import json
import requests
import socket
import sys
## import config file :
import dns_config

headers = {"Authorization": "Bearer " + dns_config.dns_api_key}
url = "{0}/livedns/domains/{1}/records/{2}".format(dns_config.dns_api_url, dns_config.domain_name, dns_config.domain_record_name)

debug = False
nocolor = False

class bcolors:
    if not nocolor:
       OKCYAN = '\033[96m'
       OKGREEN = '\033[92m'
       WARNING = '\033[93m'
       FAIL = '\033[91m'
       ENDC = '\033[0m'
    else:
       OKCYAN = ''
       OKGREEN = ''
       WARNING = ''
       FAIL = ''
       ENDC = ''

def dbg_print(text):
    if debug:
        print(bcolors.OKCYAN + text + bcolors.ENDC)

def info_print(text):
    print(bcolors.OKGREEN + text + bcolors.ENDC)

def warn_print(text):
    print(bcolors.WARNING + text + bcolors.ENDC)

def err_print(text):
    print(bcolors.FAIL + text + bcolors.ENDC, file=sys.stderr)

def get_external_ip():
    try: 
        r = requests.get(dns_config.ip_get_url)
        if r.status_code == 200:
            response = r.text
        try:
            socket.inet_aton(response)
            # legal
            return response
        except socket.error:
            # Not legal
            return False
        return False

    except requests.exceptions.RequestException:
        print('Opnsense: HTTP Request failed')

def get_current_record():
    try: 
        # https://api.gandi.net/v5/domain/domains/{domain}/hosts/{name}
        dbg_print("url: {0} and headers : {1}".format(url, headers))
        r = requests.get(url, headers=headers)
        dbg_print(r.text)
        if r.status_code != 200:
            err_print("Non 200 answer: {0}".format(str(r.status_code)))
            err_print("Cannot proceed, exiting")
            sys.exit(1)
        else:
            dbg_print("Status {0}, parsing answer".format(str(r.status_code)))
        r_json = json.loads(r.text)
        cur_ttl = r_json[0]['rrset_ttl']
        cur_ip = r_json[0]['rrset_values'][0]
        http_ref = r_json[0]['rrset_href']
        dbg_print("ttl: {0}, IP: {1}".format(cur_ttl, cur_ip))
        return cur_ttl, cur_ip, http_ref
    except requests.exceptions.RequestException:
        err_print("An error occured")
        return False

def set_ip(http, ttl, ip):
    try:
        response = requests.put(
            url = http,
            headers = {**headers, 
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "rrset_values": ip,
                "rrset_ttl": ttl
            })
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
    except requests.exceptions.RequestException:
        print('dns: HTTP Request failed')
        sys.exit(1)

cur_ttl, cur_ip, http_ref = get_current_record()

new_ip = get_external_ip()

if cur_ip != new_ip:
  warn_print("Ip changed, from {0} to {1}. Updating...".format(cur_ip, new_ip))
  set_ip(http_ref, dns_config.min_ttl, new_ip.split())
else:
  info_print("No IP change")

info_print("All done.")
sys.exit(0)

