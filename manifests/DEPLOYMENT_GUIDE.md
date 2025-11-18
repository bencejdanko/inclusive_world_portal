# Deployment Guide for Inclusive World Portal

This guide provides step-by-step instructions for deploying the Inclusive World Portal using ArgoCD and Kubernetes.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Building and Pushing Docker Images](#building-and-pushing-docker-images)
4. [Configuring Secrets](#configuring-secrets)
5. [Deploying with ArgoCD](#deploying-with-argocd)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **kubectl** (v1.24+)
- **kustomize** (v4.5+)
- **Docker** (v20.10+)
- **ArgoCD CLI** (v2.5+)
- **Git**

### Kubernetes Cluster Requirements

- Kubernetes v1.24+
- Storage provisioner with support for:
  - RWO (ReadWriteOnce) for databases
  - RWX (ReadWriteMany) for shared volumes
- Ingress controller (nginx-ingress recommended)
- cert-manager (for TLS certificates)
- Metrics server (for HPA)

### Access Requirements

- Container registry access (Docker Hub, GHCR, ECR, etc.)
- Git repository access
- Kubernetes cluster admin access
- ArgoCD instance deployed

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/inclusive_world_portal.git
cd inclusive_world_portal
```

### 2. Install ArgoCD (if not already installed)

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s \
  deployment/argocd-server -n argocd

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

### 3. Login to ArgoCD

```bash
# Login via CLI
argocd login localhost:8080 --insecure

# Change admin password
argocd account update-password
```

## Building and Pushing Docker Images

### Option 1: Docker Hub

```bash
# Set your Docker Hub username
export DOCKER_USERNAME="your-username"
export IMAGE_TAG="v1.0.0"

# Login to Docker Hub
docker login

# Build the production image
docker build \
  --target production \
  -t ${DOCKER_USERNAME}/inclusive-world-portal:${IMAGE_TAG} \
  -t ${DOCKER_USERNAME}/inclusive-world-portal:latest \
  .

# Push to Docker Hub
docker push ${DOCKER_USERNAME}/inclusive-world-portal:${IMAGE_TAG}
docker push ${DOCKER_USERNAME}/inclusive-world-portal:latest

# Update image references in manifests
cd manifests/base
# Edit django/deployment.yaml, celery/worker-deployment.yaml, celery/beat-deployment.yaml
# Replace "your-registry/inclusive-world-portal" with "${DOCKER_USERNAME}/inclusive-world-portal"
```

### Option 2: GitHub Container Registry (GHCR)

```bash
# Set variables
export GITHUB_USERNAME="your-username"
export GITHUB_TOKEN="your-github-token"
export IMAGE_TAG="v1.0.0"

# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# Build and tag
docker build \
  --target production \
  -t ghcr.io/${GITHUB_USERNAME}/inclusive-world-portal:${IMAGE_TAG} \
  -t ghcr.io/${GITHUB_USERNAME}/inclusive-world-portal:latest \
  .

# Push to GHCR
docker push ghcr.io/${GITHUB_USERNAME}/inclusive-world-portal:${IMAGE_TAG}
docker push ghcr.io/${GITHUB_USERNAME}/inclusive-world-portal:latest

# Update manifests accordingly
```

### Option 3: AWS ECR

```bash
# Set variables
export AWS_ACCOUNT_ID="123456789012"
export AWS_REGION="us-east-1"
export IMAGE_TAG="v1.0.0"

# Create ECR repository (first time only)
aws ecr create-repository \
  --repository-name inclusive-world-portal \
  --region $AWS_REGION

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build and tag
docker build \
  --target production \
  -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/inclusive-world-portal:${IMAGE_TAG} \
  -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/inclusive-world-portal:latest \
  .

# Push to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/inclusive-world-portal:${IMAGE_TAG}
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/inclusive-world-portal:latest

# Update manifests accordingly
```

### Update Kustomization Files

After pushing images, update the image references in:

```bash
# Update base kustomization
nano manifests/base/kustomization.yaml
# Change "your-registry/inclusive-world-portal" to your actual registry

# Update environment overlays
nano manifests/overlays/dev/kustomization.yaml
nano manifests/overlays/staging/kustomization.yaml
nano manifests/overlays/production/kustomization.yaml
# Update image tags appropriately
```

## Configuring Secrets

### 1. Generate Django Secret Key

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 2. Create Secrets for Development

```bash
# Create namespace first
kubectl create namespace inclusive-world-portal-dev

# Create secrets
kubectl create secret generic inclusive-world-secrets \
  --namespace=inclusive-world-portal-dev \
  --from-literal=DJANGO_SECRET_KEY='your-generated-secret-key' \
  --from-literal=POSTGRES_PASSWORD='dev-postgres-password' \
  --from-literal=MINIO_ROOT_USER='minioadmin' \
  --from-literal=MINIO_ROOT_PASSWORD='minioadmin123' \
  --from-literal=AWS_ACCESS_KEY_ID='minioadmin' \
  --from-literal=AWS_SECRET_ACCESS_KEY='minioadmin123' \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 3. Create Secrets for Production

For production, use a secure secret management solution:

#### Option A: Sealed Secrets

```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create sealed secret
kubectl create secret generic inclusive-world-secrets \
  --namespace=inclusive-world-portal \
  --from-literal=DJANGO_SECRET_KEY='prod-secret-key' \
  --from-literal=POSTGRES_PASSWORD='strong-prod-password' \
  --from-literal=MINIO_ROOT_PASSWORD='strong-minio-password' \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > manifests/overlays/production/sealed-secret.yaml
```

#### Option B: External Secrets Operator

```bash
# Install external-secrets operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace

# Create SecretStore and ExternalSecret manifests
# See: https://external-secrets.io/
```

#### Option C: Manual Creation

```bash
# Create production namespace
kubectl create namespace inclusive-world-portal

# Create production secrets (store these values securely!)
kubectl create secret generic inclusive-world-secrets \
  --namespace=inclusive-world-portal \
  --from-literal=DJANGO_SECRET_KEY='STRONG-PRODUCTION-SECRET-KEY' \
  --from-literal=POSTGRES_PASSWORD='STRONG-POSTGRES-PASSWORD' \
  --from-literal=MINIO_ROOT_USER='admin' \
  --from-literal=MINIO_ROOT_PASSWORD='STRONG-MINIO-PASSWORD' \
  --from-literal=AWS_ACCESS_KEY_ID='admin' \
  --from-literal=AWS_SECRET_ACCESS_KEY='STRONG-MINIO-PASSWORD'
```

## Deploying with ArgoCD

### 1. Add Git Repository to ArgoCD

```bash
# Via CLI
argocd repo add https://github.com/your-org/inclusive_world_portal.git \
  --username your-username \
  --password your-token

# Or via UI: Settings > Repositories > Connect Repo
```

### 2. Create AppProject (Optional)

```bash
kubectl apply -f manifests/argocd/appproject.yaml
```

### 3. Deploy Development Environment

```bash
# Update the repo URL in the manifest
nano manifests/argocd/app-dev.yaml
# Change "https://github.com/your-org/inclusive_world_portal.git"

# Apply the Application
kubectl apply -f manifests/argocd/app-dev.yaml

# Wait for sync
argocd app wait inclusive-world-portal-dev --health
```

### 4. Deploy Staging Environment

```bash
# Update repo URL
nano manifests/argocd/app-staging.yaml

# Apply
kubectl apply -f manifests/argocd/app-staging.yaml

# Sync
argocd app sync inclusive-world-portal-staging
argocd app wait inclusive-world-portal-staging --health
```

### 5. Deploy Production Environment

```bash
# Update repo URL and image tags
nano manifests/argocd/app-production.yaml
nano manifests/overlays/production/kustomization.yaml

# Apply
kubectl apply -f manifests/argocd/app-production.yaml

# Manual sync for production (recommended)
argocd app sync inclusive-world-portal-production
argocd app wait inclusive-world-portal-production --health
```

## Verification

### 1. Check Application Status

```bash
# Via CLI
argocd app get inclusive-world-portal-dev
argocd app get inclusive-world-portal-staging
argocd app get inclusive-world-portal-production

# Via UI: https://argocd.example.com
```

### 2. Check Pod Status

```bash
# Development
kubectl get pods -n inclusive-world-portal-dev

# Production
kubectl get pods -n inclusive-world-portal

# Check logs
kubectl logs -f deployment/prod-django -n inclusive-world-portal
```

### 3. Check Services and Ingress

```bash
# Check services
kubectl get svc -n inclusive-world-portal

# Check ingress
kubectl get ingress -n inclusive-world-portal

# Test connectivity
curl -I https://inclusive-world-portal.com
```

### 4. Run Django Migrations

```bash
# If migrations didn't run automatically
kubectl exec -it deployment/prod-django -n inclusive-world-portal -- \
  python manage.py migrate
```

### 5. Create Superuser

```bash
kubectl exec -it deployment/prod-django -n inclusive-world-portal -- \
  python manage.py createsuperuser
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Check logs
kubectl logs <pod-name> -n <namespace>

# Check resource quotas
kubectl describe resourcequota -n <namespace>
```

### Database Connection Issues

```bash
# Check PostgreSQL pod
kubectl logs statefulset/postgres -n <namespace>

# Test connection from Django pod
kubectl exec -it deployment/prod-django -n <namespace> -- \
  python manage.py dbshell
```

### Image Pull Errors

```bash
# Check image pull secrets
kubectl get secrets -n <namespace>

# Create image pull secret if needed
kubectl create secret docker-registry regcred \
  --docker-server=<your-registry-server> \
  --docker-username=<your-username> \
  --docker-password=<your-password> \
  --namespace=<namespace>

# Update deployments to use the secret
# Add imagePullSecrets to pod spec
```

### Storage Issues

```bash
# Check PVCs
kubectl get pvc -n <namespace>

# Check storage classes
kubectl get storageclass

# Describe PVC for issues
kubectl describe pvc <pvc-name> -n <namespace>
```

### ArgoCD Sync Issues

```bash
# Check sync status
argocd app get <app-name>

# View sync logs
argocd app logs <app-name>

# Force refresh
argocd app get <app-name> --refresh

# Hard refresh
argocd app get <app-name> --hard-refresh
```

### Network Policy Issues

```bash
# Temporarily disable network policies for debugging
kubectl delete networkpolicy --all -n <namespace>

# Test connectivity
kubectl exec -it <pod-name> -n <namespace> -- curl <service-url>
```

## Rollback

### Rollback via ArgoCD

```bash
# List history
argocd app history inclusive-world-portal-production

# Rollback to specific revision
argocd app rollback inclusive-world-portal-production <revision-id>
```

### Rollback via Kubectl

```bash
# Rollback deployment
kubectl rollout undo deployment/prod-django -n inclusive-world-portal

# Check rollout status
kubectl rollout status deployment/prod-django -n inclusive-world-portal
```

## Updating the Application

### Update Image Tag

```bash
# Update image tag in kustomization
cd manifests/overlays/production
kustomize edit set image \
  your-registry/inclusive-world-portal=your-registry/inclusive-world-portal:v1.1.0

# Commit and push
git add .
git commit -m "Update to v1.1.0"
git push

# ArgoCD will auto-sync or manually sync
argocd app sync inclusive-world-portal-production
```

### Update Configuration

```bash
# Edit configmap or secrets
kubectl edit configmap inclusive-world-config -n inclusive-world-portal

# Restart deployments to pick up changes
kubectl rollout restart deployment/prod-django -n inclusive-world-portal
kubectl rollout restart deployment/prod-celeryworker -n inclusive-world-portal
```

## Monitoring and Observability

### Access Application Logs

```bash
# Django logs
kubectl logs -f deployment/prod-django -n inclusive-world-portal

# Celery worker logs
kubectl logs -f deployment/prod-celeryworker -n inclusive-world-portal

# All pods in namespace
kubectl logs -f -l app.kubernetes.io/name=inclusive-world-portal -n inclusive-world-portal
```

### Check Resource Usage

```bash
# Pod resource usage
kubectl top pods -n inclusive-world-portal

# Node resource usage
kubectl top nodes
```

### Access Django Shell

```bash
kubectl exec -it deployment/prod-django -n inclusive-world-portal -- \
  python manage.py shell
```

## Security Best Practices

1. **Never commit secrets to Git**
2. **Use sealed-secrets or external-secrets in production**
3. **Enable Network Policies**
4. **Use Pod Security Standards**
5. **Regular security scanning of images**
6. **Keep dependencies updated**
7. **Use RBAC for access control**
8. **Enable audit logging**
9. **Use TLS for all external traffic**
10. **Regular backup of databases**

## Backup and Restore

### Backup PostgreSQL

```bash
# Create backup
kubectl exec statefulset/postgres -n inclusive-world-portal -- \
  pg_dump -U postgres inclusive_world_portal > backup.sql

# Or use a backup job
# See: https://github.com/prodrigestivill/docker-postgres-backup-local
```

### Restore PostgreSQL

```bash
# Restore from backup
kubectl exec -i statefulset/postgres -n inclusive-world-portal -- \
  psql -U postgres inclusive_world_portal < backup.sql
```

## Support

For issues or questions:
- Check the troubleshooting section above
- Review ArgoCD documentation
- Review Kubernetes documentation
- Contact the platform team
