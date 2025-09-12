// AI AdWords Homepage - Nike-Style Interactions

class Homepage {
    constructor() {
        this.modal = document.getElementById('authModal');
        this.currentForm = 'login';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
        this.animateHeroElements();
    }

    setupEventListeners() {
        // Modal triggers
        document.getElementById('loginBtn').addEventListener('click', () => {
            this.showModal('login');
        });

        document.getElementById('signupBtn').addEventListener('click', () => {
            this.showModal('signup');
        });

        document.getElementById('heroSignupBtn').addEventListener('click', () => {
            this.showModal('signup');
        });

        document.getElementById('heroDemoBtn').addEventListener('click', () => {
            this.goToDemo();
        });

        // Modal close
        document.getElementById('modalClose').addEventListener('click', () => {
            this.hideModal();
        });

        document.getElementById('modalOverlay').addEventListener('click', () => {
            this.hideModal();
        });

        // Form switching
        document.getElementById('showSignup').addEventListener('click', (e) => {
            e.preventDefault();
            this.switchForm('signup');
        });

        document.getElementById('showLogin').addEventListener('click', (e) => {
            e.preventDefault();
            this.switchForm('login');
        });

        document.getElementById('backToLogin').addEventListener('click', (e) => {
            e.preventDefault();
            this.switchForm('login');
        });

        // Magic link buttons
        document.getElementById('magicLinkBtn').addEventListener('click', () => {
            this.switchForm('magicLink');
        });

        document.getElementById('signupMagicLinkBtn').addEventListener('click', () => {
            this.switchForm('magicLink');
        });

        // SSO buttons - Login form
        document.getElementById('googleSSOBtn').addEventListener('click', () => {
            this.handleOAuthLogin('google');
        });

        document.getElementById('redditSSOBtn').addEventListener('click', () => {
            this.handleOAuthLogin('reddit');
        });

        document.getElementById('xSSOBtn').addEventListener('click', () => {
            this.handleOAuthLogin('twitter');
        });

        // SSO buttons - Signup form
        document.getElementById('signupGoogleSSOBtn').addEventListener('click', () => {
            this.handleOAuthLogin('google');
        });

        document.getElementById('signupRedditSSOBtn').addEventListener('click', () => {
            this.handleOAuthLogin('reddit');
        });

        document.getElementById('signupXSSOBtn').addEventListener('click', () => {
            this.handleOAuthLogin('twitter');
        });

        // Form submissions
        document.getElementById('loginFormElement').addEventListener('submit', (e) => {
            this.handleLogin(e);
        });

        document.getElementById('signupFormElement').addEventListener('submit', (e) => {
            this.handleSignup(e);
        });

        document.getElementById('magicLinkFormElement').addEventListener('submit', (e) => {
            this.handleMagicLink(e);
        });

        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('active')) {
                this.hideModal();
            }
        });
    }

    async checkAuthStatus() {
        try {
            const response = await fetch('/auth/me');
            if (response.ok) {
                // User is already logged in, redirect to dashboard
                this.goToDashboard();
            }
        } catch (error) {
            // User not logged in, stay on homepage
        }
    }

    showModal(formType = 'login') {
        this.modal.classList.add('active');
        this.switchForm(formType);
        document.body.style.overflow = 'hidden';
        
        // Focus first input after animation
        setTimeout(() => {
            const firstInput = this.modal.querySelector(`#${formType}Form input`);
            if (firstInput) firstInput.focus();
        }, 300);
    }

    hideModal() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
        this.clearForms();
    }

    switchForm(formType) {
        // Hide all forms
        document.getElementById('loginForm').classList.add('hidden');
        document.getElementById('signupForm').classList.add('hidden');
        document.getElementById('magicLinkForm').classList.add('hidden');

        // Show target form
        document.getElementById(`${formType}Form`).classList.remove('hidden');
        this.currentForm = formType;

        // Add animation
        const activeForm = document.getElementById(`${formType}Form`);
        activeForm.classList.add('fade-in');
        setTimeout(() => {
            activeForm.classList.remove('fade-in');
        }, 600);
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const loginData = {
            email: formData.get('email'),
            password: formData.get('password')
        };

        this.setButtonLoading(e.target.querySelector('button[type="submit"]'), true);

        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(loginData),
                credentials: 'include' // Include cookies
            });

            const result = await response.json();

            if (response.ok) {
                this.showMessage('Login successful! Redirecting...', 'success');
                setTimeout(() => {
                    this.goToDashboard();
                }, 1500);
            } else {
                this.showMessage(result.detail || 'Login failed. Please check your credentials.', 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        } finally {
            this.setButtonLoading(e.target.querySelector('button[type="submit"]'), false);
        }
    }

    async handleSignup(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const signupData = {
            name: formData.get('name'),
            email: formData.get('email'),
            password: formData.get('password')
        };

        // Basic validation
        if (signupData.password.length < 12) {
            this.showMessage('Password must be at least 12 characters long.', 'error');
            return;
        }

        this.setButtonLoading(e.target.querySelector('button[type="submit"]'), true);

        try {
            const response = await fetch('/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(signupData)
            });

            const result = await response.json();

            if (response.ok) {
                this.showMessage('Account created successfully! Please log in.', 'success');
                this.switchForm('login');
                // Pre-fill email
                document.getElementById('loginEmail').value = signupData.email;
            } else {
                this.showMessage(result.detail || 'Signup failed. Please try again.', 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        } finally {
            this.setButtonLoading(e.target.querySelector('button[type="submit"]'), false);
        }
    }

    async handleMagicLink(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const magicLinkData = {
            email: formData.get('email')
        };

        this.setButtonLoading(e.target.querySelector('button[type="submit"]'), true);

        try {
            const response = await fetch('/auth/magic-link', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(magicLinkData)
            });

            const result = await response.json();

            if (response.ok) {
                this.showMessage('Magic link sent! Check your email and click the link to sign in.', 'success');
                this.hideModal();
            } else {
                this.showMessage(result.detail || 'Failed to send magic link. Please try again.', 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        } finally {
            this.setButtonLoading(e.target.querySelector('button[type="submit"]'), false);
        }
    }

    setButtonLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            const originalText = button.innerHTML;
            button.dataset.originalText = originalText;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> PROCESSING...';
        } else {
            button.disabled = false;
            button.innerHTML = button.dataset.originalText;
        }
    }

    showMessage(text, type = 'info') {
        const container = document.getElementById('messageContainer');
        
        const message = document.createElement('div');
        message.className = `message ${type}`;
        message.textContent = text;
        
        container.appendChild(message);
        
        // Trigger animation
        setTimeout(() => {
            message.classList.add('show');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            message.classList.remove('show');
            setTimeout(() => {
                if (container.contains(message)) {
                    container.removeChild(message);
                }
            }, 300);
        }, 5000);
    }

    clearForms() {
        document.getElementById('loginFormElement').reset();
        document.getElementById('signupFormElement').reset();
        document.getElementById('magicLinkFormElement').reset();
    }

    goToDashboard() {
        window.location.href = '/dashboard';
    }

    goToDemo() {
        window.location.href = '/demo';
    }

    handleOAuthLogin(provider) {
        // Show loading state
        this.showMessage(`Connecting to ${provider.charAt(0).toUpperCase() + provider.slice(1)}...`, 'info');
        
        // Redirect to OAuth endpoint
        window.location.href = `/auth/${provider}`;
    }

    animateHeroElements() {
        // Animate hero stats on page load
        const stats = document.querySelectorAll('.stat-number');
        
        stats.forEach((stat, index) => {
            setTimeout(() => {
                stat.style.transform = 'translateY(0)';
                stat.style.opacity = '1';
            }, index * 200);
        });

        // Animate chart bars
        const chartBars = document.querySelectorAll('.chart-bars .bar');
        chartBars.forEach((bar, index) => {
            bar.style.setProperty('--i', index);
        });
    }
}

// Initialize homepage when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Homepage();
});

// Add some Nike-style scroll effects
window.addEventListener('scroll', () => {
    const nav = document.querySelector('.nav');
    if (window.scrollY > 100) {
        nav.style.background = 'rgba(255, 255, 255, 0.98)';
        nav.style.borderBottomColor = 'rgba(0, 0, 0, 0.1)';
    } else {
        nav.style.background = 'rgba(255, 255, 255, 0.95)';
        nav.style.borderBottomColor = 'var(--border-color)';
    }
});
