// Test script for API caching functionality
// Run with: node test_caching.js

// Mock localStorage for testing
global.localStorage = {
  storage: {},
  getItem(key) {
    return this.storage[key] || null;
  },
  setItem(key, value) {
    this.storage[key] = value;
  },
  removeItem(key) {
    delete this.storage[key];
  },
  clear() {
    this.storage = {};
  },
  get length() {
    return Object.keys(this.storage).length;
  },
  key(index) {
    const keys = Object.keys(this.storage);
    return keys[index] || null;
  }
};

// Mock fetch for testing
global.fetch = async (url, options = {}) => {
  console.log(`Mock fetch called for: ${url}`);

  // Simulate different responses based on URL
  if (url.includes('/student/assignments')) {
    return {
      ok: true,
      status: 200,
      headers: {
        get: (header) => header === 'content-type' ? 'application/json' : null
      },
      json: async () => ({
        assignments: [
          { id: 1, title: 'Test Assignment 1', status: 'pending' },
          { id: 2, title: 'Test Assignment 2', status: 'completed' }
        ]
      })
    };
  }

  if (url.includes('/student/mastery')) {
    return {
      ok: true,
      status: 200,
      headers: {
        get: (header) => header === 'content-type' ? 'application/json' : null
      },
      json: async () => ([
        { concept_name: 'Math', mastery_score: 85 },
        { concept_name: 'Science', mastery_score: 92 }
      ])
    };
  }

  return {
    ok: false,
    status: 404,
    statusText: 'Not Found'
  };
};

// Import the API service (this would need to be adjusted for actual testing)
const { studentAPI } = require('./frontend2/src/services/api.js');

async function testCaching() {
  console.log('Testing API caching functionality...\n');

  try {
    // Test 1: First call should make actual request and cache
    console.log('Test 1: First call to getAssignments');
    const start1 = Date.now();
    const result1 = await studentAPI.getAssignments(1);
    const end1 = Date.now();
    console.log(`Result 1: ${JSON.stringify(result1)}`);
    console.log(`Time taken: ${end1 - start1}ms`);
    console.log(`Cache keys: ${Object.keys(localStorage.storage).filter(k => k.startsWith('api_cache_'))}\n`);

    // Test 2: Second call should use cache
    console.log('Test 2: Second call to getAssignments (should use cache)');
    const start2 = Date.now();
    const result2 = await studentAPI.getAssignments(1);
    const end2 = Date.now();
    console.log(`Result 2: ${JSON.stringify(result2)}`);
    console.log(`Time taken: ${end2 - start2}ms`);
    console.log(`Results match: ${JSON.stringify(result1) === JSON.stringify(result2)}\n`);

    // Test 3: Test cache expiration (simulate by manually setting old timestamp)
    console.log('Test 3: Testing cache expiration');
    const cacheKey = 'api_cache_assignments_1';
    if (localStorage.storage[cacheKey]) {
      const cached = JSON.parse(localStorage.storage[cacheKey]);
      cached.timestamp = Date.now() - 600000; // 10 minutes ago (past 5-minute expiration)
      localStorage.storage[cacheKey] = JSON.stringify(cached);
    }

    const start3 = Date.now();
    const result3 = await studentAPI.getAssignments(1);
    const end3 = Date.now();
    console.log(`Result 3: ${JSON.stringify(result3)}`);
    console.log(`Time taken: ${end3 - start3}ms (should be slower due to fresh request)\n`);

    // Test 4: Test different endpoint caching
    console.log('Test 4: Testing mastery endpoint caching');
    const start4 = Date.now();
    const result4 = await studentAPI.getMastery();
    const end4 = Date.now();
    console.log(`Result 4: ${JSON.stringify(result4)}`);
    console.log(`Time taken: ${end4 - start4}ms`);
    console.log(`Cache keys: ${Object.keys(localStorage.storage).filter(k => k.startsWith('api_cache_'))}\n`);

    console.log('All caching tests completed successfully!');

  } catch (error) {
    console.error('Test failed:', error);
  }
}

// Run the test
testCaching();
