<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('products', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->integer('uc_amount');
            $table->decimal('price_usd', 8, 2);
            $table->text('description')->nullable();
            $table->boolean('active')->default(true);
            $table->json('extra')->nullable();
            $table->timestamps();
        });

        Schema::create('orders', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained('users');
            $table->foreignId('product_id')->constrained('products');
            $table->enum('status', ['processing', 'paid', 'delivered', 'cancelled'])->default('processing');
            $table->decimal('amount', 8, 2);
            $table->string('payment_method');
            $table->string('transaction_id')->nullable();
            $table->json('delivery_data')->nullable();
            $table->timestamps();
        });

        Schema::create('payments', function (Blueprint $table) {
            $table->id();
            $table->foreignId('order_id')->constrained('orders');
            $table->string('provider');
            $table->string('transaction_id');
            $table->decimal('amount', 8, 2);
            $table->string('currency', 10);
            $table->enum('status', ['pending', 'confirmed', 'failed'])->default('pending');
            $table->json('meta')->nullable();
            $table->timestamps();
        });

        Schema::create('promo_codes', function (Blueprint $table) {
            $table->id();
            $table->string('code')->unique();
            $table->decimal('discount', 8, 2)->nullable();
            $table->integer('uc_bonus')->nullable();
            $table->timestamp('expires_at')->nullable();
            $table->integer('usage_limit')->nullable();
            $table->integer('used_count')->default(0);
            $table->timestamps();
        });

        Schema::create('referrals', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained('users');
            $table->foreignId('referrer_id')->constrained('users');
            $table->decimal('bonus', 8, 2)->default(0);
            $table->timestamps();
        });

        Schema::create('notifications', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->nullable()->constrained('users');
            $table->string('type');
            $table->text('message');
            $table->boolean('read')->default(false);
            $table->timestamps();
        });

        Schema::create('logs', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->nullable()->constrained('users');
            $table->string('action');
            $table->json('data')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('logs');
        Schema::dropIfExists('notifications');
        Schema::dropIfExists('referrals');
        Schema::dropIfExists('promo_codes');
        Schema::dropIfExists('payments');
        Schema::dropIfExists('orders');
        Schema::dropIfExists('products');
    }
};