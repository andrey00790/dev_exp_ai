import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8001';

test.describe('AI Assistant E2E Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set longer timeout for E2E tests
    test.setTimeout(120000); // 2 minutes
  });

  test('Health endpoint should return healthy status', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/health`);
    expect(response?.status()).toBe(200);
    
    const content = await page.content();
    expect(content).toContain('healthy');
  });

  test('API documentation should be accessible', async ({ page }) => {
    await page.goto(`${BASE_URL}/docs`);
    
    // Check if Swagger UI loaded
    await expect(page.locator('.swagger-ui')).toBeVisible({ timeout: 30000 });
    
    // Check for API title
    await expect(page.locator('h2')).toContainText('AI Assistant API');
  });

  test('OpenAPI JSON schema should be valid', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/openapi.json`);
    expect(response?.status()).toBe(200);
    
    const content = await page.content();
    const jsonContent = JSON.parse(content);
    
    expect(jsonContent).toHaveProperty('openapi');
    expect(jsonContent).toHaveProperty('info');
    expect(jsonContent).toHaveProperty('paths');
  });

  test('Monitoring endpoints should be accessible', async ({ page }) => {
    // Test metrics endpoint
    const metricsResponse = await page.goto(`${BASE_URL}/metrics`);
    expect(metricsResponse?.status()).toBe(200);
    
    // Test current metrics API
    const currentMetricsResponse = await page.goto(`${BASE_URL}/api/v1/monitoring/metrics/current`);
    expect(currentMetricsResponse?.status()).toBe(200);
    
    const metricsContent = await page.content();
    const metricsData = JSON.parse(metricsContent);
    
    expect(metricsData).toHaveProperty('cpu_usage');
    expect(metricsData).toHaveProperty('memory_usage');
    expect(metricsData).toHaveProperty('timestamp');
  });

  test('WebSocket statistics should be available', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/api/v1/ws/stats`);
    expect(response?.status()).toBe(200);
    
    const content = await page.content();
    const statsData = JSON.parse(content);
    
    expect(statsData).toHaveProperty('active_connections');
    expect(statsData).toHaveProperty('total_connections');
    expect(typeof statsData.active_connections).toBe('number');
    expect(typeof statsData.total_connections).toBe('number');
  });

  test('Auth budget status should be accessible', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/api/v1/auth/budget/status`);
    expect(response?.status()).toBe(200);
    
    const content = await page.content();
    const budgetData = JSON.parse(content);
    
    expect(budgetData).toHaveProperty('current_usage');
    expect(budgetData).toHaveProperty('budget_limit');
  });

  test('Performance summary should be available', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/api/v1/monitoring/performance/summary`);
    expect(response?.status()).toBe(200);
    
    const content = await page.content();
    const perfData = JSON.parse(content);
    
    expect(perfData).toHaveProperty('avg_response_time');
    expect(perfData).toHaveProperty('requests_per_second');
    expect(typeof perfData.avg_response_time).toBe('number');
    expect(typeof perfData.requests_per_second).toBe('number');
  });

  test('Optimization endpoints should be accessible', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/api/v1/optimization/history`);
    expect(response?.status()).toBe(200);
    
    const content = await page.content();
    const historyData = JSON.parse(content);
    
    expect(Array.isArray(historyData)).toBe(true);
  });

  test('Realtime monitoring health should be okay', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/api/v1/realtime-monitoring/health`);
    expect(response?.status()).toBe(200);
    
    const content = await page.content();
    const healthData = JSON.parse(content);
    
    expect(healthData).toHaveProperty('status');
    expect(healthData.status).toBe('healthy');
  });

  test('API health check should show all services connected', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/api/v1/health`);
    expect(response?.status()).toBe(200);
    
    const content = await page.content();
    const healthData = JSON.parse(content);
    
    expect(healthData).toHaveProperty('status');
    expect(healthData.status).toBe('ok');
    expect(healthData).toHaveProperty('checks');
    
    // Check database connectivity
    expect(healthData.checks).toHaveProperty('database');
    expect(healthData.checks.database).toBe('connected');
    
    // Check Redis connectivity
    expect(healthData.checks).toHaveProperty('redis');
    expect(healthData.checks.redis).toBe('connected');
  });

  test('Response times should be within acceptable limits', async ({ page }) => {
    const startTime = Date.now();
    const response = await page.goto(`${BASE_URL}/health`);
    const endTime = Date.now();
    
    expect(response?.status()).toBe(200);
    
    const responseTime = endTime - startTime;
    expect(responseTime).toBeLessThan(2000); // Should respond within 2 seconds
  });

  test('Multiple concurrent requests should succeed', async ({ page, context }) => {
    // Create multiple pages for concurrent requests
    const pages = await Promise.all([
      context.newPage(),
      context.newPage(),
      context.newPage(),
      context.newPage(),
      context.newPage()
    ]);

    // Make concurrent requests
    const responses = await Promise.all(
      pages.map(p => p.goto(`${BASE_URL}/health`))
    );

    // Check all responses
    responses.forEach(response => {
      expect(response?.status()).toBe(200);
    });

    // Clean up
    await Promise.all(pages.map(p => p.close()));
  });
});

test.describe('Error Handling E2E Tests', () => {
  
  test('404 errors should be handled gracefully', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/non-existent-endpoint`);
    expect(response?.status()).toBe(404);
    
    const content = await page.content();
    // Should contain error information
    expect(content).toContain('404');
  });

  test('Invalid API requests should return proper error responses', async ({ page }) => {
    // Try to access auth endpoint without proper data
    await page.goto(`${BASE_URL}/api/v1/auth/login`);
    
    // Should handle POST requests properly (might return 405 Method Not Allowed for GET)
    const response = await page.evaluate(async () => {
      const resp = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: 'invalid',
          password: 'invalid'
        })
      });
      return {
        status: resp.status,
        text: await resp.text()
      };
    });
    
    // Should not be 500 Internal Server Error
    expect(response.status).not.toBe(500);
    expect([400, 401, 422]).toContain(response.status);
  });
});

test.describe('Performance E2E Tests', () => {
  
  test('Load testing endpoints should handle traffic', async ({ page }) => {
    // Make 20 sequential requests to test stability
    for (let i = 0; i < 20; i++) {
      const response = await page.goto(`${BASE_URL}/health`);
      expect(response?.status()).toBe(200);
    }
  });

  test('Memory usage should be stable', async ({ page }) => {
    // Get initial metrics
    await page.goto(`${BASE_URL}/api/v1/monitoring/metrics/current`);
    const initialContent = await page.content();
    const initialMetrics = JSON.parse(initialContent);
    
    // Make some requests
    for (let i = 0; i < 10; i++) {
      await page.goto(`${BASE_URL}/health`);
    }
    
    // Get final metrics
    await page.goto(`${BASE_URL}/api/v1/monitoring/metrics/current`);
    const finalContent = await page.content();
    const finalMetrics = JSON.parse(finalContent);
    
    // Memory usage should not have increased dramatically
    const memoryIncrease = finalMetrics.memory_usage - initialMetrics.memory_usage;
    expect(memoryIncrease).toBeLessThan(50); // Less than 50% increase
  });
}); 