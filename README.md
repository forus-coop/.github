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
      image_tag: ${{ github.sha }}
    secrets: inherit
```

### RSpec Testing

A workflow for running RSpec tests with configurable options for Ruby applications. This workflow supports:

- Customizing Ruby version
- Excluding specific files or patterns
- Running tests with specific tags
- Running tests on specific paths or files
- PostgreSQL database integration
- Redis integration

#### How to Reference in Your Repository

```yaml
jobs:
  test:
    uses: forus-coop/.github/.github/workflows/rspec-test.yml@main
    with:
      # Optional: Specify Ruby version
      ruby_version: "3.2.2"
      # Optional: Skip specific test files
      exclude_files: "spec/features/**/*,spec/slow/**/*"
      # Optional: Only run specific tagged tests
      rspec_tags: "~slow,~js"
      # Optional: Only run tests in specific directories
      rspec_paths: "spec/models,spec/controllers"
      # Optional: Enable PostgreSQL for tests
      postgres_enabled: true
      # Optional: Enable Redis for tests
      redis_enabled: true
    secrets:
      # Optional: Custom database URL
      DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
      # Optional: Custom Redis URL
      REDIS_URL: ${{ secrets.TEST_REDIS_URL }}
      inherit: true
```

### Semantic Versioning

A workflow for automatically determining and creating semantic version releases based on conventional commits or explicit version types. This workflow:

- Determines the next version number (major.minor.patch)
- Creates GitHub releases with appropriate tags
- Generates release notes from commit messages
- Updates pre-release status when moving to production
- Provides version outputs that can be used for Docker image tagging and Helm deployments

The workflow runs automatically for all deployments and maintains consistent version numbers across environments, only changing the pre-release status in GitHub.

#### How to Reference in Your Repository

```yaml
jobs:
  create-version:
    uses: forus-coop/.github/.github/workflows/semver-release.yml@main
    with:
      # Type of release - auto detects from commit messages, or specify major/minor/patch
      release_type: "auto"
      # Whether this is a prerelease - typically true for sandbox/staging
      prerelease: false
      # Branch to create the release from
      release_branch: "main"
    secrets: inherit
    
  build:
    needs: [create-version]
    uses: forus-coop/.github/.github/workflows/docker-build-push.yml@main
    with:
      # Use the semantic version for the image tag
      image_tag: ${{ needs.create-version.outputs.version_tag }}
```

#### Conventional Commit Format

For automatic version determination, use the following commit message format:

- `feat: add new feature` (increments minor version)
- `fix: fix bug` (increments patch version)
- `breaking: major change` (increments major version)

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

### Repository and Application Naming

The workflows automatically format repository names to ensure consistent naming conventions:

- **ECR Repository Names**: The repository name is converted to lowercase with underscores replaced by hyphens.
  - Example: A repository named "My_App_Service" becomes "my-app-service" in ECR.

- **Helm Release Names**: The repository name is similarly formatted for Helm releases.
  - The same hyphenated, lowercase format is used for deployment.
  - This ensures consistency between your container images and Helm deployments.

This automatic formatting maintains a consistent naming convention across all environments and services.

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
- For Ruby applications using GitHub Packages:
  - SECRET_KEY_BASE - Used during Docker build to access private Ruby gems

> **Security Note**: Always pass sensitive values like SECRET_KEY_BASE as secrets rather than inputs. The docker-build-push workflow is configured to accept this secret and pass it securely to the Docker build process.

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
secrets:
  SECRET_KEY_BASE: ${{ secrets.SECRET_KEY_BASE }} # For Ruby applications
  inherit: true

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

### Semantic Versioning Behavior

The CI/CD pipeline creates semantic versioned releases automatically for all deployments:

1. The version number is determined from conventional commits or can be manually specified
2. The same version number is used across all environments for consistency 
3. Pre-release status in GitHub is set based on the environment:
   - **Production deployments**: Full releases (no pre-release flag)
   - **Sandbox/staging deployments**: Pre-releases (with pre-release flag)

When a release is promoted from staging to production:
- The same version tag is retained
- The pre-release flag is removed
- The GitHub release is updated rather than creating a new one

This approach ensures that:
- The same image tag is used consistently across environments
- Versioning is automatic but can be overridden when needed
- Release history and notes are preserved when promoting to production

## Compatibility

These workflows are designed for applications with:
- Containerized applications with a Dockerfile
- Kubernetes deployments using Helm charts
- AWS ECR for container registry
