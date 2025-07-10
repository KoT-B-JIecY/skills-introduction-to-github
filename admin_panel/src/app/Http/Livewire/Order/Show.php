<?php

namespace App\Http\Livewire\Order;

use App\Services\BackendService;
use Livewire\Component;

class Show extends Component
{
    public int $orderId;
    public array $order = [];
    protected BackendService $backend;

    public function mount(BackendService $backend, int $order)
    {
        $this->backend = $backend;
        $this->orderId = $order;
        $this->order = $this->backend->order($order);
    }

    public function render()
    {
        return view('livewire.order.show');
    }
}