import json
import subprocess

corednsConfig = subprocess.check_output(["kubectl", "get", "-n", "kube-system", "configmap/coredns", "-o", "yaml"]).decode('ascii')
print(corednsConfig)
if 'forward . 10.5.0.1' not in corednsConfig:
    raise ValueError("coredns config is wrong")

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
                ['dnsget', '-o', 'timeout:2', '-q', lookupName],
                capture_output=True)
            result = (r.stdout + r.stderr).decode('ascii').strip().replace('\n', '; ')
            print(f'looked up {lookupName} from pod on {runningOn} -> {result}')

finally:
    pass#subprocess.check_call(["skaffold", "delete"], cwd="/my/proj/infra/k8s_lookup/")