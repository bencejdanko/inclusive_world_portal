# Kubernetes Manifests for Inclusive World Portal

This directory contains Kubernetes manifests for deploying the Inclusive World Portal application using ArgoCD.

## 📁 Directory Structure

```
manifests/
├── base/                    # Base Kubernetes resources
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── postgres/
│   ├── redis/
│   ├── minio/
│   ├── django/
│   ├── celery/
│   └── nginx/
├── overlays/               # Environment-specific configurations
│   ├── dev/
│   ├── staging/
│   └── production/
└── argocd/                 # ArgoCD Application definitions
    ├── app-dev.yaml
    ├── app-staging.yaml
    └── app-production.yaml
```

## 🚀 Deployment Strategy

### 1. Build and Push Docker Images

Before deploying with ArgoCD, you need to build and push your Docker images to a container registry.

#### Option A: Using Docker Hub

```bash
# Login to Docker Hub
docker login

# Build and tag the image
docker build -t your-dockerhub-username/inclusive-world-portal:latest \
  --target production .

# Push to Docker Hub
docker push your-dockerhub-username/inclusive-world-portal:latest

# Tag with version
docker tag your-dockerhub-username/inclusive-world-portal:latest \
  your-dockerhub-username/inclusive-world-portal:v1.0.0
docker push your-dockerhub-username/inclusive-world-portal:v1.0.0
```

#### Option B: Using GitHub Container Registry (GHCR)

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and tag
docker build -t ghcr.io/your-org/inclusive-world-portal:latest \
  --target production .

# Push to GHCR
docker push ghcr.io/your-org/inclusive-world-portal:latest
```

#### Option C: Using AWS ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t 123456789.dkr.ecr.us-east-1.amazonaws.com/inclusive-world-portal:latest \
  --target production .

# Push to ECR
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/inclusive-world-portal:latest
```

### 2. Update Image References

After pushing images, update the image references in:
- `manifests/base/django/deployment.yaml`
- `manifests/base/celery/worker-deployment.yaml`
- `manifests/base/celery/beat-deployment.yaml`

### 3. Configure Secrets

Create a secrets file with your sensitive data:

```bash
# Create from .env.docker
kubectl create secret generic inclusive-world-secrets \
  --from-env-file=.env.docker \
  --namespace=inclusive-world-portal \
  --dry-run=client -o yaml > manifests/base/secrets.yaml
```

**Important:** Never commit real secrets to git. Use sealed-secrets, external-secrets, or SOPS.

### 4. Deploy with ArgoCD

```bash
# Install ArgoCD (if not already installed)
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Apply the ArgoCD Application
kubectl apply -f manifests/argocd/app-dev.yaml

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

## 🔧 Configuration

### Environment Variables

Key environment variables are configured in:
- `manifests/base/configmap.yaml` - Non-sensitive configuration
- `manifests/base/secrets.yaml` - Sensitive data (encrypted)

### Persistent Storage

The application uses PersistentVolumeClaims for:
- PostgreSQL data
- Redis data
- MinIO data
- Django media files

Configure storage classes in environment overlays based on your cluster.

## 📝 Customization

### Development Environment

```bash
cd manifests/overlays/dev
kubectl apply -k .
```

### Staging Environment

```bash
cd manifests/overlays/staging
kubectl apply -k .
```

### Production Environment

```bash
cd manifests/overlays/production
kubectl apply -k .
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Docker image
        run: |
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} --target production .
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}
      
      - name: Update image tag in manifests
        run: |
          cd manifests/overlays/production
          kustomize edit set image inclusive-world-portal=ghcr.io/${{ github.repository }}:${{ github.sha }}
      
      - name: Commit and push manifest changes
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add manifests/
          git commit -m "Update image to ${{ github.sha }}"
          git push
```

## 🛡️ Security Considerations

1. **Never commit real secrets** - Use external secret management
2. **Use non-root containers** - Already configured in Dockerfile
3. **Enable NetworkPolicies** - Restrict pod-to-pod communication
4. **Use RBAC** - Limit service account permissions
5. **Scan images** - Integrate security scanning in CI/CD
6. **Use image digests** - Pin to specific image digests in production

## 📊 Monitoring

Consider adding:
- Prometheus for metrics
- Grafana for visualization
- Loki for log aggregation
- Jaeger for distributed tracing

## 🔗 Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Kustomize Documentation](https://kustomize.io/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
