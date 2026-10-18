// Code under test that calls an HTTP API. fetch is passed in (default: the global), so a test can give it a stub.
export async function fetchTip(fetchImpl = globalThis.fetch) {
  try {
    const response = await fetchImpl('https://tips.example.com/today');
    if (!response.ok) return 'Tip unavailable.';
    return (await response.json()).text ?? 'Tip unavailable.';
  } catch {
    return 'Tip unavailable.';
  }
}
