FROM apache/hive:4.0.0

USER root
# bullseye LTS ended 2026-08-31: the debian-security pool on deb.debian.org no
# longer has bullseye .debs (apt 404s), while the main pool still resolves.
# Drop the security source so installs come from main only.
RUN sed -i '/debian-security/d' /etc/apt/sources.list \
  && apt-get update \
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
