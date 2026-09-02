# Infrastructure — Terraform (Phase 7.3)

Provisions a single EC2 instance on AWS that runs the full application
stack via `docker compose up -d --build` (the same `docker-compose.yml`
already used locally) — Postgres, backend, and frontend, all on one host.

This is intentionally the simplest possible cloud deployment: one
instance, no load balancer, no managed database. It's the right first
step before Kubernetes (Phase 7.4) — get something real running on AWS
first, then containerize-orchestrate it properly once this works.

## What this creates

- A VPC with one public subnet
- A security group allowing SSH (22), frontend (5173), and backend API (8000)
- One EC2 instance (Ubuntu 22.04, `t3.small` by default)
- An Elastic IP, so the address doesn't change if the instance restarts
- A boot script that installs Docker, clones your repo, and runs `docker compose up -d --build` automatically

## Prerequisites

### 1. AWS CLI configured with credentials

```
aws configure
```
You'll need an AWS Access Key ID and Secret Access Key — create these in
the AWS Console under **IAM → Users → your user → Security credentials →
Create access key**.

### 2. An EC2 Key Pair (for SSH access)

In the AWS Console: **EC2 → Key Pairs → Create key pair**. Download the
`.pem` file and keep it somewhere safe — you'll need it to SSH in later,
and AWS won't let you download it again.

### 3. Terraform installed

Download from [terraform.io/downloads](https://developer.hashicorp.com/terraform/downloads).
Verify with:
```
terraform -version
```

### 4. Your repo must be public (or you'll need to add SSH deploy keys)

The instance clones your repo over plain `https://github.com/...` with no
credentials. If your repo is private, either make it public for this
deployment, or extend `user_data.sh` with a GitHub deploy key (ask if you
want this — not included here to keep the first deployment simple).

## Deploy

```
cd infra/terraform
terraform init
```

Create a `terraform.tfvars` file (don't commit this if it ever contains
secrets — it doesn't yet, but good habit):
```hcl
key_pair_name = "your-key-pair-name"     # exactly as named in AWS
repo_url      = "https://github.com/<you>/<repo>.git"
```

Then:
```
terraform plan    # review what will be created
terraform apply   # type "yes" when prompted
```

This takes a few minutes. When it finishes, Terraform prints the
`frontend_url` and `backend_url` outputs.

## After apply

The instance needs a few extra minutes after `terraform apply` finishes
to actually install Docker and start the containers (this happens via
the boot script, not instantly). Wait ~3-5 minutes, then open the
`frontend_url` from the output.

**If it's not up yet**, SSH in and check the boot log:
```
ssh -i <path-to-your-key.pem> ubuntu@<public_ip>
cat /var/log/user-data.log
```

## Testing from another machine

This is the whole point of deploying to AWS instead of `localhost` —
anyone with the public IP can now reach it:
- Open `http://<public_ip>:5173` in a browser on any machine
- Point the Student Agent at it: `python agent.py check --student-id <id> --env-id <id> --backend-url http://<public_ip>:8000`

## Tearing down

**Important**: this costs real money while running (a `t3.small` is
cheap, roughly a few cents/hour, but not free). Destroy it when you're
done testing:
```
terraform destroy
```

## What was NOT verified before this was handed off

Terraform isn't installable in the environment these files were authored
in (network restrictions), so `terraform plan`/`apply` could not be run
directly. What WAS verified: every `.tf` file was parsed with a real HCL
parser (all 6 files syntactically valid), and every variable/resource
cross-reference was checked programmatically for typos or dangling
references (all consistent). The actual AWS provisioning is untested —
please run `terraform plan` first and share the output before `apply`,
so we can catch anything before it creates real resources.
