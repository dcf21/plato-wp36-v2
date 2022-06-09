#!/bin/bash

# Open a bash terminal within the first running worker node within the Kubernetes 'plato' namespace

kubectl exec -it -n=plato \
 `kubectl get pods -n=plato --field-selector="status.phase=Running" --no-headers -o custom-columns=":metadata.name" \
  | grep "eas-worker-" | head -n 1` -- /bin/bash
