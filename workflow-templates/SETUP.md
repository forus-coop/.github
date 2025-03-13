# Setting Up CI/CD in a New Repository

This guide will help you set up the CI/CD pipeline in a new repository using our organization's centralized workflows.

## Step 1: Create the Required Directory Structure

```bash
# Create the necessary directories
mkdir -p .github/workflows
mkdir -p helm
```

## Step 2: Create the Main Workflow File

Create a CI/CD workflow file in your repository that references our centralized workflows:

```bash
# Create the main workflow file directory
mkdir -p .github/workflows

# Create the main workflow file
cat > .github/workflows/ci-cd.yml << 'EOF'
name: CI/CD Pipeline

on:
  push:
    branches:
      - main
      - master
  pull_request:
    types: [closed]
    branches:
      - main
      - master
  release:
    types: [prereleased, released]
  workflow_dispatch:
    inputs:
      ref:
        description: "Commit SHA, Branch or Tag to deploy"
        required: false
        default: ""
      environment:
        description: "Environment to deploy to"
        required: true
        type: choice
        options:
          - sandbox
          - staging
          - production
      app_name:
        description: "Name of the app (defaults to repo name)"
        required: false
      namespace:
        description: "Kubernetes namespace (defaults to environment name)"
        required: false

jobs:
  determine-environment:
    runs-on: ubuntu-latest
    outputs:
      environment: ${{ steps.set-env.outputs.environment }}
      ref: ${{ steps.set-ref.outputs.ref }}
    steps:
      - name: Set environment based on event
        id: set-env
        run: |
          if [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
            echo "environment=${{ github.event.inputs.environment }}" >> $GITHUB_OUTPUT
          elif [[ "${{ github.event_name }}" == "release" && "${{ github.event.action }}" == "released" ]]; then
            echo "environment=production" >> $GITHUB_OUTPUT
          elif [[ "${{ github.event_name }}" == "release" && "${{ github.event.action }}" == "prereleased" ]]; then
            echo "environment=staging" >> $GITHUB_OUTPUT
          elif [[ "${{ github.event_name }}" == "pull_request" && "${{ github.event.pull_request.merged }}" == "true" ]]; then
            echo "environment=sandbox" >> $GITHUB_OUTPUT
          elif [[ "${{ github.event_name }}" == "push" && "${{ github.ref }}" == "refs/heads/master" || "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "environment=sandbox" >> $GITHUB_OUTPUT
          else
            echo "environment=skip" >> $GITHUB_OUTPUT
          fi

      - name: Set reference (SHA, branch, tag)
        id: set-ref
        run: |
          if [[ "${{ github.event_name }}" == "workflow_dispatch" && "${{ github.event.inputs.ref }}" != "" ]]; then
            echo "ref=${{ github.event.inputs.ref }}" >> $GITHUB_OUTPUT
          else
            echo "ref=${{ github.sha }}" >> $GITHUB_OUTPUT
          fi

  build:
    needs: determine-environment
    if: needs.determine-environment.outputs.environment != 'skip'
    uses: forus-coop/.github/.github/workflows/docker-build-push.yml@main
    with:
      image_tag: ${{ needs.determine-environment.outputs.ref }}
    secrets: inherit

  deploy:
    needs: [determine-environment, build]
    if: needs.determine-environment.outputs.environment != 'skip'
    uses: forus-coop/.github/.github/workflows/helm-deploy.yml@main
    with:
      environment: ${{ needs.determine-environment.outputs.environment }}
      app_name: ${{ github.event.inputs.app_name || github.event.repository.name }}
      namespace: ${{ github.event.inputs.namespace || needs.determine-environment.outputs.environment }}
      image_tag: ${{ needs.determine-environment.outputs.ref }}
    secrets: inherit
EOF
```

## Step 3: Create Helm Values Files

Copy and customize the Helm values files for each environment:

```bash
# Copy the Helm values files
mkdir -p helm
curl -o helm/sandbox.yaml https://raw.githubusercontent.com/forus-coop/.github/main/workflow-templates/helm-values-examples/sandbox.yaml
curl -o helm/staging.yaml https://raw.githubusercontent.com/forus-coop/.github/main/workflow-templates/helm-values-examples/staging.yaml
curl -o helm/production.yaml https://raw.githubusercontent.com/forus-coop/.github/main/workflow-templates/helm-values-examples/production.yaml
```

Edit the values files to customize them for your application's needs.

## Step 4: Set Up GitHub Environments

In your repository settings, create the following environments:
1. sandbox
2. staging
3. production

For each environment, you can configure:
- Environment-specific secrets
- Required reviewers for deployments
- Deployment branch restrictions

## Step 5: Set Up the Required Secrets

At the organization or repository level, set up the following secrets:

1. **AWS Credentials**:
   - If using access keys: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
   - If using OIDC: `AWS_ROLE_TO_ASSUME`

2. **Kubernetes Config Files** (environment-specific):
   - `ORG_KUBECTL_CONFIG_BASE64_SANDBOX`
   - `ORG_KUBECTL_CONFIG_BASE64_STAGING`
   - `ORG_KUBECTL_CONFIG_BASE64_PRODUCTION`

To generate a base64-encoded kubeconfig file:

```bash
cat ~/.kube/config | base64 -w 0
```

> **Important**: Note that GitHub Actions doesn't support dynamic secret names with string concatenation (like `secrets['ORG_KUBECTL_CONFIG_BASE64_' + environment]`). The workflow uses conditional steps to access the appropriate secret for each environment.

## Step 6: Create a Dockerfile

Create a Dockerfile in the root of your repository that builds your application.

## Step 7: Customize the Workflow (Optional)

Edit `.github/workflows/ci-cd.yml` to customize it for your application's specific needs.

Common customizations include:
- Adding build arguments for Docker
- Customizing Helm chart parameters
- Adding testing steps

For example, to customize the Docker build:

```yaml
build:
  uses: forus-coop/.github/.github/workflows/docker-build-push.yml@main
  with:
    image_tag: ${{ needs.determine-environment.outputs.ref }}
    docker_build_dir: './app'  # If your Dockerfile is in a subdirectory
    dockerfile_path: 'Dockerfile.prod'  # If you have a specific Dockerfile
  secrets: inherit
```

## Step 8: Commit and Push

Commit and push all these files to your repository:

```bash
git add .github/workflows/ helm/ Dockerfile
git commit -m "Add CI/CD pipeline"
git push
```

## Step 9: Verify the Workflow

After pushing to your repository, verify that the GitHub Actions workflow appears in the "Actions" tab and runs as expected.

## Access to Centralized Workflows

For this approach to work, ensure:

1. The `.github` repository in your organization is public, or
2. Your repository has been granted access to the workflows in the `.github` repository

To enable workflow access, go to your organization settings > Actions > General > Workflow permissions and select "Allow enterprise, organization, and repository workflows".

## Troubleshooting

If you encounter issues with the workflow:

1. Check the workflow logs in the GitHub Actions tab
2. Ensure all required secrets are set up correctly
3. Verify that your Dockerfile builds successfully locally
4. Check that your Helm values files are correctly formatted
5. Ensure that the AWS ECR repository exists and is accessible
6. Verify that the Kubernetes cluster is accessible with the provided kubeconfig 