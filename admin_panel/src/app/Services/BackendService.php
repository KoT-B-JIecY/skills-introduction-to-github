<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;

class BackendService
{
    private string $baseUrl;
    private string $apiKey;

    public function __construct()
    {
        $this->baseUrl = env('BACKEND_URL', 'http://backend:8000');
        $this->apiKey  = env('ADMIN_API_KEY', 'changeme');
    }

    private function client()
    {
        return Http::withHeaders(['X-API-KEY' => $this->apiKey]);
    }

    public function products()
    {
        return $this->client()->get("{$this->baseUrl}/admin/products")->json();
    }

    public function product(int $id)
    {
        return $this->client()->get("{$this->baseUrl}/admin/products/{$id}")->json();
    }

    public function saveProduct(array $data, ?int $id = null)
    {
        if ($id) {
            return $this->client()->put("{$this->baseUrl}/admin/products/{$id}", $data)->json();
        }
        return $this->client()->post("{$this->baseUrl}/admin/products", $data)->json();
    }

    public function deleteProduct(int $id): void
    {
        $this->client()->delete("{$this->baseUrl}/admin/products/{$id}");
    }

    public function orders()
    {
        return $this->client()->get("{$this->baseUrl}/admin/orders")->json();
    }

    public function order(int $id)
    {
        return $this->client()->get("{$this->baseUrl}/admin/orders/{$id}")->json();
    }
}