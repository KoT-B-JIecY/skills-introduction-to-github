# --- Build stage ---
FROM composer:2 AS builder
WORKDIR /var/www/html

# Create base Laravel project
RUN composer create-project --prefer-dist laravel/laravel laravel-app \
    && cd laravel-app \
    # Install Jetstream (includes Fortify + 2FA) \
    && composer require laravel/jetstream --no-interaction --no-progress \
    && php artisan jetstream:install livewire --no-interaction \
    && php artisan key:generate --force

# --- Runtime stage ---
FROM php:8.2-apache
WORKDIR /var/www/html

# Enable Apache modules
RUN a2enmod rewrite

# Copy application from builder stage
COPY --from=builder /var/www/html/laravel-app /var/www/html

# Set correct document root
ENV APACHE_DOCUMENT_ROOT /var/www/html/public
RUN sed -ri -e 's!/var/www/html!/var/www/html/public!g' /etc/apache2/sites-available/*.conf \
    && sed -ri -e 's!/var/www/!/var/www/html/public!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

# Expose port and start apache
EXPOSE 80
CMD ["bash", "-c", "php artisan migrate --force && apache2-foreground"]