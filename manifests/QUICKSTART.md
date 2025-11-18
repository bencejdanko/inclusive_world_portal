# Quick Start Guide

Get your Inclusive World Portal deployed in minutes!

## 🚀 Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker Hub account (or any container registry)
- ArgoCD installed

## 📋 5-Minute Deployment

### Step 1: Build and Push Image (3 minutes)

```bash
# Login to Docker Hub
docker login

# Build and push (replace YOUR_USERNAME)
export DOCKER_USERNAME="your-dockerhub-username"
docker build -t ${DOCKER_USERNAME}/inclusive-world-portal:latest --target production .
docker push ${DOCKER_USERNAME}/inclusive-world-portal:latest
```

### Step 2: Update Manifests (1 minute)

```bash
# Update image references
cd manifests/base
find . -type f -name "*.yaml" -exec sed -i \
  "s|your-registry/inclusive-world-portal|${DOCKER_USERNAME}/inclusive-world-portal|g" {} +

# Update kustomization
sed -i "s|your-registry/inclusive-world-portal|${DOCKER_USERNAME}/inclusive-world-portal|g" kustomization.yaml

# Commit changes
git add .
git commit -m "Update image references"
git push
```

### Step 3: Create Secrets (1 minute)

```bash
# Create namespace
kubectl create namespace inclusive-world-portal-dev

# Generate Django secret key
export DJANGO_SECRET=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Create secrets
kubectl create secret generic inclusive-world-secrets \
  --namespace=inclusive-world-portal-dev \
  --from-literal=DJANGO_SECRET_KEY="${DJANGO_SECRET}" \
  --from-literal=POSTGRES_PASSWORD='dev-password-123' \
  --from-literal=MINIO_ROOT_USER='minioadmin' \
  --from-literal=MINIO_ROOT_PASSWORD='minioadmin123' \
  --from-literal=AWS_ACCESS_KEY_ID='minioadmin' \
  --from-literal=AWS_SECRET_ACCESS_KEY='minioadmin123'
```

### Step 4: Deploy with ArgoCD (30 seconds)

```bash
# Update repo URL in ArgoCD manifest
sed -i "s|https://github.com/your-org/inclusive_world_portal.git|$(git remote get-url origin)|g" \
  manifests/argocd/app-dev.yaml

# Apply ArgoCD Application
kubectl apply -f manifests/argocd/app-dev.yaml

# Wait for deployment
kubectl wait --for=condition=Ready pods --all -n inclusive-world-portal-dev --timeout=600s
```

### Step 5: Access Application

```bash
# Get the service
kubectl get svc -n inclusive-world-portal-dev

# Port forward to access locally
kubectl port-forward svc/dev-nginx -n inclusive-world-portal-dev 8080:80

# Open browser
open http://localhost:8080
```

## 🎯 What Gets Deployed?

- ✅ PostgreSQL database with persistent storage
- ✅ Redis cache
- ✅ MinIO object storage
- ✅ Django web application (2 replicas)
- ✅ Celery worker (2 replicas)
- ✅ Celery beat scheduler
- ✅ Nginx reverse proxy

## 📝 Next Steps

1. **Create a superuser:**
   ```bash
   kubectl exec -it deployment/dev-django -n inclusive-world-portal-dev -- \
     python manage.py createsuperuser
   ```

2. **Access admin panel:**
   - Navigate to: http://localhost:8080/admin/

3. **Check ArgoCD UI:**
   ```bash
   kubectl port-forward svc/argocd-server -n argocd 8443:443
   # Visit: https://localhost:8443
   ```

4. **View logs:**
   ```bash
   kubectl logs -f deployment/dev-django -n inclusive-world-portal-dev
   ```

## 🔧 Common Issues

### Pods not starting?
```bash
# Check pod status
kubectl describe pod <pod-name> -n inclusive-world-portal-dev

# Check events
kubectl get events -n inclusive-world-portal-dev --sort-by='.lastTimestamp'
```

### Image pull errors?
```bash
# Make sure image is public or create imagePullSecret
kubectl create secret docker-registry regcred \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=${DOCKER_USERNAME} \
  --docker-password=${DOCKER_PASSWORD} \
  --namespace=inclusive-world-portal-dev
```

### Database connection issues?
```bash
# Check PostgreSQL logs
kubectl logs statefulset/dev-postgres -n inclusive-world-portal-dev

# Test connection
kubectl exec -it deployment/dev-django -n inclusive-world-portal-dev -- \
  python manage.py check --database default
```

## 🚀 Deploy to Production

Ready for production? Check out the [Deployment Guide](./DEPLOYMENT_GUIDE.md) for:
- Production-grade security
- SSL/TLS configuration
- Monitoring and observability
- Backup and disaster recovery
- CI/CD pipeline setup

## 💡 Tips

- Use `kubectl get all -n inclusive-world-portal-dev` to see all resources
- ArgoCD will auto-sync changes from your Git repo
- Scale deployments with: `kubectl scale deployment/dev-django --replicas=3`
- Check resource usage: `kubectl top pods -n inclusive-world-portal-dev`

## 📚 Documentation

- [Full Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Manifest Structure](./README.md)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
