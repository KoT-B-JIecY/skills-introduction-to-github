<div>
    <h1 class="text-2xl font-semibold mb-4">Order #{{ $order['id'] }}</h1>

    <div class="space-y-2">
        <p><b>User ID:</b> {{ $order['user_id'] }}</p>
        <p><b>Product ID:</b> {{ $order['product_id'] }}</p>
        <p><b>Quantity:</b> {{ $order['qty'] }}</p>
        <p><b>Amount:</b> ${{ $order['amount'] }}</p>
        <p><b>Status:</b> {{ $order['status'] }}</p>
        <p><b>Created at:</b> {{ $order['created_at'] }}</p>
    </div>

    <a href="{{ route('admin.orders.index') }}" class="text-blue-600 underline mt-4 inline-block">Back to Orders</a>
</div>