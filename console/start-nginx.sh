#!/bin/sh
export PORT=${PORT:-80}
envsubst '$PORT' < /etc/nginx/conf.d/default.conf > /tmp/nginx.conf
cp /tmp/nginx.conf /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
