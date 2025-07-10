<?php

namespace App\Http\Livewire\Settings;

use Livewire\Component;

class Payments extends Component
{
    public string $public_note = 'Payment keys are managed via env variables';

    public function render()
    {
        return view('livewire.settings.payments');
    }
}