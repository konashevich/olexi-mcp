# Oracle Cloud — create the VM (one-time)

Tenancy: **akonashevich** · Region: **Australia East (Sydney)** `ap-sydney-1`

## 1. Instance

Compute → Instances → **Create instance**

| Field | Value |
|-------|--------|
| Name | `olexi-unified` |
| Image | Ubuntu 22.04 **aarch64** |
| Shape | `VM.Standard.A1.Flex` — **1 OCPU**, **6 GB** RAM |
| Boot volume | 50 GB |
| SSH key | Paste your public key (see below) |

**SSH public key** (from deploy machine):

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKsGEVIfLqDdX+E+2ZcwLhPZdqv3lj1bOhRRnsY86vjX a.konashevich@gmail.com
```

Networking: assign **public IPv4** (reserved if available).

## 2. Firewall (security list / NSG)

Allow inbound **TCP 22, 80, 443** from `0.0.0.0/0` (tighten SSH later if desired).

## 3. Bootstrap (from your laptop or Cloud Shell)

Replace `VM_IP` with the instance public IP:

```bash
export HOST_GOOGLE_API_KEY='(loaded by agent — or from GCP secret)'
ssh -o StrictHostKeyChecking=accept-new ubuntu@VM_IP \
  'curl -fsSL https://raw.githubusercontent.com/konashevich/olexi-mcp/main/deploy/oracle/bootstrap-vm.sh | sudo bash -s'
```

Or agent runs:

```bash
scp deploy/oracle/bootstrap-vm.sh ubuntu@VM_IP:/tmp/
ssh ubuntu@VM_IP "sudo HOST_GOOGLE_API_KEY='$HOST_GOOGLE_API_KEY' bash /tmp/bootstrap-vm.sh"
```

## 4. DNS (olexi.legal)

| Host | Type | Value |
|------|------|--------|
| `mcp-api` | A | VM public IP |
| `ext` | A | VM public IP |

Keep `mcp.olexi.legal` on GitHub Pages (CNAME unchanged).

## 5. Verify

```bash
curl -fsS https://mcp-api.olexi.legal/
curl -fsS https://ext.olexi.legal/health
```

Then delete Cloud Run services `olexi-mcp-root-au` and `olexi-extension-host`.
