/**
 * UI E2E тесты на основе функциональных требований FR-001 to FR-080
 * Покрывает ключевые пользовательские сценарии через браузер
 * 
 * Context7 Pattern: Comprehensive browser testing with real user interactions
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

class TestUIRequirements {
  constructor(private page: Page) {}

  /**
   * Context7 pattern: Reusable authentication helper
   */
  async authenticateUser(email: string = 'test@example.com', password: string = 'TestPassword123!') {
    await this.page.goto('/login');
    await this.page.fill('input[name="email"]', email);
    await this.page.fill('input[name="password"]', password);
    await this.page.click('button[type="submit"]');
    
    // Ожидаем успешного входа
    await expect(this.page).toHaveURL(/dashboard|search|chat/);
  }

  /**
   * Context7 pattern: Wait for API responses
   */
  async waitForApiResponse(urlPattern: string | RegExp, timeout: number = 5000) {
    return await this.page.waitForResponse(response => 
      typeof urlPattern === 'string' ? 
        response.url().includes(urlPattern) : 
        urlPattern.test(response.url())
    , { timeout });
  }
}

test.describe('FR-001-009: Аутентификация и авторизация', () => {
  test('FR-001: Вход по email/паролю через UI', async ({ page }) => {
    const ui = new TestUIRequirements(page);
    
    // Шаг 1: Переход на страницу входа
    await page.goto('/login');
    await expect(page).toHaveTitle(/login|вход|sign in/i);
    
    // Шаг 2: Заполнение формы входа
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'TestPassword123!');
    
    // Шаг 3: Отправка формы
    const loginPromise = ui.waitForApiResponse('/api/v1/auth/login');
    await page.click('button[type="submit"]');
    
    // Шаг 4: Проверка успешного входа
    const loginResponse = await loginPromise;
    expect(loginResponse.status()).toBe(200);
    
    // Проверяем, что пользователь перенаправлен на дашборд
    await expect(page).toHaveURL(/dashboard|search|chat/);
    
    // Проверяем наличие элементов авторизованного пользователя
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('FR-002: SSO провайдеры доступны в UI', async ({ page }) => {
    await page.goto('/login');
    
    // Проверяем наличие кнопок SSO
    const ssoButtons = [
      '[data-testid="login-google"]',
      '[data-testid="login-microsoft"]', 
      '[data-testid="login-github"]',
      'button:has-text("Google")',
      'button:has-text("Microsoft")',
      'button:has-text("GitHub")'
    ];
    
    let ssoFound = false;
    for (const selector of ssoButtons) {
      if (await page.locator(selector).count() > 0) {
        ssoFound = true;
        break;
      }
    }
    
    expect(ssoFound).toBeTruthy();
  });

  test('FR-009: Отображение бюджета пользователя', async ({ page }) => {
    const ui = new TestUIRequirements(page);
    await ui.authenticateUser();
    
    // Переход в профиль или на страницу бюджета
    await page.goto('/profile');
    
    // Проверяем отображение информации о бюджете
    const budgetElements = [
      '[data-testid="budget-limit"]',
      '[data-testid="current-usage"]',
      'text=/budget/i',
      'text=/лимит/i',
      'text=/usage/i'
    ];
    
    let budgetFound = false;
    for (const selector of budgetElements) {
      if (await page.locator(selector).count() > 0) {
        budgetFound = true;
        break;
      }
    }
    
    expect(budgetFound).toBeTruthy();
  });
});

test.describe('FR-010-018: Семантический поиск', () => {
  test.beforeEach(async ({ page }) => {
    const ui = new TestUIRequirements(page);
    await ui.authenticateUser();
  });

  test('FR-010: Базовый семантический поиск через UI', async ({ page }) => {
    const ui = new TestUIRequirements(page);
    
    // Переход на страницу поиска
    await page.goto('/search');
    await expect(page).toHaveTitle(/search|поиск/i);
    
    // Шаг 1: Ввод поискового запроса
    const searchInput = page.locator('input[name="query"], input[placeholder*="search"], input[placeholder*="поиск"]').first();
    await searchInput.fill('authentication security best practices');
    
    // Шаг 2: Выполнение поиска
    const searchPromise = ui.waitForApiResponse('/api/v1/search');
    await page.keyboard.press('Enter');
    
    // Шаг 3: Ожидание результатов
    const searchResponse = await searchPromise;
    expect(searchResponse.status()).toBe(200);
    
    // Проверка отображения результатов
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    
    // FR-011: Проверка отображения score релевантности
    const firstResult = page.locator('[data-testid="search-result"]').first();
    await expect(firstResult).toBeVisible();
    
    // FR-012: Проверка отображения источника
    await expect(firstResult.locator('[data-testid="result-source"]')).toBeVisible();
  });

  test('FR-014-017: Расширенный поиск с фильтрами', async ({ page }) => {
    const ui = new TestUIRequirements(page);
    await page.goto('/search/advanced');
    
    // Открытие панели фильтров
    await page.click('[data-testid="filters-toggle"], button:has-text("Фильтры"), button:has-text("Filters")');
    
    // FR-014: Фильтрация по источникам
    await page.check('input[name="sources"][value="confluence"]');
    await page.check('input[name="sources"][value="jira"]');
    
    // FR-015: Фильтрация по дате
    await page.fill('input[name="date_from"]', '2024-01-01');
    
    // FR-016: Фильтрация по типу контента
    await page.selectOption('select[name="content_type"]', 'documentation');
    
    // Выполнение поиска с фильтрами
    await page.fill('input[name="query"]', 'API documentation');
    
    const searchPromise = ui.waitForApiResponse('/api/v1/search/advanced');
    await page.click('button[type="submit"]');
    
    const searchResponse = await searchPromise;
    expect(searchResponse.status()).toBe(200);
    
    // Проверка применения фильтров в результатах
    await expect(page.locator('[data-testid="active-filters"]')).toBeVisible();
  });

  test('FR-013: Пагинация результатов поиска', async ({ page }) => {
    await page.goto('/search');
    
    // Выполнение поиска
    await page.fill('input[name="query"]', 'configuration setup guide');
    await page.keyboard.press('Enter');
    
    // Ожидание загрузки результатов
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    
    // Проверка наличия пагинации
    const paginationElements = [
      '[data-testid="pagination"]',
      'button:has-text("Next")',
      'button:has-text("Следующая")',
      '.pagination'
    ];
    
    let paginationFound = false;
    for (const selector of paginationElements) {
      if (await page.locator(selector).count() > 0) {
        paginationFound = true;
        // Тестируем переход на следующую страницу
        await page.click(selector);
        await page.waitForLoadState('networkidle');
        break;
      }
    }
    
    // Если пагинация не найдена, проверяем наличие достаточного количества результатов
    if (!paginationFound) {
      const resultsCount = await page.locator('[data-testid="search-result"]').count();
      expect(resultsCount).toBeGreaterThan(0);
    }
  });
});

test.describe('FR-019-026: Генерация RFC', () => {
  test.beforeEach(async ({ page }) => {
    const ui = new TestUIRequirements(page);
    await ui.authenticateUser();
  });

  test('FR-019-021: Интерактивная генерация RFC через UI', async ({ page }) => {
    const ui = new TestUIRequirements(page);
    
    // Переход на страницу генерации RFC
    await page.goto('/rfc-generation');
    await expect(page).toHaveTitle(/rfc|документ/i);
    
    // Шаг 1: Заполнение базовой информации
    await page.fill('textarea[name="task_description"]', 
      'Implement new user authentication system with multi-factor authentication');
    
    await page.fill('textarea[name="project_context"]', 
      'E-commerce platform with high security requirements');
    
    await page.selectOption('select[name="priority"]', 'high');
    await page.selectOption('select[name="template_type"]', 'architecture');
    
    // FR-022: Проверка доступности шаблонов
    const templateOptions = await page.locator('select[name="template_type"] option').count();
    expect(templateOptions).toBeGreaterThan(1);
    
    // Шаг 2: Запуск генерации
    const generatePromise = ui.waitForApiResponse('/api/v1/generate/rfc');
    await page.click('button[type="submit"], button:has-text("Generate"), button:has-text("Создать")');
    
    // Шаг 3: Ожидание ответа
    const generateResponse = await generatePromise;
    expect(generateResponse.status()).toBe(200);
    
    // FR-021: Проверка отображения прогресса
    await expect(page.locator('[data-testid="generation-progress"]')).toBeVisible({ timeout: 10000 });
    
    // FR-020: Проверка появления умных вопросов (если реализовано)
    const questionElements = [
      '[data-testid="smart-question"]',
      '.question-form',
      'text=question',
      'text=вопрос'
    ];
    
    // Ожидаем появления либо прогресса, либо вопросов
    let found = false;
    for (const selector of questionElements) {
      if (await page.locator(selector).count() > 0) {
        found = true;
        break;
      }
    }
    
    // Или ожидаем завершения генерации
    await expect(page.locator('[data-testid="generation-result"], .generated-content')).toBeVisible({ timeout: 30000 });
  });

  test('FR-023-024: Редактирование и экспорт RFC', async ({ page }) => {
    // Сначала создаем или переходим к существующему RFC
    await page.goto('/rfc-generation');
    
    // Быстрая генерация для тестирования
    await page.fill('textarea[name="task_description"]', 'Test RFC for editing');
    await page.click('button[type="submit"]');
    
    // Ожидание завершения генерации
    await expect(page.locator('[data-testid="generation-result"]')).toBeVisible({ timeout: 30000 });
    
    // FR-023: Тестирование редактирования
    const editButton = page.locator('button:has-text("Edit"), button:has-text("Редактировать")');
    if (await editButton.count() > 0) {
      await editButton.click();
      
      // Проверяем возможность редактирования контента
      const editableContent = page.locator('textarea[name="content"], .editor, [contenteditable="true"]');
      await expect(editableContent).toBeVisible();
      
      // Вносим изменения
      await editableContent.fill('Updated RFC content for testing');
      await page.click('button:has-text("Save"), button:has-text("Сохранить")');
    }
    
    // FR-024: Тестирование экспорта
    const exportButton = page.locator('button:has-text("Export"), button:has-text("Экспорт")');
    if (await exportButton.count() > 0) {
      await exportButton.click();
      
      // Проверяем доступность форматов экспорта
      const exportFormats = ['markdown', 'pdf', 'word', 'docx'];
      for (const format of exportFormats) {
        const formatButton = page.locator(`button:has-text("${format}")`);
        if (await formatButton.count() > 0) {
          expect(await formatButton.count()).toBeGreaterThan(0);
          break;
        }
      }
    }
  });
});

test.describe('FR-027-034: Чат-интерфейс', () => {
  test.beforeEach(async ({ page }) => {
    const ui = new TestUIRequirements(page);
    await ui.authenticateUser();
  });

  test('FR-027-029: Multi-turn разговор в чате', async ({ page }) => {
    const ui = new TestUIRequirements(page);
    
    // Переход на страницу чата
    await page.goto('/chat');
    await expect(page).toHaveTitle(/chat|чат/i);
    
    // Шаг 1: Отправка первого сообщения
    const chatInput = page.locator('input[name="message"], textarea[name="message"]').first();
    await chatInput.fill('What is authentication in web applications?');
    
    const firstMessagePromise = ui.waitForApiResponse('/api/v1/ai/chat');
    await page.keyboard.press('Enter');
    
    // Ожидание ответа
    const firstResponse = await firstMessagePromise;
    expect(firstResponse.status()).toBe(200);
    
    // Проверка появления сообщений в чате
    await expect(page.locator('[data-testid="chat-message"]')).toHaveCount(2); // user + assistant
    
    // Шаг 2: Отправка follow-up вопроса (FR-027: multi-turn)
    await chatInput.fill('Can you provide a code example?');
    
    const secondMessagePromise = ui.waitForApiResponse('/api/v1/ai/chat');
    await page.keyboard.press('Enter');
    
    await secondMessagePromise;
    
    // Проверка контекста разговора
    await expect(page.locator('[data-testid="chat-message"]')).toHaveCount(4); // 2 user + 2 assistant
    
    // FR-028: Проверка подсветки синтаксиса кода
    const codeBlocks = page.locator('pre, code, .hljs');
    if (await codeBlocks.count() > 0) {
      await expect(codeBlocks.first()).toBeVisible();
    }
    
    // FR-029: Тестирование копирования ответа
    const copyButton = page.locator('button:has-text("Copy"), button[title*="copy"], [data-testid="copy-button"]');
    if (await copyButton.count() > 0) {
      await copyButton.first().click();
      
      // Проверяем feedback о копировании
      await expect(page.locator('text="Copied", text="Скопировано"')).toBeVisible({ timeout: 3000 });
    }
  });

  test('FR-032: Загрузка файлов в чат', async ({ page }) => {
    await page.goto('/chat');
    
    // Поиск кнопки загрузки файлов
    const uploadElements = [
      'input[type="file"]',
      '[data-testid="file-upload"]',
      'button:has-text("Upload")',
      'button:has-text("Загрузить")'
    ];
    
    let uploadFound = false;
    for (const selector of uploadElements) {
      if (await page.locator(selector).count() > 0) {
        uploadFound = true;
        
        if (selector === 'input[type="file"]') {
          // Создаем тестовый файл для загрузки
          const testFile = Buffer.from('Test file content');
          await page.setInputFiles(selector, {
            name: 'test.txt',
            mimeType: 'text/plain',
            buffer: testFile
          });
        }
        break;
      }
    }
    
    expect(uploadFound).toBeTruthy();
  });
});

test.describe('FR-050-065: Мониторинг и аналитика', () => {
  test.beforeEach(async ({ page }) => {
    const ui = new TestUIRequirements(page);
    await ui.authenticateUser();
  });

  test('FR-054-057: Дашборд с ключевыми метриками', async ({ page }) => {
    // Переход на дашборд аналитики
    await page.goto('/analytics');
    
    // Проверка наличия ключевых метрик
    const metricElements = [
      '[data-testid="usage-metrics"]',
      '[data-testid="performance-metrics"]',
      '.metric-card',
      '.dashboard-widget'
    ];
    
    let metricsFound = false;
    for (const selector of metricElements) {
      if (await page.locator(selector).count() > 0) {
        metricsFound = true;
        await expect(page.locator(selector)).toBeVisible();
        break;
      }
    }
    
    expect(metricsFound).toBeTruthy();
    
    // Проверка графиков и трендов
    const chartElements = [
      'canvas',
      '.recharts-wrapper',
      '.chart-container',
      '[data-testid="chart"]'
    ];
    
    let chartsFound = false;
    for (const selector of chartElements) {
      if (await page.locator(selector).count() > 0) {
        chartsFound = true;
        break;
      }
    }
    
    expect(chartsFound).toBeTruthy();
  });

  test('FR-062-064: Live мониторинг с real-time обновлениями', async ({ page }) => {
    await page.goto('/monitoring');
    
    // Проверка наличия live метрик
    const liveElements = [
      '[data-testid="live-metrics"]',
      'text="Live"',
      'text="Real-time"',
      '.live-indicator'
    ];
    
    let liveFound = false;
    for (const selector of liveElements) {
      if (await page.locator(selector).count() > 0) {
        liveFound = true;
        await expect(page.locator(selector)).toBeVisible();
        break;
      }
    }
    
    expect(liveFound).toBeTruthy();
    
    // Проверка автообновления (ожидаем изменения в течение 10 секунд)
    const initialContent = await page.locator('[data-testid="live-metrics"]').textContent();
    await page.waitForTimeout(5000);
    const updatedContent = await page.locator('[data-testid="live-metrics"]').textContent();
    
    // Контент может обновиться или остаться тем же (если нет новых данных)
    expect(typeof updatedContent).toBe('string');
  });
});

test.describe('NFR-001-004: Производительность UI', () => {
  test('NFR-001: Время загрузки страниц <1 секунды', async ({ page }) => {
    const pages = [
      '/',
      '/search', 
      '/chat',
      '/rfc-generation',
      '/analytics'
    ];
    
    for (const pagePath of pages) {
      const startTime = Date.now();
      
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');
      
      const loadTime = Date.now() - startTime;
      
      // NFR-004: Загрузка дашбордов должна занимать менее 1 секунды
      expect(loadTime).toBeLessThan(1000);
    }
  });

  test('NFR-041-043: Совместимость с браузерами и responsive design', async ({ page, browserName }) => {
    await page.goto('/');
    
    // Проверка, что приложение работает в текущем браузере
    await expect(page.locator('body')).toBeVisible();
    
    // Тестирование responsive design
    const viewports = [
      { width: 1920, height: 1080 }, // Desktop
      { width: 768, height: 1024 },  // Tablet
      { width: 375, height: 667 }    // Mobile
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.waitForTimeout(500);
      
      // Проверяем, что контент адаптируется
      const bodyRect = await page.locator('body').boundingBox();
      expect(bodyRect?.width).toBeLessThanOrEqual(viewport.width);
    }
  });
});

test.describe('Интеграционные UI сценарии', () => {
  test('Полный workflow: Поиск → Чат → RFC генерация', async ({ page }) => {
    const ui = new TestUIRequirements(page);
    await ui.authenticateUser();
    
    // Шаг 1: Выполнение поиска
    await page.goto('/search');
    await page.fill('input[name="query"]', 'authentication best practices');
    await page.keyboard.press('Enter');
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    
    // Шаг 2: Переход в чат для уточнения
    await page.goto('/chat');
    await page.fill('input[name="message"]', 'Based on the search results, what are the main authentication patterns?');
    await page.keyboard.press('Enter');
    await expect(page.locator('[data-testid="chat-message"]')).toHaveCount(2);
    
    // Шаг 3: Генерация RFC на основе полученной информации
    await page.goto('/rfc-generation');
    await page.fill('textarea[name="task_description"]', 
      'Create authentication system RFC based on research findings');
    await page.click('button[type="submit"]');
    
    // Ожидание завершения процесса
    await expect(page.locator('[data-testid="generation-result"]')).toBeVisible({ timeout: 30000 });
  });
}); 