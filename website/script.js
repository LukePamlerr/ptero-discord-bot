// ===========================================
// Pterodactyl Discord Bot - Interactive Guide
// ===========================================

// DOM Elements
const navToggle = document.getElementById('navToggle');
const navMenu = document.querySelector('.nav-menu');
const navLinks = document.querySelectorAll('.nav-link');

// Navigation Toggle
navToggle.addEventListener('click', () => {
    navMenu.classList.toggle('active');
    navToggle.classList.toggle('active');
});

// Close mobile menu when clicking on a link
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('active');
        navToggle.classList.remove('active');
    });
});

// Smooth scrolling for navigation links
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// Active navigation link highlighting
window.addEventListener('scroll', () => {
    let current = '';
    const sections = document.querySelectorAll('section');
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (scrollY >= (sectionTop - 200)) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').slice(1) === current) {
            link.classList.add('active');
        }
    });
});

// Deployment Steps Navigation
let currentStep = 1;

function showStep(stepNumber) {
    // Hide all steps
    for (let i = 1; i <= 6; i++) {
        const step = document.getElementById(`step${i}`);
        if (step) {
            step.classList.remove('active');
        }
    }
    
    // Show current step
    const currentStepElement = document.getElementById(`step${stepNumber}`);
    if (currentStepElement) {
        currentStepElement.classList.add('active');
        currentStep = stepNumber;
        
        // Smooth scroll to step
        currentStepElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function nextStep(stepNumber) {
    if (stepNumber <= 6) {
        showStep(stepNumber);
    }
}

function prevStep(stepNumber) {
    if (stepNumber >= 1) {
        showStep(stepNumber);
    }
}

// Initialize first step
document.addEventListener('DOMContentLoaded', () => {
    showStep(1);
});

// Commands Tab System
function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab content
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

// Copy to Clipboard Function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show success feedback
        const button = event.target.closest('.copy-btn');
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i> Copied!';
        button.style.background = 'var(--success-color)';
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.style.background = 'var(--primary-color)';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        // Show success feedback
        const button = event.target.closest('.copy-btn');
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i> Copied!';
        button.style.background = 'var(--success-color)';
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.style.background = 'var(--primary-color)';
        }, 2000);
    });
}

// Progress Indicator
function updateProgress() {
    const sections = document.querySelectorAll('section');
    const scrollPosition = window.scrollY + window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;
    
    let progress = (scrollPosition / documentHeight) * 100;
    progress = Math.min(progress, 100);
    
    // Update progress bar if it exists
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
}

// Scroll event listener for progress
window.addEventListener('scroll', updateProgress);

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', () => {
    const animatedElements = document.querySelectorAll('.feature-card, .step-card, .setup-card, .trouble-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// Search functionality (if needed)
function searchCommands(query) {
    const commandItems = document.querySelectorAll('.command-item');
    commandItems.forEach(item => {
        const syntax = item.querySelector('.command-syntax').textContent.toLowerCase();
        const description = item.querySelector('.command-description').textContent.toLowerCase();
        
        if (syntax.includes(query.toLowerCase()) || description.includes(query.toLowerCase())) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// Theme toggle (for future enhancement)
function toggleTheme() {
    document.body.classList.toggle('light-theme');
    localStorage.setItem('theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
}

// Load saved theme
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K for search (if search is implemented)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('#search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Arrow keys for deployment steps
    if (e.key === 'ArrowRight' && currentStep < 6) {
        nextStep(currentStep + 1);
    } else if (e.key === 'ArrowLeft' && currentStep > 1) {
        prevStep(currentStep - 1);
    }
    
    // Number keys for steps
    if (e.key >= '1' && e.key <= '6') {
        showStep(parseInt(e.key));
    }
});

// Smooth reveal animation for hero elements
document.addEventListener('DOMContentLoaded', () => {
    const heroElements = document.querySelectorAll('.hero-text, .hero-visual');
    heroElements.forEach((el, index) => {
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 200);
    });
});

// Parallax effect for hero section
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const hero = document.querySelector('.hero');
    if (hero && scrolled < window.innerHeight) {
        hero.style.transform = `translateY(${scrolled * 0.5}px)`;
    }
});

// Dynamic year in footer
document.addEventListener('DOMContentLoaded', () => {
    const yearElements = document.querySelectorAll('.current-year');
    const currentYear = new Date().getFullYear();
    yearElements.forEach(el => {
        el.textContent = currentYear;
    });
});

// Form validation (if forms are added)
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const inputs = form.querySelectorAll('input[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('error');
            isValid = false;
        } else {
            input.classList.remove('error');
        }
    });
    
    return isValid;
}

// Loading states
function showLoading(element, text = 'Loading...') {
    const originalContent = element.innerHTML;
    element.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
    element.disabled = true;
    
    return () => {
        element.innerHTML = originalContent;
        element.disabled = false;
    };
}

// Toast notifications
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, duration);
}

// Add toast styles dynamically
const toastStyles = `
    .toast {
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        box-shadow: var(--shadow-lg);
        max-width: 400px;
    }
    
    .toast.show {
        transform: translateX(0);
    }
    
    .toast-success {
        border-color: var(--success-color);
        color: var(--success-color);
    }
    
    .toast-error {
        border-color: var(--error-color);
        color: var(--error-color);
    }
    
    .toast-info {
        border-color: var(--primary-color);
        color: var(--primary-color);
    }
`;

// Add toast styles to head
const styleSheet = document.createElement('style');
styleSheet.textContent = toastStyles;
document.head.appendChild(styleSheet);

// Initialize tooltips (if needed)
document.addEventListener('DOMContentLoaded', () => {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = e.target.getAttribute('data-tooltip');
            document.body.appendChild(tooltip);
            
            const rect = e.target.getBoundingClientRect();
            tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
        });
        
        element.addEventListener('mouseleave', () => {
            const tooltip = document.querySelector('.tooltip');
            if (tooltip) {
                document.body.removeChild(tooltip);
            }
        });
    });
});

// Performance monitoring
const performanceMetrics = {
    startTime: performance.now(),
    
    logLoadTime() {
        const loadTime = performance.now() - this.startTime;
        console.log(`Page loaded in ${loadTime.toFixed(2)}ms`);
    },
    
    logInteractions() {
        // Log user interactions for analytics (if needed)
        document.addEventListener('click', (e) => {
            const target = e.target.closest('[data-track]');
            if (target) {
                const action = target.getAttribute('data-track');
                console.log(`User interaction: ${action}`);
            }
        });
    }
};

// Initialize performance monitoring
document.addEventListener('DOMContentLoaded', () => {
    performanceMetrics.logLoadTime();
    performanceMetrics.logInteractions();
});

// Accessibility improvements
document.addEventListener('DOMContentLoaded', () => {
    // Add ARIA labels to interactive elements
    const interactiveElements = document.querySelectorAll('button, a, input, textarea, select');
    interactiveElements.forEach(element => {
        if (!element.getAttribute('aria-label') && !element.textContent.trim()) {
            const icon = element.querySelector('i');
            if (icon) {
                const iconClass = icon.className;
                let label = 'Button';
                
                if (iconClass.includes('discord')) label = 'Discord';
                if (iconClass.includes('github')) label = 'GitHub';
                if (iconClass.includes('twitter')) label = 'Twitter';
                if (iconClass.includes('server')) label = 'Server';
                if (iconClass.includes('user')) label = 'User';
                if (iconClass.includes('chart')) label = 'Analytics';
                if (iconClass.includes('backup')) label = 'Backup';
                
                element.setAttribute('aria-label', label);
            }
        }
    });
    
    // Skip to main content link
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link';
    skipLink.textContent = 'Skip to main content';
    document.body.insertBefore(skipLink, document.body.firstChild);
});

// Add skip link styles
const skipLinkStyles = `
    .skip-link {
        position: absolute;
        top: -40px;
        left: 6px;
        background: var(--primary-color);
        color: var(--text-primary);
        padding: 8px;
        text-decoration: none;
        border-radius: 4px;
        z-index: 10000;
        transition: top 0.3s ease;
    }
    
    .skip-link:focus {
        top: 6px;
    }
`;

const skipStyleSheet = document.createElement('style');
skipStyleSheet.textContent = skipLinkStyles;
document.head.appendChild(skipStyleSheet);

// Export functions for external use
window.PteroBotGuide = {
    scrollToSection,
    showStep,
    nextStep,
    prevStep,
    showTab,
    copyToClipboard,
    searchCommands,
    toggleTheme,
    validateForm,
    showLoading,
    showToast
};
