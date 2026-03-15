// ===== COMPREHENSIVE IMDB CONSOLE CAPTURE TEST =====
// Paste this into browser console on IMDB.com to test HG Logger

console.log('%c===== HG LOGGER IMDB CAPTURE TEST =====', 'color: #4a9eff; font-size: 16px; font-weight: bold;');

// Test 1: Verify HG Logger is loaded
console.log('%cTest 1: Checking HG Logger availability...', 'color: #ffa500;');
if (window.HGLoggerDebug) {
    console.log('✅ HGLoggerDebug is available');
    console.log('Current capture state:', window.HGLoggerDebug.getIsCapturing());
    console.log('Buffer size:', window.HGLoggerDebug.getBuffer().length);
    console.log('Capture count:', window.HGLoggerDebug.getCaptureCount());
} else {
    console.error('❌ HGLoggerDebug is NOT available - script may not be loaded');
}

// Test 2: Check if hooks are installed
console.log('%cTest 2: Checking console hooks...', 'color: #ffa500;');
const isHooked = console.log.toString().includes('function');
console.log('Console.log is:', isHooked ? '✅ Hooked (function)' : '❌ Not hooked (native)');
console.log('Console.log function:', console.log.toString().substring(0, 100));

// Test 3: Generate test website logs
console.log('%cTest 3: Generating test website logs...', 'color: #ffa500;');
console.log('IMDB TEST: This is a simulated IMDB console.log');
console.warn('IMDB TEST: This is a simulated IMDB warning');
console.error('IMDB TEST: This is a simulated IMDB error');
console.info('IMDB TEST: This is a simulated IMDB info message');

// Test 4: Test with objects and arrays
console.log('%cTest 4: Testing complex data types...', 'color: #ffa500;');
console.log('IMDB TEST: Object data', { 
    movieTitle: 'The Shawshank Redemption', 
    year: 1994, 
    rating: 9.3 
});
console.log('IMDB TEST: Array data', ['Drama', 'Crime', 'Thriller']);

// Test 5: Check buffer after test
setTimeout(() => {
    console.log('%cTest 5: Checking capture results...', 'color: #ffa500;');
    
    if (window.HGLoggerDebug) {
        const buffer = window.HGLoggerDebug.getBuffer();
        console.log('Buffer size after tests:', buffer.length);
        
        // Show last 5 entries
        console.log('Last 5 buffer entries:');
        buffer.slice(-5).forEach((entry, idx) => {
            console.log(`  ${idx + 1}. [${entry.method}] ${entry.host}: ${JSON.stringify(entry.args).substring(0, 60)}...`);
        });
        
        // Count IMDB TEST entries
        const imdbTestCount = buffer.filter(e => 
            e.args && e.args.length > 0 && 
            String(e.args[0]).includes('IMDB TEST')
        ).length;
        
        console.log(`Found ${imdbTestCount} IMDB TEST entries in buffer`);
        
        // Force UI render
        if (window.render) {
            window.render();
            console.log('✅ UI rendered - check HG Logger panel for captured logs');
        }
    }
}, 1000);

// Test 6: Try to trigger IMDB's own console logs
console.log('%cTest 6: Instructions for capturing IMDB logs...', 'color: #ffa500;');
console.log('To capture IMDB\'s real console logs:');
console.log('1. Navigate around the site (click movies, search, etc.)');
console.log('2. Trigger network errors by blocking requests in DevTools');
console.log('3. Check the HG Logger UI for any captured logs');
console.log('4. IMDB may have console logs stripped in production');

// Test 7: Manual console.log injection
console.log('%cTest 7: You can manually test by running:', 'color: #ffa500;');
console.log('console.log("Manual IMDB test message");');
console.log('Then check the HG Logger UI to see if it was captured');

console.log('%c===== END HG LOGGER TEST =====', 'color: #4a9eff; font-size: 16px; font-weight: bold;');
