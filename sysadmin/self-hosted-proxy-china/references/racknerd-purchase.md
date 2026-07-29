# RackNerd VPS Purchase Walkthrough

## Deal Page
https://www.racknerd.com/specials/

## Recommended Plan
**1 GB KVM VPS Special** — $21.99/year (~¥158)
- 1 vCPU, 1 GB RAM, 20 GB SSD
- 3 TB monthly transfer, 1 Gbps port
- Sufficient for personal proxy use

## Purchase Steps

1. Click "Order Now" on the 1 GB plan
2. **Configuration**:
   - Location: **Los Angeles DC-02** or **San Jose** (West coast → China)
   - OS: **Debian 12** (best Xray compatibility)
3. **Billing Information**:
   - Name: any English name
   - Email: real email (receives root password)
   - Address: fake US address (not verified)
     - e.g., `123 Mission Street, San Francisco, CA 94105`
   - Phone: leave blank (optional)
4. **Payment**: Select "Stripe支付宝" (Alipay)
   - If payment page crashes, turn off existing VPN and retry
   - Alternative: PayPal

## After Purchase
- Wait 2-10 minutes for provisioning
- Check email for "Your RackNerd VPS is Ready"
- Email contains: IP, root password, SSH port, SolusVM panel credentials

## SolusVM Panel
URL: https://nerdvm.racknerd.com/
Used for: reboot, reinstall OS, console access, backups.
Credentials are separate from root SSH password.
