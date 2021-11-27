"""
<pod 내부에서 파일에 저장된 인증 정보는 아래와 같은 파일에 디폴트로 존재>
* API 서버: https://kubernetes.default로 고정되어 있다
* token: /var/run/secrets/kubernetes.io/serviceaccount/token에 저장되어 있다
* cert: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt에 저장되어 있다

<쿠버네티스 api 참고 예제>
https://github.com/kubernetes-client/python/tree/master/examples
https://github.com/kubernetes-client/python/blob/master/kubernetes/README.md # api_client 내에 쓸 수 있는 코드들
https://github.com/kubernetes-client/python/blob/master/examples/pod_config_list.py # config 파일 출력인데, 오류가 있어서 보류
https://stackoverflow.com/questions/69170404/using-the-python-kubernetes-api-is-there-a-way-to-list-secrets-in-my-current-n # secret 관련 설명

## 필요할 것 같은 엔진들로 모아 놨으며, 아직까지 해당 정보를 db에서 어떻게 넣을 지 감을 못잡아서 제대로 def로 나눠 놓지는 못했습니다. 
## 아래 2가지 방법으로 exception처리 한게 있는데, 솔직히 아직까지 쿠버네티스의 경우 로거에 보내는 게 더 헷갈리지 않을까 싶어서 두가지 유형 전부 썼습니다.
## 시크릿은 옵션으로만 넣어서 필요 할때만 출력하게 해야 할지..
"""

import ssl
import os
import kubernetes
from kubernetes import client
from kubernetes import config
from kubernetes import watch
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from log.dagda_logger import DagdaLogger
from exception.dagda_error import DagdaError

class KubernetesDriver:
    def pod_and_namspace_info(self):
        try:
            # 기본적인 연결 정보
            config = client.Configuration()

            config.api_key['authorization'] = open('/var/run/secrets/kubernetes.io/serviceaccount/token').read()
            config.api_key_prefix['authorization'] = 'Bearer'
            config.host = 'https://kubernetes.default'
            config.ssl_ca_cert = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
            config.verify_ssl=False

            # api_client는 위에서 연결한 정보를 바탕으로 통신할 클라이언트
            api_client = client.CoreV1Api(client.ApiClient(config))

            # namespace list 중 " "부분에 원하는 namespace 넣고 pod 출력
            ret = api_client.list_namespaced_pod("default", watch=False)

            print("Listing pods with their IPs:")

            for i in ret.items:
	            print(f"{i.status.pod_ip}\t{i.metadata.name}") # i.metadata.namespace == namespace 가져 와라

            # kubectl exec [pod name] -- sh
            my_command = ['sh']

            response = stream(api_client.connect_get_namespaced_pod_exec,
                  'pod name',
                  'namespace',
                 command=my_command,
                 stdin=False,
                 stderr=True,
                 stdout=True,
                 tty=False)

            print(response)

        except ApiException as e:               
            # 연결 오류
            # pod나 namespace 오류
            DagdaLogger.get_logger().error('Kubernetes 연결 오류!!!! Pod, Namespace 부터 확인 해주세요!!!')

    def secret_list_and_namespace(self):
        # secret 리스트 검색 및 해당 네임 출력
        config.load_kube_config()
        v1 = client.CoreV1Api()

        k = v1.list_namespaced_secret(str(os.environ.get("[MY_POD_NAMESPACE]")))  # list_secret_for_all_namespaces => 전체 시크릿 리스트 출력 
        for i in k.items:
            print(i.metadata.name)

    """
    [kube_config 리스트 출력 예제, return에 넣은 fuction이 필요하다고 하는데, 이해가 안됨.]
    contexts, active_context = config.list_kube_config_contexts()

    if not contexts:
        print("Cannot find any context in kube-config file.")
        return

    contexts = [context['name'] for context in contexts]
    active_index = contexts.index(active_context['name'])
    option, _ = pick(contexts, title="Pick the context to load", default_index=active_index)
    # Configs can be set in Configuration class directly or using helper
    # utility
    config.load_kube_config(context=option)

    print("Active host is %s" % configuration.Configuration().host)
    """


    # 팔콘 이벤트 로그와 겹치는 부분이 아닐까 싶음.
    def take_log(self):
        # log 가져오기
        config.load_kube_config()
        pod_name = "[pod_name]"
        try:
            api_instance = client.CoreV1Api()
            api_response = api_instance.read_namespaced_pod_log(name=pod_name, namespace='default')         
            # read_namespaced_pod_log 대신 read_namespaced_pod 으로 만 고치면 "kubectl describe pods [pod_name]"
            print(api_response)
        except ApiException as e:
            print('Found exception in reading the logs')


"""
# pod, namespace watch & timeout 추가 => exec 실행 없이 watch 라이브러리 추가 해서 출력
	# Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.

    config.load_kube_config()

    v1 = client.CoreV1Api()
    count = 10
    w = watch.Watch()
    for event in w.stream(v1.list_namespace, timeout_seconds=10):
        print("Event: %s %s" % (event['type'], event['object'].metadata.name))
        count -= 1
        if not count:
            w.stop()
    print("Finished namespace stream.")

    for event in w.stream(v1.list_pod_for_all_namespaces, timeout_seconds=10):
        print("Event: %s %s %s" % (
            event['type'],
            event['object'].kind,
            event['object'].metadata.name)
        )
        count -= 1
        if not count:
            w.stop()
    print("Finished pod stream.")

"""