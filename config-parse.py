#!/usr/bin/env python3
import re

fn = input('Filename:')
#vscount = 0
cs_vip = {}
cs_pol = {}
cs_act = {}
srv = {}
vip = {}
svc = {}
svc_grp = {}

try:
    fw = open (fn + '_vs.md', 'w')
    # Start parsing
    for line in open(fn):
        temp = line.split(' ')

        if "add server" in line:
            srv[temp[2]] = temp[3].rstrip()

        if "add service " in line:
            svc[temp[2]] = {
                'server': temp[3],
                'protocol': temp[4],
                'port': temp[5]
            }

        if "add serviceGroup" in line:
            svc_grp[temp[2]] = {
                'protocol': temp[3],
                'servers': [],
            }

        if "add lb vserver" in line:
            vip[temp[3]] = {
                'protocol': temp[4],
                'ip': temp[5],
                'port': temp[6],
                'services': [],
                'appexpert': []
            }

        if "add cs vserver" in line:
            cs_vip[temp[3]] = {
                'protocol': temp[4],
                'ip': temp[5],
                'port': temp[6],
                'policies': [],
                'appexpert': [],
                'default': None
            }

        if "add cs action" in line:
            cs_act[temp[3]] = temp[5].rstrip()

        if "add cs policy " in line:
            target = line.split(' -action ', 1)[1].rstrip()
            temp2 = line.split(' -rule ', 1)[1]
            rule = temp2.split(' -action', 1)[0]
            cs_pol[temp[3]] = {}
            cs_pol[temp[3]] = {
                'expression': rule,
                'target': target
            }

        if "bind lb vserver" in line:
            if "-type" in line:
                vip[temp[3]]['appexpert'].append(temp[5].rstrip())
            else:
                vip[temp[3]]['services'].append(temp[4].rstrip())

        if "bind cs vserver" in line:
            if "-type" in line:
                cs_vip[temp[3]]['appexpert'].append(temp[5].rstrip())
            elif "-lbvserver" in line:
                cs_vip[temp[3]]['default'] = temp[5].rstrip()
            else:
                cs_vip[temp[3]]['policies'].append(temp[5].rstrip())
        
        if "bind serviceGroup" in line:
            if temp[3] != "-monitorName":
                svc_grp[temp[2]]['servers'].append(
                    {
                        'server': temp[3],
                        'port': temp[4].rstrip()
                    }
                )

    fw.write ('\r\n# Content Switching Virtual Servers')
    for csvs in cs_vip:
        fw.write ('\r\n## '+csvs+' ['+cs_vip[csvs]['ip']+':'+cs_vip[csvs]['port']+' '+cs_vip[csvs]['protocol']+'] \r\n')
        print(f'Content switching VS: {csvs}')
        fw.write ('### Policies \r\n')
        print(f'Policies: {cs_vip[csvs]["policies"]}')
        for pol in cs_vip[csvs]['policies']:
            print(pol)
            if cs_pol.get(pol, False):
                target = cs_pol[pol]['target']
                expr = cs_pol[pol]['expression']
                fw.write ('* POL: '+pol+'('+expr+') -> ACT: '+target+'\r\n')
                lbvip = cs_act[target]
                fw.write ('\t* LB_VIP: '+lbvip+' ['+vip.get(lbvip, {}).get('ip','-')+':'+vip.get(lbvip, {}).get('port','-')+' '+vip.get(lbvip,{}).get('protocol','-')+'] \r\n')
                for service in vip.get(lbvip, {}).get('services', []):
                    if service in svc:
                        server = svc[service].get('server','')
                        proto = svc[service].get('protocol','')
                        port = svc[service].get('port','')
                        name = srv[server]
                        fw.write ('\t\t* SVC: '+server+' - Server: '+name+' ['+proto+' '+port+']\r\n')
                    elif service in svc_grp:
                        print(f'SVC GRP: {svc_grp[service]}')
                        proto = svc_grp[service].get('protocol', '-')
                        fw.write ('\t\t* SVC_GRP: '+service+' - '+proto+'\r\n')
                        for server in svc_grp[service].get('servers', []):
                            port = server.get('port', '-')
                            server_name = server.get('server', None)
                            name = srv[server_name]
                            fw.write ('\t\t\t* Server: '+server_name+' - '+name+' ['+proto+' '+port+']\r\n')
        if cs_vip[csvs]['default'] is not None:
            lbvip = cs_vip[csvs]['default']
            print(f'DEFAULT: {lbvip}')
            fw.write ('\t* DEFAULT: '+lbvip+' ['+vip.get(lbvip, {}).get('ip','-')+':'+vip.get(lbvip, {}).get('port','-')+' '+vip.get(lbvip,{}).get('protocol','-')+'] \r\n')
            for service in vip.get(lbvip, {}).get('services', []):
                if service in svc:
                    server = svc[service].get('server','')
                    proto = svc[service].get('protocol','')
                    port = svc[service].get('port','')
                    name = srv[server]
                    fw.write ('\t\t* '+server+' - '+name+' ['+proto+' '+port+']\r\n')
                elif service in svc_grp:
                    proto = svc_grp[service].get('protocol', '-')
                    fw.write ('\t\t* SVC_GRP: '+service+' - '+proto+'\r\n')
                    for server in svc_grp[service].get('servers', []):
                        port = server.get('port', '-')
                        server_name = server.get('server', None)
                        name = srv[server_name]
                        fw.write ('\t\t\t* Server: '+server_name+' - '+name+' ['+proto+' '+port+']\r\n')
            
    fw.write ('\r\n# LoadBalancing Virtual Servers - Addressable')
    for lbvs in vip:
        print(lbvs)
        if not vip[lbvs]['ip'] == '0.0.0.0':
            fw.write ('\r\n## '+lbvs+' ['+vip[lbvs]['ip']+':'+vip[lbvs]['port']+' '+vip[lbvs]['protocol']+'] \r\n')
            fw.write ('### Services \r\n')
            for service in vip[lbvs].get('services', []):
                fw.write ('\t* '+service+'\r\n')
                if service in svc:
                    server = svc[service].get('server','')
                    proto = svc[service].get('protocol','')
                    port = svc[service].get('port','')
                    name = srv[server]
                    fw.write ('\t\t* SRV: '+server+' - Server: '+name+' ['+proto+' '+port+']\r\n')
                elif service in svc_grp:
                    proto = svc_grp[service].get('protocol', '-')
                    fw.write ('\t\t* SVC_GRP: '+service+' - '+proto+'\r\n')
                    for server in svc_grp[service].get('servers', []):
                        port = server.get('port', '-')
                        server_name = server.get('server', None)
                        name = srv[server_name]
                        fw.write ('\t\t\t* Server: '+server_name+' - '+name+' ['+proto+' '+port+']\r\n')

    fw.close()
except Exception as e:
    print(f'Exception {e}')
finally:
    fw.close()
