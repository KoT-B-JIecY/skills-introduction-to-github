<?php

namespace App\Http\Livewire\Product;

use App\Services\BackendService;
use Livewire\Component;

class Index extends Component
{
    public array $products = [];
    protected BackendService $backend;

    public function mount(BackendService $backend)
    {
        $this->backend = $backend;
        $this->refresh();
    }

    public function refresh(): void
    {
        $this->products = $this->backend->products();
    }

    public function render()
    {
        return view('livewire.product.index');
    }
}