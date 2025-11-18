# Pre-Deployment Checklist

Use this checklist before deploying to any environment.

## 🔧 Initial Setup

### Container Registry
- [ ] Choose container registry (Docker Hub, GHCR, ECR, etc.)
- [ ] Create registry account/repository
- [ ] Configure registry credentials
- [ ] Test image push/pull access

### Git Repository
- [ ] Repository is accessible
- [ ] Manifests are in version control
- [ ] Branch strategy is defined (main, develop, staging)
- [ ] Repository URL is updated in ArgoCD manifests

### Kubernetes Cluster
- [ ] Cluster is accessible via kubectl
- [ ] Required namespaces can be created
- [ ] Storage classes are available
- [ ] Ingress controller is installed
- [ ] cert-manager is installed (for TLS)
- [ ] Metrics server is installed (for HPA)

### ArgoCD
- [ ] ArgoCD is installed
- [ ] ArgoCD CLI is configured
- [ ] Git repository is added to ArgoCD
- [ ] RBAC is configured (if needed)

## 📝 Configuration Updates

### Image References
- [ ] Update `manifests/base/django/deployment.yaml` with your registry
- [ ] Update `manifests/base/celery/worker-deployment.yaml` with your registry
- [ ] Update `manifests/base/celery/beat-deployment.yaml` with your registry
- [ ] Update `manifests/base/kustomization.yaml` images section
- [ ] Update overlay kustomization files with appropriate tags

### Domain Names
- [ ] Update `manifests/base/nginx/ingress.yaml` with your domain
- [ ] Update `manifests/overlays/dev/ingress-patch.yaml`
- [ ] Update `manifests/overlays/staging/ingress-patch.yaml`
- [ ] Update `manifests/overlays/production/ingress-patch.yaml`
- [ ] Configure DNS records for domains

### Storage Classes
- [ ] Identify available storage classes: `kubectl get storageclass`
- [ ] Update PostgreSQL StatefulSet storage class
- [ ] Update MinIO StatefulSet storage class
- [ ] Update Django PVCs with RWX-capable storage class
- [ ] Update Redis PVC storage class

### Resource Limits
- [ ] Review and adjust CPU/memory requests and limits
- [ ] Verify cluster has sufficient resources
- [ ] Adjust HPA min/max replicas for your needs
- [ ] Update ResourceQuota if needed

## 🔒 Secrets Configuration

### Development
- [ ] Generate Django secret key
- [ ] Create `inclusive-world-secrets` in dev namespace
- [ ] Set PostgreSQL password
- [ ] Set MinIO credentials
- [ ] Verify secrets are created: `kubectl get secrets -n inclusive-world-portal-dev`

### Staging
- [ ] Generate unique Django secret key
- [ ] Create `inclusive-world-secrets` in staging namespace
- [ ] Set strong PostgreSQL password
- [ ] Set strong MinIO credentials
- [ ] Configure email settings (if using SMTP)

### Production
- [ ] Generate strong Django secret key
- [ ] Use sealed-secrets or external-secrets operator
- [ ] Set production-grade passwords (16+ chars)
- [ ] Configure Sentry DSN (if using)
- [ ] Configure email settings
- [ ] Store secrets backup securely (encrypted)
- [ ] Never commit real secrets to Git

## 🚀 Build and Push Images

### Development Image
- [ ] Build development image
- [ ] Tag with `develop-<sha>`
- [ ] Push to registry
- [ ] Verify image is pullable

### Staging Image
- [ ] Build staging image
- [ ] Tag with `staging-<sha>`
- [ ] Push to registry
- [ ] Verify image is pullable

### Production Image
- [ ] Build production image
- [ ] Tag with semantic version (e.g., `v1.0.0`)
- [ ] Push to registry
- [ ] Scan image for vulnerabilities
- [ ] Sign image (optional but recommended)
- [ ] Verify image is pullable

## 📋 Manifest Validation

### Syntax Check
- [ ] Validate YAML syntax: `yamllint manifests/`
- [ ] Validate with kubectl: `kubectl apply --dry-run=client -k manifests/base/`
- [ ] Validate overlays: `kubectl apply --dry-run=client -k manifests/overlays/dev/`

### Kustomize Build
- [ ] Build dev: `kubectl kustomize manifests/overlays/dev/`
- [ ] Build staging: `kubectl kustomize manifests/overlays/staging/`
- [ ] Build production: `kubectl kustomize manifests/overlays/production/`
- [ ] Review generated manifests for correctness

### ArgoCD Validation
- [ ] Update repo URLs in ArgoCD Application manifests
- [ ] Validate Application manifest: `kubectl apply --dry-run=client -f manifests/argocd/app-dev.yaml`
- [ ] Check for ArgoCD-specific errors

## 🔐 Security Review

### Network Policies
- [ ] Review network policies are appropriate
- [ ] Test connectivity between services
- [ ] Verify external access is restricted

### RBAC
- [ ] Service accounts have minimal permissions
- [ ] Pod security standards are applied
- [ ] ArgoCD RBAC is configured

### Container Security
- [ ] Images use non-root user ✓ (already configured)
- [ ] Images are scanned for vulnerabilities
- [ ] Base images are up to date
- [ ] No secrets in environment variables (use k8s secrets)

### Ingress/TLS
- [ ] TLS is enabled for production
- [ ] cert-manager issuer is configured
- [ ] Force HTTPS redirect is enabled
- [ ] Security headers are configured

## 🎯 Pre-Deployment Testing

### Development Environment
- [ ] Deploy to dev: `kubectl apply -f manifests/argocd/app-dev.yaml`
- [ ] Wait for sync: `argocd app wait inclusive-world-portal-dev`
- [ ] Check pod status: `kubectl get pods -n inclusive-world-portal-dev`
- [ ] Check logs for errors: `kubectl logs -l app=django -n inclusive-world-portal-dev`
- [ ] Access application via port-forward
- [ ] Run migrations: `kubectl exec ... -- python manage.py migrate`
- [ ] Create superuser: `kubectl exec ... -- python manage.py createsuperuser`
- [ ] Login to admin panel
- [ ] Test basic functionality

### Staging Environment
- [ ] Deploy to staging
- [ ] Verify sync status
- [ ] Test with production-like data
- [ ] Run full test suite
- [ ] Performance testing
- [ ] Security testing

### Production Readiness
- [ ] Staging tests passed
- [ ] All secrets are configured
- [ ] Backups are configured
- [ ] Monitoring is set up
- [ ] Alerting is configured
- [ ] Rollback plan is documented
- [ ] Team is notified

## 📊 Monitoring Setup

### Application Monitoring
- [ ] Configure Prometheus metrics
- [ ] Set up Grafana dashboards
- [ ] Configure log aggregation (Loki/ELK)
- [ ] Set up distributed tracing (Jaeger)

### Alerting
- [ ] Configure alert rules
- [ ] Set up notification channels (Slack, email)
- [ ] Test alert delivery
- [ ] Document on-call procedures

### Health Checks
- [ ] Verify liveness probes are working
- [ ] Verify readiness probes are working
- [ ] Test application endpoints
- [ ] Monitor database connections

## 💾 Backup Configuration

### Database Backups
- [ ] Configure PostgreSQL backup job
- [ ] Test backup creation
- [ ] Test backup restoration
- [ ] Set retention policy
- [ ] Store backups off-cluster

### MinIO Backups
- [ ] Configure MinIO backup
- [ ] Test backup/restore
- [ ] Set retention policy

### Disaster Recovery
- [ ] Document recovery procedures
- [ ] Test full cluster recovery
- [ ] Define RTO/RPO targets

## 📚 Documentation

- [ ] Update README with deployment info
- [ ] Document environment variables
- [ ] Document manual procedures
- [ ] Create runbook for common issues
- [ ] Document rollback procedures
- [ ] Update architecture diagrams

## ✅ Deployment

### Deploy to Production
- [ ] All checklist items above are complete
- [ ] Change window is scheduled
- [ ] Stakeholders are notified
- [ ] Apply ArgoCD Application: `kubectl apply -f manifests/argocd/app-production.yaml`
- [ ] Manually sync (for production): `argocd app sync inclusive-world-portal-production`
- [ ] Monitor deployment progress
- [ ] Verify all pods are healthy
- [ ] Run smoke tests
- [ ] Verify external access
- [ ] Monitor metrics and logs
- [ ] Notify stakeholders of completion

## 🎉 Post-Deployment

- [ ] Verify application is accessible
- [ ] Run full test suite
- [ ] Monitor for errors/issues
- [ ] Update documentation
- [ ] Retrospective meeting
- [ ] Update this checklist with lessons learned

---

## Quick Reference Commands

```bash
# Check pod status
kubectl get pods -n <namespace>

# Check logs
kubectl logs -f deployment/<name> -n <namespace>

# Check events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n <namespace>

# Execute command in pod
kubectl exec -it deployment/<name> -n <namespace> -- <command>

# Port forward
kubectl port-forward svc/<service> -n <namespace> <local-port>:<remote-port>

# Check ArgoCD status
argocd app get <app-name>

# Sync application
argocd app sync <app-name>

# Rollback
argocd app rollback <app-name> <revision>
```
