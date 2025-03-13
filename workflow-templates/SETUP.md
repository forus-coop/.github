# Setting Up CI/CD in a New Repository

This guide will help you set up the CI/CD pipeline in a new repository using our organization's workflow templates.

## Step 1: Create the Required Directory Structure

```bash
# Create the necessary directories
mkdir -p .github/workflows
mkdir -p helm
```

## Step 2: Copy the Workflow Files

Copy the main workflow file to your repository:

```bash
# Create the main workflow file
cp /path/to/workflow-templates/example-usage.yml .github/workflows/ci-cd.yml
```

## Step 3: Copy the Helm Values Files

Copy and customize the Helm values files for each environment:

```bash
# Copy the Helm values files
cp /path/to/workflow-templates/helm-values-examples/sandbox.yaml helm/
cp /path/to/workflow-templates/helm-values-examples/staging.yaml helm/
cp /path/to/workflow-templates/helm-values-examples/production.yaml helm/
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

2. **Kubernetes Config Files**:
   - `ORG_KUBECTL_CONFIG_BASE64_SANDBOX`
   - `ORG_KUBECTL_CONFIG_BASE64_STAGING`
   - `ORG_KUBECTL_CONFIG_BASE64_PRODUCTION`

To generate a base64-encoded kubeconfig file:

```bash
cat ~/.kube/config | base64 -w 0
```

## Step 6: Create a Dockerfile

Create a Dockerfile in the root of your repository that builds your application.

## Step 7: Customize the Workflow (Optional)

Edit `.github/workflows/ci-cd.yml` to customize it for your application's specific needs.

Common customizations include:
- Changing the Dockerfile path
- Adding build arguments
- Customizing Helm chart parameters
- Adding testing steps

## Step 8: Commit and Push

Commit and push all these files to your repository:

```bash
git add .github/workflows/ci-cd.yml helm/ Dockerfile
git commit -m "Add CI/CD pipeline"
git push
```

## Step 9: Verify the Workflow

After pushing to your repository, verify that the GitHub Actions workflow appears in the "Actions" tab and runs as expected.

## Troubleshooting

If you encounter issues with the workflow:

1. Check the workflow logs in the GitHub Actions tab
2. Ensure all required secrets are set up correctly
3. Verify that your Dockerfile builds successfully locally
4. Check that your Helm values files are correctly formatted
5. Ensure that the AWS ECR repository exists and is accessible
6. Verify that the Kubernetes cluster is accessible with the provided kubeconfig 