// Test Script for HG Logger Console Capture
// Paste this into browser console to test

console.log('=== HG LOGGER CONSOLE CAPTURE TEST ===');

// Test 1: Basic console methods
console.log('TEST 1: Basic console.log');
console.warn('TEST 1: Basic console.warn');
console.error('TEST 1: Basic console.error');
console.info('TEST 1: Basic console.info');

// Test 2: Console methods with objects
console.log('TEST 2: Object logging', { test: true, data: [1,2,3] });
console.warn('TEST 2: Warning with object', { warning: 'test warning' });

// Test 3: HG Logger debug functions
if (window.HGLoggerDebug) {
    console.log('TEST 3: HGLoggerDebug available');
    console.log('TEST 3: Buffer size:', window.HGLoggerDebug.getBuffer().length);
    console.log('TEST 3: Capture count:', window.HGLoggerDebug.getCaptureCount());
    console.log('TEST 3: Is capturing:', window.HGLoggerDebug.getIsCapturing());
    
    // Run built-in test
    window.HGLoggerDebug.testWebsiteConsole();
} else {
    console.log('TEST 3: HGLoggerDebug NOT available');
}

// Test 4: Force render if available
if (window.render) {
    console.log('TEST 4: Forcing UI render');
    window.render();
} else {
    console.log('TEST 4: UI render function not available');
}

// Test 5: Check if console methods are hooked
console.log('TEST 5: Console.log function:', console.log.toString().substring(0, 100));
console.log('TEST 5: Console methods hooked:', 
    typeof console.log !== 'function' ? 'NO' : 
    console.log.toString().includes('hookFunction') ? 'YES' : 'UNKNOWN');

console.log('=== END HG LOGGER TEST ===');