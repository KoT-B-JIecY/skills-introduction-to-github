<?php

namespace App\Http\Livewire\Order;

use App\Services\BackendService;
use Livewire\Component;

class Index extends Component
{
    public array $orders = [];
    protected BackendService $backend;

    public function mount(BackendService $backend)
    {
        $this->backend = $backend;
        $this->orders = $this->backend->orders();
    }

    public function render()
    {
        return view('livewire.order.index');
    }
}