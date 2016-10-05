from senderbase import SenderBase
from termcolor import colored
import requests

from dnsbl import Base
from providers import BASE_PROVIDERS
from solutions import TO_DELIST

from lxml import html


sb = SenderBase(timeout=30)
out = ''

#check_ip = ["mx0%s.telecomitalia.it" % x for x in range(1,8)]
check_ip = ['217.169.121.10', '217.169.121.22']


## Trend Micro
def trendmicro_test(ip):
    URL="https://ers.trendmicro.com/reputations/index?ip_address=%s" % ip

    page = requests.get(URL)
    tree = html.fromstring(page.content)

    reputation = tree.xpath('//dd[@class="reputationValue"]/text()')
    if len(reputation) > 0:
        reputation.append('https://ers.trendmicro.com/reputations/block/%s/DUL' % ip)
        return reputation
    else:
        return ['Good']


def reputation(rep):
    if rep == 'Good':
        return colored(rep, 'green')
    if rep == 'Neutral':
        return colored(rep, 'yellow')
    if rep == 'Poor':
        return colored(rep, 'red')
    if rep == 'Bad':
        return colored(rep, 'red')
    else:
        return rep


def bl(it):
    if it == False:
        return colored(it, 'green')
    if it == True:
        return colored(it, 'red')
        
    
def dnsbl_check(ip):
    backend = Base(ip=ip, providers=BASE_PROVIDERS)
    return backend.check()

def dnsbl_filter(dnsbl):
    dnsbl_list = []
    for ck in dnsbl:
        if ck[1] == False or ck[1] == None:
            pass
        else:
            dnsbl_list.append(ck[0])
    return dnsbl_list

def p_out(txt):
    global out
    print(txt)
    out += str(txt) + "\n"

for ip in check_ip:
    sb_out = sb.lookup(ip)
    dnsbl_l = dnsbl_filter(dnsbl_check(ip))
    ip_info = requests.get('http://ipinfo.io/%s' % ip)
    trend_micro = trendmicro_test(ip)
    EMAIL = 0

    p_out(' ')

    ## Info generiche
    p_out(colored(ip,'cyan'))
    p_out(' HostName: %s' % ip_info.json()['hostname'])
    p_out(' Provider: %s' % ip_info.json()['org'])

    # Info Sender Base
    p_out(' Black List: %s' %  bl(sb_out['black_listed']))
    if sb_out['black_listed'] == True:
        EMAIL = 1
        p_out(sb_out['blacklists'])

    p_out(' Reputation: %s' % reputation(sb_out['email_reputation']))
    p_out(' Eml Volume: %s' % sb_out['email_volume'])
    p_out(' Chg Volume: %s' % sb_out['volume_change'])
    if sb_out['fwd_rev_dns_match'] == 'Yes':
        p_out(' FW Rev DNS: %s' % colored(sb_out['fwd_rev_dns_match'],'green'))
    else:
        p_out(' FW Rev DNS: %s' % colored(sb_out['fwd_rev_dns_match'],'red'))
        EMAIL = 1
    
    # Trend Micro
    p_out(' Trend Micro Test: %s' % reputation(trend_micro[0]))

    # Soluzioni:
    if len(trend_micro) > 1:
        p_out('  Per delistare: %s' % trend_micro[1])

    # Info dnsbl_check
    if len(dnsbl_l) > 0:
        p_out(' DNSBL: %s -> %s' % (colored('KO','red'),dnsbl_l))
        EMAIL = 1
        p_out(colored(' Soluzioni:','magenta'))
    else:
        p_out(' DNSBL: %s' % colored('OK','green'))

    # Soluzioni:
    for D in dnsbl_l:
        if D in TO_DELIST.keys():
            p_out( '  Per delistare da %s: %s' % (colored(D,'red'), TO_DELIST[D].replace('__IP__',ip)))

    if EMAIL > 0:
        p_out("\n\n * * * * inviare email per l'ip %s * * * *" % ip)

#print out
