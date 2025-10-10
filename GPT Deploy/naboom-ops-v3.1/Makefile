SHELL := /bin/bash

SITE   ?= /etc/nginx/sites-available/naboomneighbornet.net.za
SNIP   ?= /etc/nginx/snippets/proxy-common.conf
SYSTEMD?= /etc/systemd/system
SCRIPTS?= /usr/local/bin
ENV    ?= /etc/default/naboom
MOSQ   ?= /etc/mosquitto

install:
	install -d $(dir $(SITE)) $(dir $(SNIP)) /etc/nginx/conf.d $(SYSTEMD) $(SCRIPTS) $(MOSQ) /etc/logrotate.d
	install -m 0644 nginx/sites-available/naboomneighbornet.net.za $(SITE)
	install -m 0644 nginx/snippets/proxy-common.conf $(SNIP)
	install -m 0644 nginx/conf.d/00-core-http3.conf /etc/nginx/conf.d/00-core-http3.conf
	install -m 0644 mosquitto/mosquitto.conf $(MOSQ)/mosquitto.conf
	install -m 0640 mosquitto/acl $(MOSQ)/acl || true
	install -m 0600 mosquitto/passwd $(MOSQ)/passwd || true
	install -m 0644 systemd/naboom-gunicorn.service $(SYSTEMD)/naboom-gunicorn.service
	install -m 0644 systemd/naboom-daphne.service $(SYSTEMD)/naboom-daphne.service
	install -m 0644 systemd/naboom-celery.service $(SYSTEMD)/naboom-celery.service
	install -m 0644 systemd/naboom-celerybeat.service $(SYSTEMD)/naboom-celerybeat.service
	install -m 0644 systemd/naboom-mqtt.service $(SYSTEMD)/naboom-mqtt.service
	install -m 0755 scripts/*.sh $(SCRIPTS)/
	install -m 0755 scripts/naboom-mqtt-subscriber.py $(SCRIPTS)/
	install -m 0755 scripts/verify-mqtt-flow.py $(SCRIPTS)/
	install -m 0644 logrotate/mosquitto /etc/logrotate.d/mosquitto
	[ -f $(ENV) ] || install -m 0644 .env.sample $(ENV)

deploy:
	systemctl daemon-reload
	systemctl enable naboom-gunicorn naboom-daphne naboom-celery naboom-celerybeat naboom-mqtt
	systemctl restart mosquitto || systemctl start mosquitto
	nginx -t && systemctl reload nginx || systemctl restart nginx
	systemctl start naboom-gunicorn naboom-daphne naboom-celery naboom-celerybeat naboom-mqtt

verify:
	$(SCRIPTS)/gunicorn-health-check.sh
	$(SCRIPTS)/daphne-health-check.sh
	REDIS_URL=$$(. $(ENV); echo redis://$$REDIS_CELERY_USER:$$REDIS_CELERY_PASSWORD@$$REDIS_APP_HOST:$$REDIS_APP_PORT/$$REDIS_CELERY_DB) $(SCRIPTS)/celery-redis-acl-test.sh
	$(SCRIPTS)/celery-health-check.sh || true
	$(SCRIPTS)/celerybeat-health-check.sh || true
	$(SCRIPTS)/mqtt-dependency-check.sh
	$(SCRIPTS)/mqtt-health-check.sh || true
	$(SCRIPTS)/monitor-http3-deployment.sh naboomneighbornet.net.za || true

verify-h3-ocsp:
	$(SCRIPTS)/verify-ocsp.sh naboomneighbornet.net.za

verify-ws:
	$(SCRIPTS)/verify-ws.sh naboomneighbornet.net.za /ws/ 443

verify-mqtt-ws:
	$(SCRIPTS)/verify-mqtt-ws.sh naboomneighbornet.net.za /mqtt 443

verify-mqtt-flow:
	MQTT_USER=$$(. $(ENV); echo $$MQTT_USER) MQTT_PASSWORD=$$(. $(ENV); echo $$MQTT_PASSWORD) \
	MQTT_FLOW_HOST=naboomneighbornet.net.za MQTT_FLOW_PORT=443 MQTT_FLOW_PATH=/mqtt \
	$(SCRIPTS)/verify-mqtt-flow.py

rollback:
	bash $(SCRIPTS)/rollback.sh

status:
	systemctl --no-pager status naboom-gunicorn naboom-daphne naboom-celery naboom-celerybeat naboom-mqtt || true

logs:
	journalctl -u naboom-gunicorn -u naboom-daphne -u naboom-celery -u naboom-celerybeat -u naboom-mqtt --no-pager -n 200

tune:
	@echo "CPU cores: $$(nproc 2>/dev/null || echo unknown)"
	@echo "Gunicorn profile: $${GUNICORN_PROFILE:-io}"
	@echo "Celery profile:   $${CELERY_PROFILE:-io}"

.PHONY: install deploy verify verify-h3-ocsp verify-ws verify-mqtt-ws verify-mqtt-flow rollback status logs tune
