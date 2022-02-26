#!/bin/bash

for item in ../kubernetes_yaml/*.yaml
do
    kubectl delete -f $item
done

