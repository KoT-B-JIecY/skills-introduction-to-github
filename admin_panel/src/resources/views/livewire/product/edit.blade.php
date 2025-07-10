<div>
    <h1 class="text-2xl font-semibold mb-4">Edit Product #{{ $productId }}</h1>

    @if (session()->has('success'))
        <div class="p-2 bg-green-200 text-green-800 mb-4">{{ session('success') }}</div>
    @endif

    <form wire:submit.prevent="save" class="space-y-4">
        <div>
            <label class="block">Title</label>
            <input type="text" wire:model="title" class="border p-2 w-full">
            @error('title') <span class="text-red-600">{{ $message }}</span> @enderror
        </div>
        <div>
            <label class="block">UC Amount</label>
            <input type="number" wire:model="uc_amount" class="border p-2 w-full">
            @error('uc_amount') <span class="text-red-600">{{ $message }}</span> @enderror
        </div>
        <div>
            <label class="block">Price USD</label>
            <input type="number" step="0.01" wire:model="price_usd" class="border p-2 w-full">
            @error('price_usd') <span class="text-red-600">{{ $message }}</span> @enderror
        </div>
        <div>
            <label class="inline-flex items-center">
                <input type="checkbox" wire:model="is_active" class="form-checkbox">
                <span class="ml-2">Active</span>
            </label>
        </div>
        <button type="submit" class="px-4 py-2 bg-blue-600 text-white">Save</button>
    </form>
</div>