# Image Build and Deployment Strategy

This document outlines the recommended strategies for building and deploying Docker images for the Inclusive World Portal.

## 🎯 Image Tagging Strategy

### Semantic Versioning for Production

Use [Semantic Versioning](https://semver.org/) for production releases:

```
v<major>.<minor>.<patch>
```

Examples:
- `v1.0.0` - Initial production release
- `v1.1.0` - New features, backward compatible
- `v1.1.1` - Bug fixes
- `v2.0.0` - Breaking changes

### Environment-Based Tagging

| Environment | Tag Strategy | Example |
|------------|--------------|---------|
| Development | `develop-<short-sha>` | `develop-a1b2c3d` |
| Staging | `staging-<short-sha>` | `staging-x9y8z7w` |
| Production | `v<major>.<minor>.<patch>` | `v1.2.3` |

### Additional Tags

- `latest` - Always points to the latest main branch build
- `<branch>-latest` - Latest build from a specific branch
- `<sha>` - Full commit SHA for debugging

## 🏗️ Build Strategies

### Strategy 1: GitHub Actions (Recommended)

**Pros:**
- Automated on every push
- Integrated with GitHub
- Free for public repos
- Built-in secret management

**Cons:**
- Slower build times
- Limited to GitHub

**Implementation:**

Already configured in `.github/workflows/build-and-deploy.yml`

```yaml
# Triggered on:
# - Push to main, develop, staging
# - Tags matching v*.*.*
# - Pull requests to main
```

### Strategy 2: GitLab CI/CD

**Pros:**
- Built-in container registry
- Faster builds
- Advanced caching

**Example `.gitlab-ci.yml`:**

```yaml
variables:
  IMAGE: $CI_REGISTRY_IMAGE
  DOCKER_DRIVER: overlay2

stages:
  - build
  - deploy

build:
  stage: build
  image: docker:24-dind
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build --target production -t $IMAGE:$CI_COMMIT_SHORT_SHA .
    - docker tag $IMAGE:$CI_COMMIT_SHORT_SHA $IMAGE:$CI_COMMIT_REF_NAME
    - docker push $IMAGE:$CI_COMMIT_SHORT_SHA
    - docker push $IMAGE:$CI_COMMIT_REF_NAME
  only:
    - branches
    - tags
```

### Strategy 3: Jenkins Pipeline

**Pros:**
- Full control
- On-premise option
- Highly customizable

**Example Jenkinsfile:**

```groovy
pipeline {
    agent any
    
    environment {
        REGISTRY = 'your-registry.com'
        IMAGE = 'inclusive-world-portal'
        TAG = "${env.GIT_COMMIT.take(7)}"
    }
    
    stages {
        stage('Build') {
            steps {
                script {
                    docker.build("${REGISTRY}/${IMAGE}:${TAG}", 
                                "--target production .")
                }
            }
        }
        
        stage('Push') {
            steps {
                script {
                    docker.withRegistry("https://${REGISTRY}", 'registry-credentials') {
                        docker.image("${REGISTRY}/${IMAGE}:${TAG}").push()
                        docker.image("${REGISTRY}/${IMAGE}:${TAG}").push('latest')
                    }
                }
            }
        }
        
        stage('Update Manifests') {
            steps {
                sh """
                    cd manifests/overlays/production
                    sed -i 's|newTag:.*|newTag: ${TAG}|g' kustomization.yaml
                    git add .
                    git commit -m "Update image to ${TAG}"
                    git push
                """
            }
        }
    }
}
```

### Strategy 4: Local Development Builds

**For testing before pushing:**

```bash
#!/bin/bash
# build-local.sh

set -e

# Configuration
REGISTRY="your-registry"
IMAGE="inclusive-world-portal"
TAG="local-$(git rev-parse --short HEAD)"

echo "Building image: ${REGISTRY}/${IMAGE}:${TAG}"

# Build
docker build \
  --target production \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --cache-from ${REGISTRY}/${IMAGE}:latest \
  -t ${REGISTRY}/${IMAGE}:${TAG} \
  -t ${REGISTRY}/${IMAGE}:local \
  .

echo "Build complete!"
echo "Image: ${REGISTRY}/${IMAGE}:${TAG}"

# Optional: Push
read -p "Push to registry? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker push ${REGISTRY}/${IMAGE}:${TAG}
    docker push ${REGISTRY}/${IMAGE}:local
fi
```

## 📦 Container Registry Options

### GitHub Container Registry (GHCR)

**Best for:** GitHub-hosted projects

```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and push
docker build -t ghcr.io/username/inclusive-world-portal:v1.0.0 --target production .
docker push ghcr.io/username/inclusive-world-portal:v1.0.0
```

**Manifest update:**
```yaml
images:
  - name: your-registry/inclusive-world-portal
    newName: ghcr.io/username/inclusive-world-portal
    newTag: v1.0.0
```

### Docker Hub

**Best for:** Public images, simple setup

```bash
# Login
docker login

# Build and push
docker build -t username/inclusive-world-portal:v1.0.0 --target production .
docker push username/inclusive-world-portal:v1.0.0
```

**Manifest update:**
```yaml
images:
  - name: your-registry/inclusive-world-portal
    newName: username/inclusive-world-portal
    newTag: v1.0.0
```

### AWS ECR

**Best for:** AWS deployments

```bash
# Create repository
aws ecr create-repository --repository-name inclusive-world-portal --region us-east-1

# Login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t 123456789.dkr.ecr.us-east-1.amazonaws.com/inclusive-world-portal:v1.0.0 \
  --target production .
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/inclusive-world-portal:v1.0.0
```

### Google Container Registry (GCR)

**Best for:** GCP deployments

```bash
# Configure Docker
gcloud auth configure-docker

# Build and push
docker build -t gcr.io/project-id/inclusive-world-portal:v1.0.0 --target production .
docker push gcr.io/project-id/inclusive-world-portal:v1.0.0
```

### Azure Container Registry (ACR)

**Best for:** Azure deployments

```bash
# Login
az acr login --name myregistry

# Build and push
docker build -t myregistry.azurecr.io/inclusive-world-portal:v1.0.0 --target production .
docker push myregistry.azurecr.io/inclusive-world-portal:v1.0.0
```

### Harbor (Self-Hosted)

**Best for:** Enterprise, on-premise

```bash
# Login
docker login harbor.company.com

# Build and push
docker build -t harbor.company.com/project/inclusive-world-portal:v1.0.0 --target production .
docker push harbor.company.com/project/inclusive-world-portal:v1.0.0
```

## 🔄 Deployment Workflows

### GitOps Workflow (Recommended)

```
1. Developer pushes code to Git
2. CI builds and pushes image
3. CI updates manifest with new image tag
4. ArgoCD detects manifest change
5. ArgoCD syncs to cluster
6. Application is deployed
```

**Advantages:**
- Git as single source of truth
- Audit trail
- Easy rollbacks
- Declarative

### Push-Based Workflow

```
1. Developer pushes code to Git
2. CI builds and pushes image
3. CI directly updates Kubernetes
4. Application is deployed
```

**Advantages:**
- Faster deployments
- Simpler setup

**Example:**
```bash
# In CI/CD pipeline
kubectl set image deployment/django \
  django=${REGISTRY}/${IMAGE}:${TAG} \
  -n inclusive-world-portal
```

## 🚀 Release Process

### Development Release

```bash
# Automatic on every push to develop
git checkout develop
git add .
git commit -m "feat: new feature"
git push origin develop

# CI builds and tags: develop-<sha>
# ArgoCD auto-deploys to dev environment
```

### Staging Release

```bash
# Automatic on push to staging
git checkout staging
git merge develop
git push origin staging

# CI builds and tags: staging-<sha>
# ArgoCD auto-deploys to staging
```

### Production Release

```bash
# Create release tag
git checkout main
git merge staging
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin main --tags

# CI builds and tags: v1.2.3
# CI creates PR to update production manifests
# Manual review and merge
# ArgoCD syncs to production
```

## 🔒 Security Best Practices

### 1. Multi-Stage Builds

Already implemented in `Dockerfile`:
- Builder stage (discarded)
- Production stage (minimal, no build tools)

### 2. Scan Images

```bash
# Trivy
trivy image ${REGISTRY}/${IMAGE}:${TAG}

# Snyk
snyk container test ${REGISTRY}/${IMAGE}:${TAG}

# Grype
grype ${REGISTRY}/${IMAGE}:${TAG}
```

### 3. Sign Images

```bash
# Cosign
cosign sign ${REGISTRY}/${IMAGE}:${TAG}

# Verify
cosign verify ${REGISTRY}/${IMAGE}:${TAG}
```

### 4. Use Specific Base Image Versions

```dockerfile
# Bad
FROM python:3.13-alpine

# Good
FROM python:3.13.0-alpine3.19
```

### 5. Non-Root User

Already implemented:
```dockerfile
USER django
```

## 📊 Monitoring Image Builds

### Build Metrics to Track

- Build time
- Image size
- Layer count
- Vulnerability count
- Cache hit rate

### Tools

- **Docker Build History**
  ```bash
  docker history ${IMAGE}:${TAG}
  ```

- **Dive** (image layer analysis)
  ```bash
  dive ${IMAGE}:${TAG}
  ```

- **Skopeo** (inspect remote images)
  ```bash
  skopeo inspect docker://${REGISTRY}/${IMAGE}:${TAG}
  ```

## 🎓 Tips and Tricks

### Optimize Build Speed

1. **Use BuildKit:**
   ```bash
   export DOCKER_BUILDKIT=1
   ```

2. **Layer caching:**
   ```dockerfile
   # Copy deps first (changes less often)
   COPY pyproject.toml uv.lock ./
   RUN uv sync --frozen --no-install-project
   
   # Copy code last (changes often)
   COPY . .
   ```

3. **Use cache mounts:**
   ```dockerfile
   RUN --mount=type=cache,target=/root/.cache/uv \
       uv sync --frozen
   ```

### Reduce Image Size

1. **Multi-stage builds** ✅ (already implemented)
2. **Alpine base images** ✅ (already implemented)
3. **Remove unnecessary files:**
   ```dockerfile
   RUN rm -rf /var/cache/apk/* /tmp/*
   ```

### Debug Build Issues

```bash
# Build with verbose output
docker build --progress=plain --no-cache .

# Inspect intermediate layers
docker build --target builder -t debug .
docker run -it debug sh
```

## 📝 Manifest Update Methods

### Method 1: Kustomize Edit (Recommended)

```bash
cd manifests/overlays/production
kustomize edit set image \
  your-registry/inclusive-world-portal=ghcr.io/user/app:v1.2.3
git add kustomization.yaml
git commit -m "Update to v1.2.3"
git push
```

### Method 2: Sed

```bash
cd manifests/overlays/production
sed -i 's|newTag:.*|newTag: v1.2.3|g' kustomization.yaml
```

### Method 3: Yq

```bash
yq e '.images[0].newTag = "v1.2.3"' -i manifests/overlays/production/kustomization.yaml
```

### Method 4: ArgoCD Image Updater

Install ArgoCD Image Updater to automatically update images:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  annotations:
    argocd-image-updater.argoproj.io/image-list: app=ghcr.io/user/app
    argocd-image-updater.argoproj.io/app.update-strategy: semver
```

## 🔗 References

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Image Pull Policy](https://kubernetes.io/docs/concepts/containers/images/)
- [ArgoCD Image Updater](https://argocd-image-updater.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
