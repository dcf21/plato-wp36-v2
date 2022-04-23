#!/bin/bash

kubectl delete -f ../kubernetes_yaml/web-interface.yaml -n=plato
kubectl apply -f ../kubernetes_yaml/web-interface.yaml -n=plato
