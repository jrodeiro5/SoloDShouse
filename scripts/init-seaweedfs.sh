#!/bin/sh
# Initialize SeaweedFS S3 buckets on first startup.
# Called by `make up` after seaweedfs is healthy.
set -e

ENDPOINT="${OBJECT_STORE_ENDPOINT:-http://localhost:8333}"
ACCESS_KEY="${S3_ACCESS_KEY:-solodshouse}"
SECRET_KEY="${S3_SECRET_KEY:-solodshouse123}"
DATA_BUCKET="${DATA_BUCKET:-solodshouse-data}"
MLFLOW_BUCKET="${MLFLOW_ARTIFACT_BUCKET:-solodshouse-mlflow}"

for BUCKET in "$DATA_BUCKET" "$MLFLOW_BUCKET"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        --aws-sigv4 "aws:amz:us-east-1:s3" \
        --user "${ACCESS_KEY}:${SECRET_KEY}" \
        -X HEAD "${ENDPOINT}/${BUCKET}" 2>/dev/null || echo "000")

    if [ "$STATUS" = "200" ] || [ "$STATUS" = "301" ]; then
        echo "Bucket already exists: ${BUCKET}"
    else
        curl -s -o /dev/null -w "%{http_code}" \
            --aws-sigv4 "aws:amz:us-east-1:s3" \
            --user "${ACCESS_KEY}:${SECRET_KEY}" \
            -X PUT "${ENDPOINT}/${BUCKET}" \
            -H "Content-Length: 0"
        echo "Created bucket: ${BUCKET}"
    fi
done
