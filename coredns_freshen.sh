#!/bin/zsh
kubectl apply -f templates/kube/coredns.yaml
kubectl get -n kube-system configmap/coredns -o yaml 
