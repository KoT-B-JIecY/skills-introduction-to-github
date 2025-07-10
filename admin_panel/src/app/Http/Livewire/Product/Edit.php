<?php

namespace App\Http\Livewire\Product;

use App\Services\BackendService;
use Livewire\Component;
use Illuminate\Support\Facades\Redirect;

class Edit extends Component
{
    public int $productId;
    public string $title = '';
    public int $uc_amount = 0;
    public float $price_usd = 0;
    public bool $is_active = true;

    protected BackendService $backend;

    protected array $rules = [
        'title' => 'required|string',
        'uc_amount' => 'required|integer|min:1',
        'price_usd' => 'required|numeric|min:0',
        'is_active' => 'boolean',
    ];

    public function mount(BackendService $backend, int $product)
    {
        $this->backend = $backend;
        $this->productId = $product;
        $data = $this->backend->product($product);
        $this->fill($data);
    }

    public function save()
    {
        $this->validate();
        $payload = [
            'title' => $this->title,
            'uc_amount' => $this->uc_amount,
            'price_usd' => $this->price_usd,
            'is_active' => $this->is_active,
        ];
        $this->backend->saveProduct($payload, $this->productId);
        session()->flash('success', 'Product saved');
        return Redirect::route('admin.products.index');
    }

    public function render()
    {
        return view('livewire.product.edit');
    }
}