<div>
    <h1 class="text-2xl font-semibold mb-4">Products</h1>

    <table class="min-w-full bg-white">
        <thead>
            <tr>
                <th class="px-4 py-2">ID</th>
                <th class="px-4 py-2">Title</th>
                <th class="px-4 py-2">UC</th>
                <th class="px-4 py-2">Price USD</th>
                <th class="px-4 py-2">Active</th>
            </tr>
        </thead>
        <tbody>
            @foreach($products as $prod)
                <tr>
                    <td class="border px-4 py-2">{{ $prod['id'] }}</td>
                    <td class="border px-4 py-2">
                        <a href="{{ route('admin.products.edit', $prod['id']) }}" class="text-blue-600 underline">{{ $prod['title'] }}</a>
                    </td>
                    <td class="border px-4 py-2">{{ $prod['uc_amount'] }}</td>
                    <td class="border px-4 py-2">${{ $prod['price_usd'] }}</td>
                    <td class="border px-4 py-2">{{ $prod['is_active'] ? 'Yes' : 'No' }}</td>
                </tr>
            @endforeach
        </tbody>
    </table>
</div>