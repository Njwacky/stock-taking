// Developer Page Interactive Enhancements

document.addEventListener('DOMContentLoaded', function() {
    // Add intersection observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe elements for animation
    const animatedElements = document.querySelectorAll('.project-card, .skill-item, .contact-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    // Add typing effect to the main title
    const mainTitle = document.querySelector('.dev-title h1');
    if (mainTitle) {
        const originalText = mainTitle.textContent;
        mainTitle.textContent = '';
        mainTitle.style.borderRight = '3px solid #667eea';
        mainTitle.style.animation = 'blink 1s infinite';
        
        let charIndex = 0;
        const typeWriter = setInterval(() => {
            if (charIndex < originalText.length) {
                mainTitle.textContent += originalText.charAt(charIndex);
                charIndex++;
            } else {
                clearInterval(typeWriter);
                mainTitle.style.borderRight = 'none';
                mainTitle.style.animation = 'none';
            }
        }, 100);
    }

    // Add hover effect to tech tags
    const techTags = document.querySelectorAll('.tech-tag');
    techTags.forEach(tag => {
        tag.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1) rotate(2deg)';
        });
        
        tag.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) rotate(0deg)';
        });
    });

    // Add ripple effect to contact cards
    const contactCards = document.querySelectorAll('.contact-card');
    contactCards.forEach(card => {
        card.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    // Add parallax effect to header
    const header = document.querySelector('.dev-header');
    if (header) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            
            if (scrolled < 500) {
                header.style.transform = `translateY(${rate}px)`;
                header.style.opacity = 1 - (scrolled / 500);
            }
        });
    }

    // Add skill progress bars animation
    const skillItems = document.querySelectorAll('.skill-item');
    skillItems.forEach((item, index) => {
        setTimeout(() => {
            item.style.animation = 'slideInUp 0.6s ease-out forwards';
        }, index * 100);
    });

    // Add smooth scroll for internal navigation (if we add anchor links later)
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
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

    // Add dynamic year to footer (if needed)
    const currentYear = new Date().getFullYear();
    const yearElements = document.querySelectorAll('[data-year]');
    yearElements.forEach(el => {
        el.textContent = currentYear;
    });
});

// Add CSS for ripple effect
const style = document.createElement('style');
style.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    @keyframes blink {
        0%, 50% { border-color: #667eea; }
        51%, 100% { border-color: transparent; }
    }
    
    .contact-card {
        position: relative;
        overflow: hidden;
    }
`;
document.head.appendChild(style);
