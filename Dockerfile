# AJ Atelier – PHP 8.3 + Apache, Document Root = public/
FROM php:8.3-apache

RUN a2enmod rewrite headers deflate expires remoteip \
 && sed -ri 's#/var/www/html#/var/www/site/public#g' /etc/apache2/sites-available/000-default.conf /etc/apache2/apache2.conf \
 && printf '<Directory /var/www/site/public>\n  AllowOverride All\n  Require all granted\n</Directory>\nRemoteIPHeader X-Forwarded-For\nRemoteIPTrustedProxy 172.16.0.0/12\nServerTokens Prod\nServerSignature Off\n' > /etc/apache2/conf-enabled/site.conf \
 && printf 'expose_php=Off\ndate.timezone=Europe/Berlin\nsession.cookie_httponly=1\nupload_max_filesize=2M\npost_max_size=2M\n' > /usr/local/etc/php/conf.d/site.ini \
 && cp /usr/local/etc/php/php.ini-production /usr/local/etc/php/php.ini

WORKDIR /var/www/site
COPY app/ app/
COPY public/ public/
RUN mkdir -p app/data && chown -R www-data:www-data app/data

HEALTHCHECK --interval=60s --timeout=5s CMD php -r 'exit(@fsockopen("127.0.0.1", 80) ? 0 : 1);'
