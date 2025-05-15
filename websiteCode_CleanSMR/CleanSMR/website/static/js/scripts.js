/**
 * Wait for the DOM to be fully loaded before executing scripts.
 */
document.addEventListener('DOMContentLoaded', function() {
    /**
     * Initialize Animate On Scroll (AOS) library for scroll animations.
     * @param {number} duration - Duration of the animation in milliseconds.
     * @param {boolean} once - Whether animation should happen only once.
     * @param {number} offset - Offset (in pixels) from the original trigger point.
     */
    AOS.init({
        duration: 1000,
        once: true,
        offset: 100
    });

    /**
     * Initialize Particles.js for background particle effects.
     */
    initParticles();
    
    // Initialize all custom components and handlers
    init2FAModal();
    initLoader();
    initScrollProgress();
    initSmoothScroll();
    initCounters();
    initFeatureHover();
    initNavbar();
    initAPIDemo();
});

/**
 * Initialize the loader component to handle page loading animations.
 * Ensures the loader is displayed for a minimum time even if the page loads quickly.
 */function initLoader() {
    // Minimum time to show the loader (4 seconds)
    const minimumLoaderTime = 4000; // 4 seconds in milliseconds
    const startTime = performance.now(); // High-precision timing

    window.addEventListener('load', function() {
        const loader = document.querySelector('.loader-wrapper');
        if (loader) {
            // Set the loader to fade out
            loader.style.opacity = '0';
            // Calculate elapsed time since the page load started
            const elapsedTime = performance.now() - startTime;
            const remainingTime = Math.max(minimumLoaderTime - elapsedTime, 0);

            // Hide the loader after the remaining time has elapsed or immediately if it's already been shown long enough
            setTimeout(() => {
                loader.style.display = 'none';
            }, remainingTime);
        }
    });
}


/**
 * Initialize the scroll progress bar to indicate how much of the page has been scrolled.
 * Updates the width of the progress bar based on the scroll position.
 */
function initScrollProgress() {
    window.addEventListener('scroll', function() {
        const progressBar = document.querySelector('.scroll-progress');
        if (progressBar) {
            const windowHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrolled = (window.scrollY / windowHeight) * 100;
            progressBar.style.width = `${scrolled}%`;
        }
    });
}

/**
 * Initialize smooth scrolling for anchor links and specific buttons.
 * Adds smooth scroll behavior to anchor links and specific buttons.
 */
function initSmoothScroll() {
    // Add smooth scroll to all anchor links starting with '#'
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add smooth scroll to the 'Learn More' button
    const learnMoreBtn = document.getElementById('learn-more-btn');
    if (learnMoreBtn) {
        learnMoreBtn.addEventListener('click', () => {
            const featuresSection = document.querySelector('.features-section');
            if (featuresSection) {
                featuresSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
}

/**
 * Initialize counter animations for elements with the class 'counter'.
 * Uses Intersection Observer to animate counters when they come into view.
 */
function initCounters() {
    const counters = document.querySelectorAll('.counter');

    /**
     * Animate the counter from 0 to the target value.
     * @param {HTMLElement} counter - The counter element.
     * @param {number} target - The target value to count up to.
     */
    const animateCounter = (counter, target) => {
        const increment = target / 50; // Increment value for each frame
        let current = 0;

        const updateCounter = () => {
            if (current < target) {
                current += increment;
                counter.textContent = current.toFixed(1);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };

        updateCounter();
    };

    // Use Intersection Observer to animate counters when they come into view
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseFloat(counter.textContent);
                animateCounter(counter, target);
                observer.unobserve(counter);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(counter => observer.observe(counter));
}

/**
 * Initialize hover effects for feature cards.
 * Adds a hover effect to feature cards to elevate and add a shadow.
 */
function initFeatureHover() {
    const features = document.querySelectorAll('.feature-card');

    features.forEach(feature => {
        feature.addEventListener('mouseenter', () => {
            feature.style.transform = 'translateY(-10px)';
            feature.style.boxShadow = '0 10px 20px rgba(0, 255, 255, 0.2)';
        });

        feature.addEventListener('mouseleave', () => {
            feature.style.transform = 'translateY(0)';
            feature.style.boxShadow = 'none';
        });
    });
}

/*
 * Initialize the navbar behavior, including toggling and scroll effects.
 * Handles the navbar toggle button and scroll behavior.
 */
function initNavbar() {
    const navbarToggle = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');

    if (navbarToggle && navbarCollapse) {
        navbarToggle.addEventListener('click', () => {
            navbarCollapse.classList.toggle('show');
        });

        // Close navbar when clicking outside
        document.addEventListener('click', (e) => {
            if (!navbarToggle.contains(e.target) && !navbarCollapse.contains(e.target)) {
                navbarCollapse.classList.remove('show');
            }
        });
    }

    // Navbar scroll behavior
    let lastScroll = 0;
    window.addEventListener('scroll', () => {
        const navbar = document.querySelector('.glass-nav');
        const currentScroll = window.scrollY;

        if (currentScroll > lastScroll && currentScroll > 80) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        lastScroll = currentScroll;
    });
}

/**
 * Initialize Particles.js with the specified configuration file.
 * Loads the particle effect configuration and initializes Particles.js.
 */
function initParticles() {
    particlesJS.load('particles-js', '/static/js/particles-config.json', function() {
        console.log('Particles.js loaded successfully');
    });
}

/**
 * Initialize the API demo button to fetch and display data from the API.
 * Adds a click event listener to the API demo button to fetch data from the API.
 */
function initAPIDemo() {
    const apiDemoBtn = document.getElementById('api-demo-btn');
    if (apiDemoBtn) {
        apiDemoBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/demo-endpoint/');
                const data = await response.json();
                console.log('API Response:', data);
                alert(`Sample Data: ${JSON.stringify(data)}`);
            } catch (error) {
                console.error('Error fetching API data:', error);
                alert('Unable to fetch data. Please try again later.');
            }
        });
    }
}

/**
 * Initialize the 'Get Started' button to redirect to the registration page.
 */
const getStartedBtn = document.getElementById('get-started-btn');
if (getStartedBtn) {
    getStartedBtn.addEventListener('click', () => {
        window.location.href = '/register/';
    });
}


/**
 * Global error handler to log JavaScript errors.
 */
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.message);
    
}); 


function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function init2FAModal() {
    const authCodeInput = document.getElementById('auth_code');
    if (authCodeInput) {
        // Only allow numbers
        authCodeInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 6) {
                this.value = this.value.slice(0, 6);
            }
        });

        // Clear input when modal is hidden
        const twoFactorModal = document.getElementById('twoFactorModal');
        twoFactorModal.addEventListener('hidden.bs.modal', function () {
            authCodeInput.value = '';
        });
    }
}