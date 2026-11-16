FROM apache/hive:4.0.0

USER root
# bullseye is EOL: deb.debian.org still serves the apt indexes but its
# security pool files are gone (404), so a fresh build dies in apt-get
# install. Point apt at archive.debian.org, which keeps the whole distro
# (index and pool consistent). Release files there are expired, so disable
# the Valid-Until check.
RUN for f in /etc/apt/sources.list /etc/apt/sources.list.d/*.list; do \
      if [ -f "$f" ]; then \
        sed -i -e 's|deb.debian.org|archive.debian.org|g' \
               -e 's|security.debian.org|archive.debian.org|g' "$f"; \
      fi; \
    done \
  && apt-get update -o Acquire::Check-Valid-Until=false \
  && apt-get install -y --no-install-recommends gettext-base netcat-openbsd curl postgresql-client \
  && curl -fsSL -o /opt/hive/lib/postgresql-42.7.3.jar https://jdbc.postgresql.org/download/postgresql-42.7.3.jar \
  && rm -rf /var/lib/apt/lists/*

# Add S3A filesystem JARs (present in Hadoop tools but not on Hive classpath by default)
RUN ln -s /opt/hadoop/share/hadoop/tools/lib/hadoop-aws-3.3.6.jar /opt/hive/lib/ \
 && ln -s /opt/hadoop/share/hadoop/tools/lib/aws-java-sdk-bundle-1.12.367.jar /opt/hive/lib/

COPY metastore-site.xml.template /opt/hive/conf/metastore-site.xml.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
