# Grafana dashboards and alert rules

`dashboards/logiflow-wms.json` is the portable Grafana V2 export of the LogiFlow WMS dashboard. It includes CPU, memory, and application log panels.

`alert-rules.yaml` is a Grafana file-provisioning export of the `logiflow` evaluation group. It contains:

- `LogiFlow HTTP errors`: counts HTTP 4xx/5xx log lines over five minutes; alert threshold is greater than zero.
- `LogiFlow memory high`: alerts when the maximum working set for a LogiFlow pod exceeds 100 MiB for one minute.

Both rules send notifications to the `logiflow-email` contact point. The rules reference this contact point, but the contact point itself is currently created in Grafana and is not provisioned from Git. Recreate it after a fresh Grafana install before expecting email alerts.

SMTP server settings are separate and stored in the local, Git-ignored `k8s/monitoring/grafana-smtp-values.yaml` file. Recreate that file locally when configuring email delivery. Never commit SMTP credentials.

## Restore the dashboard

1. In Grafana, open **Dashboards → New → Import dashboard**.
2. Upload `dashboards/logiflow-wms.json`.
3. Select the `LogiFlow` folder and map the Prometheus and Loki data sources if Grafana asks.
4. Click **Import**.

## Restore alert rules

`alert-rules.yaml` uses Grafana's file-provisioning format; it is not imported through the dashboard import page. To provision it, mount the file into Grafana's `/etc/grafana/provisioning/alerting/` directory and restart or upgrade Grafana. The `LogiFlow` folder, `logiflow` evaluation group, Prometheus and Loki data sources, and `logiflow-email` contact point must exist. If a recreated Loki data source has a different UID, update the Loki `datasourceUid` and model UID in the YAML before provisioning it.

Keep this directory in Git as the recoverable source for the dashboard and alert rule definitions. The SMTP credentials stay local and out of Git; the email contact point remains a manual Grafana setup step.
