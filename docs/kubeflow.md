# Set up on Kubeflow

### What is Kubeflow?

[Kubeflow](https://www.kubeflow.org) is a free and open-source machine learning platform designed to enable using machine learning pipelines to orchestrate complicated workflows running on Kubernetes. 

In this method, you will install JupyterFlow on existing Kubeflow platform.

## Install Kubeflow

Refer to [kubeflow getting started page](https://www.kubeflow.org/docs/started/getting-started/) for installation.

## Configure Storage

You need a shared storage volume, such as NFS server(`ReadWriteMany` access mode), to make JupyterFlow get the same ML code written in Jupyter notebook. To do this, configure `singleuser.storage` property.
If you're unfamiliar with storage access mode, take a look at [Kubernetes persistent volume access mode](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes).

The simplest way to have a `ReadWriteMany` type storage is installing nfs-server-provisioner.

```bash
# StorageClass name will be nfs-server
helm install nfs-server stable/nfs-server-provisioner
```

Select `ReadWriteMany` access mode storage when launching your notebook server on Kubeflow Notebook Server.

## Expose Argo Workflow Web UI

You need to expose Argo web UI to see the result of `jupyterflow`. Unfortunately, JupyterFlow currently does not support Kubeflow Pipelines, so the result of `juypterflow` workflow does not appear in Kubeflow Pipelines web pages. You need to manually expose Argo Workflow web UI to check out the result.

The simplest way to expose Argo Workflow web UI is changing `argo-ui` Service to `LoadBalancer` type.

```bash
# Expose argo-ui Service as LoadBalancer type
kubectl patch svc argo-ui -p '{"spec": {"type": "LoadBalancer"}}' -n kubeflow
# service/argo-ui patched
```

And then change Argo UI deployment environment variable. To find out the reason, take a look at [Argo issue#1215](https://github.com/argoproj/argo-workflows/issues/1215)

```bash
# Change BASE_HREF env to /
kubectl set env deployment/argo-ui BASE_HREF=/ -n kubeflow
# deployment.apps/argo-ui env updated
```

Browse `<LOAD_BALANCER_IP>:80` to see Argo Workflow web UI is available. For detail configuration, refer to [https://argoproj.github.io/argo-workflows/argo-server/](https://argoproj.github.io/argo-workflows/argo-server)


## Grant Kubeflow notebook Service Account RBAC

Grant the service account used in Kubeflow notebook a role to create Argo Workflow objects. The default service account name in Kubeflow notebook is `default-editor`.

#### Options 1)

The simplest way to grant service account is to bind `cluster-admin` role. Assuming your Kubeflow namespace is `jupyterflow`, run

```bash
# binding cluster-admin role to jupyterflow:default-editor
kubectl create clusterrolebinding jupyterflow-admin \
                        --clusterrole=cluster-admin \
                        --serviceaccount=jupyterflow:default-editor
```

#### Options 2)

For more fine-grained Access Control, create Workflow Role in the namespace where Kubeflow is installed.

For example, create Workflow Role in `jupyterflow` namespace with following command.

```bash
cat << EOF | kubectl apply -n jupyterflow -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: workflow-role
rules:
# pod get/watch is used to identify the container IDs of the current pod
# pod patch is used to annotate the step's outputs back to controller (e.g. artifact location)
- apiGroups:
  - ""
  resources:
  - pods
  verbs:
  - get
  - watch
  - patch
  - list
# logs get/watch are used to get the pods logs for script outputs, and for log archival
- apiGroups:
  - ""
  resources:
  - pods/log
  verbs:
  - get
  - watch
- apiGroups:
  - "argoproj.io"
  resources:
  - workflows
  verbs:
  - get
  - watch
  - patch
  - list
  - create
EOF
```

Then, bind the Role with your service account. For example, bind `default-editor` service account with workflow role in `jupyterflow` namespace.

```bash
# binding workflow role to jupyterflow:default-editor
kubectl create rolebinding workflow-rb \
                      --role=workflow-role \
                      --serviceaccount=jupyterflow:default-editor \
                      --namespace jupyterflow
```

You might want to look at [https://argoproj.github.io/argo-workflows/service-accounts](https://argoproj.github.io/argo-workflows/service-accounts) for granting permissions.

## Install jupyterflow

Finally, launch a JupyterHub notebook server and install `jupyterflow` using pip.

In jupyter notebook Terminal, run

```bash
pip install jupyterflow
```
