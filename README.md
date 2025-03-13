# GitHub Workflow Templates

This repository contains reusable GitHub Actions workflow templates for CI/CD pipelines in our organization.

## Centralized Workflow Approach

We use a centralized workflow approach where all repositories in the organization reference the workflows defined in this `.github` repository. This provides:

- A single source of truth for all CI/CD workflows
- Consistent deployment processes across all repositories
- Simplified maintenance and updates

## Available Workflows

### CI/CD Pipeline

A complete CI/CD pipeline that builds Docker images, pushes them to AWS ECR, and deploys to Kubernetes using Helm.

#### How to Reference in Your Repository

In your repository's workflow file:

```yaml
jobs:
  build:
    uses: forus-coop/.github/.github/workflows/docker-build-push.yml@main
    with:
      image_tag: ${{ github.sha }}
      runner_group: sandbox
    secrets: inherit

  deploy:
    uses: forus-coop/.github/.github/workflows/helm-deploy.yml@main
    with:
      environment: production
      app_name: my-app
      image_tag: ${{ github.sha }}
    secrets: inherit
```

#### How to Set Up in a New Repository

1. Navigate to your repository
2. Create a `.github/workflows/ci-cd.yml` file
3. Use the template from `workflow-templates/example-usage.yml`
4. Customize as needed for your application
5. Commit the changes to your repository

For detailed setup instructions, see [SETUP.md](workflow-templates/SETUP.md).

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

Example Helm values files are provided in the `workflow-templates/helm-values-examples/` directory. You can fetch these files using:

```bash
curl -o helm/sandbox.yaml https://raw.githubusercontent.com/forus-coop/.github/main/workflow-templates/helm-values-examples/sandbox.yaml
curl -o helm/staging.yaml https://raw.githubusercontent.com/forus-coop/.github/main/workflow-templates/helm-values-examples/staging.yaml
curl -o helm/production.yaml https://raw.githubusercontent.com/forus-coop/.github/main/workflow-templates/helm-values-examples/production.yaml
```

The Helm values files include:
- Environment-specific configuration
- Resource allocation
- Ingress settings
- Environment variables
- Autoscaling settings (for production)

### Self-Hosted Runners

The workflows are designed to use self-hosted runners with specific group names:

1. Docker build jobs run on the runner group specified by the `runner_group` parameter (defaults to 'sandbox')
2. Deployment jobs run on the runner group with the same name as the target environment

Ensure that you have self-hosted runners set up in the following runner groups:
- `sandbox` - For sandbox environment
- `staging` - For staging environment
- `production` - For production environment

### Secrets

The workflows require the following secrets to be set at the organization or repository level:

- AWS credentials (either AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, or AWS_ROLE_TO_ASSUME for OIDC)
- Kubernetes config files base64-encoded:
  - ORG_KUBECTL_CONFIG_BASE64_SANDBOX
  - ORG_KUBECTL_CONFIG_BASE64_STAGING
  - ORG_KUBECTL_CONFIG_BASE64_PRODUCTION

> **Important**: GitHub Actions doesn't support dynamic secret names with string concatenation. The workflow uses conditional steps to access the appropriate secret for each environment.

### GitHub Environments

Set up the following environments in your repository settings:
- sandbox
- staging
- production

## Workflow Permission Requirements

For repositories to use these centralized workflows:

1. The `.github` repository must be public, OR
2. Workflow permissions must be properly configured in your organization settings:
   - Go to your organization settings > Actions > General
   - Under "Workflow permissions", select "Allow enterprise, organization, and repository workflows"

## Customizing Workflow Usage

The workflows are designed to be used with minimal configuration, but can be customized with various input parameters.

Examples of customization:

```yaml
# Custom Docker build configuration
uses: forus-coop/.github/.github/workflows/docker-build-push.yml@main
with:
  docker_build_dir: './app'
  dockerfile_path: 'Dockerfile.prod'
  image_tag: ${{ github.sha }}
  runner_group: sandbox

# Custom Helm deployment
uses: forus-coop/.github/.github/workflows/helm-deploy.yml@main
with:
  environment: production
  helm_chart: 'oci://ghcr.io/forus-coop/custom-chart'
  helm_values_file: './helm/custom/production.yaml'
```

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
