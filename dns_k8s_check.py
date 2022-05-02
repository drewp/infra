import json
import subprocess

subprocess.check_call(["skaffold", "run"], cwd="/my/proj/infra/k8s_lookup/")

try:
    j = subprocess.check_output(['kubectl', 'get', 'pod', '-o', 'json', '--selector', 'name=k8s-lookup'])
    pods = json.loads(j)['items']
    for lookupName in [
            'bang',
            'bang.bigasterisk.com',
            'bang.bigasterisk.com.',
            'mongodb.default.svc.cluster.local',
            'mongodb.default.svc.cluster.local.',
    ]:
        for pod in pods:
            runningOn = pod['spec']['nodeName']
            podName = pod['metadata']['name']

            r = subprocess.run(
                ['kubectl', 'exec', f'pod/{podName}'] + ['--'] +  #
                ['dnsget', '-q', lookupName],
                capture_output=True)
            result = (r.stdout + r.stderr).decode('ascii').strip().replace('\n', '; ')
            print(f'looked up {lookupName} from pod on {runningOn} -> {result}')

finally:
    subprocess.check_call(["skaffold", "delete"], cwd="/my/proj/infra/k8s_lookup/")