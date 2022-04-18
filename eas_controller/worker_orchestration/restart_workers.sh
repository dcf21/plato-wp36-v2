#!/bin/bash

kubectl delete -f ../kubernetes_yaml/eas-debugging.yaml -n=plato
kubectl apply -f ../kubernetes_yaml/eas-debugging.yaml -n=plato
