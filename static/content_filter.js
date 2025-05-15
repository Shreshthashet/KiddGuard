// KidGuard Content Monitoring and Filtering
function initContentMonitoring() {
    // Only initialize on child dashboard
    if (!document.body.classList.contains('child-dashboard') && 
        window.location.pathname !== '/child/dashboard') {
        return;
    }
    
    console.log('Content monitoring initialized');
    
    // Listen for page loads to report URLs
    window.addEventListener('load', reportCurrentPage);
    
    //Set up periodic monitoring(every 30 seconds)
    setInterval(reportCurrentPage,30000);
    
}

function reportCurrentPage() {
    // In a real application, this would be handled by a browser extension
    // For this demo, we'll simulate the reporting
    
    // Get current page details
    const currentUrl = window.location.href;
    const pageTitle = document.title;
    const pageContent = document.body.innerText.substring(0, 1000); // First 1000 chars
    
    // Send report to server
    reportToServer(currentUrl, pageTitle, pageContent);
}

function reportToServer(url, title, content) {
    console.log('Reporting page to server:', url);
    
    // Use fetch API to report the page
    fetch('/report_website', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            url: url,
            title: title,
            content: content
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Report response:', data);
    })
    .catch(error => {
        console.error('Error reporting page:', error);
    });
}

function simulateExtensionActivity() {
    // This simulates what a browser extension would do in a real implementation
    console.log('Simulating browser extension activity');
    
    // Create a small floating indicator to show monitoring is active
    const indicator = document.createElement('div');
    indicator.style.position = 'fixed';
    indicator.style.bottom = '20px';
    indicator.style.right = '20px';
    indicator.style.padding = '8px 12px';
    indicator.style.background = 'rgba(0, 123, 255, 0.1)';
    indicator.style.color = '#0d6efd';
    indicator.style.borderRadius = '4px';
    indicator.style.fontSize = '12px';
    indicator.style.zIndex = '9999';
    indicator.style.display = 'flex';
    indicator.style.alignItems = 'center';
    indicator.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
    
    indicator.innerHTML = `
        <i class="fas fa-shield-alt" style="margin-right: 8px;"></i>
        KidGuard Monitoring Active
    `;
    
    document.body.appendChild(indicator);
    
    // Simulate periodic activity reporting
    setInterval(() => {
        // Flash the indicator to show activity
        indicator.style.background = 'rgba(0, 123, 255, 0.3)';
        setTimeout(() => {
            indicator.style.background = 'rgba(0, 123, 255, 0.1)';
        }, 300);
        
        // In a real extension, this would capture the actual current page
        const simulatedUrls = [
            'https://www.example.com/homework/math',
            'https://www.educationsite.org/science',
            'https://www.games.com/puzzle',
            'https://www.homework-helper.com/history',
            'https://www.socialnetwork.com/feed',
            // Add a couple of inappropriate URLs to occasionally trigger alerts
            'https://www.adult-content.com',
            'https://www.gambling-games.com'
        ];
        
        const simulatedTitles = [
            'Math Homework Help | Example.com',
            'Science Lessons for Kids | EducationSite',
            'Puzzle Games - Brain Training',
            'History Resources and Study Guides',
            'Social Network - Your Feed',
            // Corresponding titles for inappropriate sites
            'Adult Content - 18+ Only',
            'Online Gambling Games'
        ];
        
        const simulatedContents = [
            'Educational content about mathematics and problem solving',
            'Science educational material for school students',
            'Fun puzzle games to train your brain and improve cognitive skills',
            'Historical resources and study guides for homework',
            'Social media feed with friends and family updates',
            // Content that will trigger the filter
            'Adult content with explicit material and pornographic images',
            'Online gambling, betting, and casino games with real money'
        ];
        
        // Pick a random simulated site for the demo
        const randomIndex = Math.floor(Math.random() * simulatedUrls.length);
        
        // Report the simulated site
        reportToServer(
            simulatedUrls[randomIndex],
            simulatedTitles[randomIndex],
            simulatedContents[randomIndex]
        );
    }, 20000); // Every 20 seconds for the demo
}
