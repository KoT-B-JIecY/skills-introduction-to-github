<div>
    <h1 class="text-2xl font-semibold mb-4">Orders</h1>

    <table class="min-w-full bg-white">
        <thead>
            <tr>
                <th class="px-2 py-2">ID</th>
                <th class="px-2 py-2">User</th>
                <th class="px-2 py-2">Product</th>
                <th class="px-2 py-2">Qty</th>
                <th class="px-2 py-2">Amount</th>
                <th class="px-2 py-2">Status</th>
            </tr>
        </thead>
        <tbody>
            @foreach($orders as $o)
                <tr>
                    <td class="border px-2 py-1"><a href="{{ route('admin.orders.show', $o['id']) }}" class="underline text-blue-600">{{ $o['id'] }}</a></td>
                    <td class="border px-2 py-1">{{ $o['user_id'] }}</td>
                    <td class="border px-2 py-1">{{ $o['product_id'] }}</td>
                    <td class="border px-2 py-1">{{ $o['qty'] }}</td>
                    <td class="border px-2 py-1">${{ $o['amount'] }}</td>
                    <td class="border px-2 py-1">{{ $o['status'] }}</td>
                </tr>
            @endforeach
        </tbody>
    </table>
</div>