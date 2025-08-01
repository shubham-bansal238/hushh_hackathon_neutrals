// Utility for updating product status via backend API
export async function updateProductStatus(id: number, newStatus: string) {
  const res = await fetch('http://localhost:5000/products/update-status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, newStatus })
  });
  if (!res.ok) throw new Error('Failed to update product status');
  return res.json();
}

export async function fetchProducts() {
  const res = await fetch('http://localhost:5000/products');
  if (!res.ok) throw new Error('Failed to fetch products');
  return res.json();
}
