<?php

use Illuminate\Support\Facades\Route;
use App\Http\Livewire\Product\Index as ProductIndex;
use App\Http\Livewire\Product\Edit as ProductEdit;
use App\Http\Livewire\Order\Index as OrderIndex;
use App\Http\Livewire\Order\Show as OrderShow;
use App\Http\Livewire\Settings\Payments as PaymentSettings;

Route::middleware(['auth', 'verified'])->group(function () {
    Route::get('/admin/products', ProductIndex::class)->name('admin.products.index');
    Route::get('/admin/products/{product}', ProductEdit::class)->name('admin.products.edit');

    Route::get('/admin/orders', OrderIndex::class)->name('admin.orders.index');
    Route::get('/admin/orders/{order}', OrderShow::class)->name('admin.orders.show');

    Route::get('/admin/settings/payments', PaymentSettings::class)->name('admin.settings.payments');
});