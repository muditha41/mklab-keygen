# Let's Encrypt (Certbot) for SWAPS

Use Certbot to obtain and renew TLS certificates so Nginx can serve HTTPS.

## One-time setup (host or container)

1. Ensure Nginx is running and `/.well-known/acme-challenge/` is served from `/var/www/certbot` (see `nginx.conf`).

2. Get a certificate (replace `protection.yourserver.com` and `admin@yourserver.com`):

   ```bash
   docker run --rm -v deploy_certbot_conf:/etc/letsencrypt -v deploy_certbot_www:/var/www/certbot \
     certbot certonly --webroot -w /var/www/certbot \
     -d protection.yourserver.com \
     --email admin@yourserver.com --agree-tos --no-eff-email
   ```

3. Update `deploy/nginx/nginx.conf`: add the HTTPS server block (see `nginx.ssl.conf`), set `server_name` and `ssl_certificate` paths to your domain and `/etc/letsencrypt/live/protection.yourserver.com/...`. Reload Nginx.

## Auto-renewal (cron)

Certbot recommends renewing every 12 weeks. Add a cron job (or use a systemd timer):

```bash
0 0 1 * * docker run --rm -v deploy_certbot_conf:/etc/letsencrypt -v deploy_certbot_www:/var/www/certbot \
  certbot renew --quiet && docker compose -f deploy/docker-compose.yml exec nginx nginx -s reload
```

Adjust the path to `docker compose` and the project path as needed.
