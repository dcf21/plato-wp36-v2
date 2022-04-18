#!/bin/bash

kubectl delete -f ../kubernetes_yaml/eas-debugging.yaml
kubectl apply -f ../kubernetes_yaml/eas-debugging.yaml

