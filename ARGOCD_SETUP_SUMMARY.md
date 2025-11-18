# ArgoCD Setup Summary for Inclusive World Portal

A complete Kubernetes manifest structure for deploying your Django application with ArgoCD:

```
manifests/
├── README.md                          # Overview and structure
├── DEPLOYMENT_GUIDE.md                # Comprehensive deployment instructions
├── QUICKSTART.md                      # 5-minute quick start guide
├── IMAGE_BUILD_STRATEGY.md            # Image building and tagging strategies
├── CHECKLIST.md                       # Pre-deployment checklist
├── .gitignore                         # Protect secrets from Git
│
├── base/                              # Base Kubernetes resources
│   ├── namespace.yaml                 # Namespace definition
│   ├── configmap.yaml                 # Application configuration
│   ├── secrets.yaml.example           # Secret template (DO NOT commit real secrets!)
│   ├── kustomization.yaml             # Base kustomize config
│   │
│   ├── postgres/                      # PostgreSQL database
│   │   ├── statefulset.yaml           # StatefulSet with persistent storage
│   │   └── service.yaml               # Database service
│   │
│   ├── redis/                         # Redis cache
│   │   ├── deployment.yaml            # Redis deployment
│   │   ├── service.yaml               # Redis service
│   │   └── pvc.yaml                   # Persistent volume claim
│   │
│   ├── minio/                         # MinIO object storage
│   │   ├── statefulset.yaml           # MinIO StatefulSet
│   │   ├── service.yaml               # MinIO service
│   │   └── init-job.yaml              # Bucket initialization job
│   │
│   ├── django/                        # Django application
│   │   ├── deployment.yaml            # Django deployment with migrations
│   │   ├── service.yaml               # Django service
│   │   ├── pvc.yaml                   # Static/media storage
│   │   └── hpa.yaml                   # Horizontal Pod Autoscaler
│   │
│   ├── celery/                        # Celery workers
│   │   ├── worker-deployment.yaml     # Celery worker deployment
│   │   ├── beat-deployment.yaml       # Celery beat scheduler
│   │   ├── pvc.yaml                   # Beat schedule storage
│   │   └── worker-hpa.yaml            # Worker autoscaling
│   │
│   └── nginx/                         # Nginx reverse proxy
│       ├── configmap.yaml             # Nginx configuration
│       ├── deployment.yaml            # Nginx deployment
│       ├── service.yaml               # Nginx service
│       └── ingress.yaml               # Ingress resource
│
├── overlays/                          # Environment-specific configs
│   ├── dev/                           # Development environment
│   │   ├── kustomization.yaml         # Dev customizations
│   │   └── ingress-patch.yaml         # Dev ingress config
│   │
│   ├── staging/                       # Staging environment
│   │   ├── kustomization.yaml         # Staging customizations
│   │   ├── ingress-patch.yaml         # Staging ingress with TLS
│   │   └── namespace-resourcequota.yaml
│   │
│   └── production/                    # Production environment
│       ├── kustomization.yaml         # Production customizations
│       ├── ingress-patch.yaml         # Production ingress with TLS
│       ├── namespace-resourcequota.yaml
│       ├── pod-disruption-budget.yaml # High availability config
│       └── network-policy.yaml        # Network security policies
│
└── argocd/                            # ArgoCD application definitions
    ├── app-dev.yaml                   # Dev environment app
    ├── app-staging.yaml               # Staging environment app
    ├── app-production.yaml            # Production environment app
    └── appproject.yaml                # ArgoCD project with RBAC

.github/workflows/
├── build-and-deploy.yml               # CI/CD pipeline for image builds
└── security-scan.yml                  # Security scanning workflow

scripts/
├── build-and-push.sh                  # Helper script to build/push images
└── update-image-tag.sh                # Helper script to update manifests
```

## 🎯 Key Features

### Multi-Environment Support
- **Development**: Auto-sync enabled, debug mode, minimal resources
- **Staging**: Auto-sync, production-like config, moderate resources
- **Production**: Manual sync, full security, high availability

### High Availability
- Multiple replicas for Django (2-3)
- Multiple replicas for Celery workers (2-3)
- Horizontal Pod Autoscalers (HPA) for auto-scaling
- Pod Disruption Budgets (PDB) for graceful updates
- Rolling update strategy with zero downtime

### Security
- Network policies to restrict pod-to-pod communication
- Non-root containers
- Sealed secrets support
- TLS/HTTPS for production
- Resource quotas
- RBAC for ArgoCD access

### Observability
- Liveness and readiness probes
- Resource requests and limits
- Health check endpoints
- Structured logging

### GitOps
- Full GitOps workflow with ArgoCD
- Declarative configuration
- Automatic sync for dev/staging
- Manual approval for production
- Easy rollbacks

## 🚀 Quick Start

### 1. Update Image References

```bash
# Find and replace all image references
cd manifests/base
find . -type f -name "*.yaml" -exec sed -i \
  's|your-registry/inclusive-world-portal|YOUR_ACTUAL_REGISTRY/inclusive-world-portal|g' {} +
```

### 2. Build and Push Image

```bash
# Using Docker Hub
docker build -t YOUR_USERNAME/inclusive-world-portal:latest --target production .
docker push YOUR_USERNAME/inclusive-world-portal:latest

# Or use the helper script
chmod +x scripts/build-and-push.sh
./scripts/build-and-push.sh YOUR_REGISTRY latest
```

### 3. Create Secrets

```bash
# Generate Django secret key
export DJANGO_KEY=$(openssl rand -base64 50)

kubectl create secret generic inclusive-world-secrets \
  --namespace=inclusive-world-portal-dev \
  --from-literal=DJANGO_SECRET_KEY="${DJANGO_KEY}" \
  --from-literal=POSTGRES_PASSWORD='dev-password-123' \
  --from-literal=MINIO_ROOT_USER='minioadmin' \
  --from-literal=MINIO_ROOT_PASSWORD='minioadmin123' \
  --from-literal=AWS_ACCESS_KEY_ID='minioadmin' \
  --from-literal=AWS_SECRET_ACCESS_KEY='minioadmin123'

```

### 4. Deploy with ArgoCD

```bash
# Update repo URL in ArgoCD manifest
sed -i 's|https://github.com/your-org/inclusive_world_portal.git|YOUR_REPO_URL|g' \
  manifests/argocd/app-dev.yaml

# Apply ArgoCD Application
kubectl apply -f manifests/argocd/app-dev.yaml

# Wait for sync
argocd app wait inclusive-world-portal-dev --health
```

### 5. Access Application

```bash
# Port forward to access
kubectl port-forward svc/dev-nginx -n inclusive-world-portal-dev 8080:80

# Create superuser
kubectl exec -it deployment/dev-django -n inclusive-world-portal-dev -- \
  python manage.py createsuperuser

# Open browser
open http://localhost:8080
```

## 📝 Next Steps

### For Development
1. Follow the [QUICKSTART.md](manifests/QUICKSTART.md) guide
2. Configure your Git repository URL
3. Set up local development workflow

### For Production
1. Review the [DEPLOYMENT_GUIDE.md](manifests/DEPLOYMENT_GUIDE.md)
2. Complete the [CHECKLIST.md](manifests/CHECKLIST.md)
3. Set up proper secret management (sealed-secrets or external-secrets)
4. Configure TLS certificates with cert-manager
5. Set up monitoring and alerting
6. Configure backup strategy

### For CI/CD
1. Review `.github/workflows/build-and-deploy.yml`
2. Configure GitHub secrets (GITHUB_TOKEN is automatic)
3. Optional: Add SLACK_WEBHOOK_URL for notifications
4. Optional: Add SNYK_TOKEN for security scanning
5. Customize branch strategy if needed

## 🔧 Customization

### Storage Classes
Update storage classes in overlays based on your cluster:
```yaml
# In manifests/overlays/production/kustomization.yaml
storageClassName: fast-ssd  # For PostgreSQL
storageClassName: standard  # For MinIO
storageClassName: nfs-client  # For Django RWX volumes
```

### Domain Names
Update domain names in ingress patches:
```yaml
# manifests/overlays/production/ingress-patch.yaml
host: your-domain.com
```

### Resource Limits
Adjust CPU/memory in deployment specs based on your needs.

### Replica Counts
Modify replica counts in overlay kustomization files.

## 📚 Documentation

- **[README.md](manifests/README.md)** - Overview and directory structure
- **[DEPLOYMENT_GUIDE.md](manifests/DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[QUICKSTART.md](manifests/QUICKSTART.md)** - 5-minute quick start
- **[IMAGE_BUILD_STRATEGY.md](manifests/IMAGE_BUILD_STRATEGY.md)** - Image building strategies
- **[CHECKLIST.md](manifests/CHECKLIST.md)** - Pre-deployment checklist

## 🎓 Important Notes

### Secrets Management
- **NEVER commit real secrets to Git**
- Use `secrets.yaml.example` as a template
- Real secrets should use:
  - Sealed Secrets for small teams
  - External Secrets Operator for enterprise
  - Manual creation for quick testing

### Image Registry
You must replace `your-registry/inclusive-world-portal` with your actual registry:
- Docker Hub: `username/inclusive-world-portal`
- GHCR: `ghcr.io/username/inclusive-world-portal`
- ECR: `123456789.dkr.ecr.us-east-1.amazonaws.com/inclusive-world-portal`
- GCR: `gcr.io/project-id/inclusive-world-portal`

### ArgoCD Sync Policies
- **Dev**: Auto-sync enabled (immediate updates)
- **Staging**: Auto-sync enabled (immediate updates)
- **Production**: Manual sync (controlled releases)

### Resource Requirements
Minimum cluster resources needed:
- **Dev**: 4 CPU, 8GB RAM
- **Staging**: 8 CPU, 16GB RAM
- **Production**: 20 CPU, 40GB RAM (with headroom for scaling)

## 🆘 Getting Help

If you encounter issues:

1. Check the [DEPLOYMENT_GUIDE.md](manifests/DEPLOYMENT_GUIDE.md) troubleshooting section
2. Review pod logs: `kubectl logs -f deployment/django -n <namespace>`
3. Check events: `kubectl get events -n <namespace> --sort-by='.lastTimestamp'`
4. Verify ArgoCD status: `argocd app get <app-name>`
5. Review the [CHECKLIST.md](manifests/CHECKLIST.md) to ensure all steps are completed

## ✅ Summary

You now have:
- ✅ Complete Kubernetes manifests for all services
- ✅ ArgoCD Applications for 3 environments (dev, staging, production)
- ✅ Kustomize overlays for environment-specific configs
- ✅ CI/CD pipeline with GitHub Actions
- ✅ Security scanning workflow
- ✅ Comprehensive documentation
- ✅ Helper scripts for common tasks
- ✅ Production-ready configuration with HA and security

**Ready to deploy!** Start with the [QUICKSTART.md](manifests/QUICKSTART.md) for a rapid dev deployment, or follow the [DEPLOYMENT_GUIDE.md](manifests/DEPLOYMENT_GUIDE.md) for production.
