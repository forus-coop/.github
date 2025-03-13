# GitHub Workflow Templates

This repository contains reusable GitHub Actions workflow templates for CI/CD pipelines in our organization.

## Available Workflows

### CI/CD Pipeline

A complete CI/CD pipeline that builds Docker images, pushes them to AWS ECR, and deploys to Kubernetes using Helm.

#### How to Use in Your Repository

1. Navigate to your repository
2. Click on "Actions" tab
3. Under "Workflows created by your organization", select "CI/CD Pipeline"
4. Click "Set up this workflow"
5. Make any necessary customizations to the workflow file
6. Commit the changes to your repository

## Requirements for Your Repository

### Directory Structure

The CI/CD pipeline expects the following directory structure:

```
├── Dockerfile
├── helm/
│   ├── sandbox.yaml
│   ├── staging.yaml
│   └── production.yaml
```

### Helm Values Files

Example Helm values files are provided in the `workflow-templates/helm-values-examples/` directory. Copy these files to your repository as a starting point:

```
mkdir -p helm
cp /path/to/workflow-templates/helm-values-examples/*.yaml helm/
```

The Helm values files include:
- Environment-specific configuration
- Resource allocation
- Ingress settings
- Environment variables
- Autoscaling settings (for production)

### Secrets

The workflows require the following secrets to be set at the organization or repository level:

- AWS credentials (either AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, or AWS_ROLE_TO_ASSUME for OIDC)
- Kubernetes config files base64-encoded:
  - ORG_KUBECTL_CONFIG_BASE64_SANDBOX
  - ORG_KUBECTL_CONFIG_BASE64_STAGING
  - ORG_KUBECTL_CONFIG_BASE64_PRODUCTION

### GitHub Environments

Set up the following environments in your repository settings:
- sandbox
- staging
- production

## Customizing the Workflows

The workflows are designed to be used as-is, but can be customized as needed. The main `ci-cd-pipeline.yml` workflow calls two other workflows:

1. `docker-build-push.yml` - Builds and pushes Docker images to ECR
2. `helm-deploy.yml` - Deploys applications to Kubernetes using Helm

An example file demonstrating customization options is provided in `workflow-templates/example-usage.yml`.

## Workflow Behavior

- **Push to master/main**: Builds and deploys to sandbox environment
- **Merge PR to master/main**: Builds and deploys to sandbox environment
- **Create pre-release**: Builds and deploys to staging environment
- **Create release**: Builds and deploys to production environment
- **Manual trigger**: Allows selecting environment and other parameters

## Compatibility

These workflows are designed for applications with:
- Containerized applications with a Dockerfile
- Kubernetes deployments using Helm charts
- AWS ECR for container registry
