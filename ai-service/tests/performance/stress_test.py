import asyncio
import time
import httpx
import statistics

async def stress_test_endpoint(url: str, num_requests: int):
    """
    Simulate high volume of queries to measure p95 latency and failure rates.
    """
    latencies = []
    failures = 0
    
    print(f"Starting Stress Test: {num_requests} requests to {url}")
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for _ in range(num_requests):
            tasks.append(client.post(url, json={"query": "Safe test query", "role": "admin"}, headers={"Authorization": "Bearer MOCK_TOKEN"}))
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()
        
    for res in results:
        if isinstance(res, httpx.Response) and res.status_code == 200:
            latencies.append(res.elapsed.total_seconds())
        else:
            failures += 1
            
    total_time = end_time - start_time
    
    print("\n--- RESULTS ---")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Throughput: {len(results)/total_time:.2f} req/s")
    if latencies:
        print(f"P50 Latency: {statistics.median(latencies):.3f}s")
        print(f"P95 Latency: {statistics.quantiles(latencies, n=100)[94]:.3f}s")
    print(f"Failure Rate: {(failures/len(results))*100:.1f}%")

if __name__ == "__main__":
    # In practice, run this against a staging environment
    # asyncio.run(stress_test_endpoint("http://localhost:8000/v1/query", 100))
    pass
