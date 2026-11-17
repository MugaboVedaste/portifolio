// Matrix Rain Animation
const canvas = document.getElementById('matrixCanvas');
const ctx = canvas ? canvas.getContext('2d') : null;

// Set canvas size
function resizeCanvas() {
    if (!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

// Matrix characters - mix of code symbols and data
const matrixChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*(){}[]<>/\\|~`+-=';
const codeWords = ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'class', 'def', 'import', 'return', 'async', 'await', 'try', 'catch'];
const chars = matrixChars.split('');

const fontSize = 14;
const columns = canvas ? canvas.width / fontSize : 0;
const drops = [];

// Initialize drops
for (let i = 0; i < columns; i++) {
    drops[i] = Math.random() * -100;
}

// Draw matrix rain
function drawMatrix() {
    if (!canvas) return;
    // Semi-transparent black to create trailing effect
    ctx.fillStyle = 'rgba(15, 23, 42, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.font = fontSize + 'px monospace';

    for (let i = 0; i < drops.length; i++) {
        // Random character or code word
        const text = Math.random() > 0.95 ? 
            codeWords[Math.floor(Math.random() * codeWords.length)] : 
            chars[Math.floor(Math.random() * chars.length)];

        // Gradient effect - brighter at the tip
        const gradient = ctx.createLinearGradient(0, drops[i] * fontSize, 0, (drops[i] + 1) * fontSize);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.8)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.2)');
        ctx.fillStyle = gradient;

        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

        // Reset drop to top randomly
        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
            drops[i] = 0;
        }

        drops[i]++;
    }
}

// Animation loop
setInterval(drawMatrix, 50);

// Loading Screen
window.addEventListener('load', () => {
    const loadingScreen = document.getElementById('loading-screen');
    if (!loadingScreen) return;
    setTimeout(() => {
        loadingScreen.classList.add('fade-out');
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 500);
    }, 1500);
});

// Typing Animation Effect
const typingElement = document.getElementById('typing');
const texts = [
    'Vedaste MUGABO',
    'Data Engineer',
    'Data Scientist',
    'Backend Developer',
    'Software Tester',
    'Translator'
];
let textIndex = 0;
let charIndex = 0;
let isDeleting = false;
let typingSpeed = 100;

function typeText() {
    if (!typingElement) return;
    const currentText = texts[textIndex];
    
    if (isDeleting) {
        typingElement.textContent = currentText.substring(0, charIndex - 1);
        charIndex--;
        typingSpeed = 50;
    } else {
        typingElement.textContent = currentText.substring(0, charIndex + 1);
        charIndex++;
        typingSpeed = 100;
    }
    
    if (!isDeleting && charIndex === currentText.length) {
        // Pause at end of text
        typingSpeed = 2000;
        isDeleting = true;
    } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        textIndex = (textIndex + 1) % texts.length;
        typingSpeed = 500;
    }
    
    setTimeout(typeText, typingSpeed);
}

// Start typing animation when page loads
window.addEventListener('DOMContentLoaded', () => {
    setTimeout(typeText, 500);
});

// Mobile Navigation Toggle
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');

navToggle.addEventListener('click', () => {
    navMenu.classList.toggle('active');
});

// Close mobile menu when clicking on a link
document.querySelectorAll('.nav-menu a').forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('active');
    });
});

// Smooth scrolling for navigation links
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

// Add active class to navigation on scroll
window.addEventListener('scroll', () => {
    let current = '';
    const sections = document.querySelectorAll('section');
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (pageYOffset >= sectionTop - 200) {
            current = section.getAttribute('id');
        }
    });

    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${current}`) {
            link.classList.add('active');
        }
    });
});

// Project Modal Data (rendered by the Flask backend from the database)
const projectData = window.PROJECT_DATA || {};

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
}

// Open Project Modal
function openModal(projectId) {
    const project = projectData[projectId];
    if (!project) return;
    const modal = document.getElementById('projectModal');
    const modalBody = document.getElementById('modalBody');

    let implementedList = (project.implemented || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
    let techList = (project.technologies || []).map(tech => `<span class="tag">${escapeHtml(tech)}</span>`).join('');

    modalBody.innerHTML = `
        <h2>${escapeHtml(project.title)}</h2>
        <div style="margin-top: 1.5rem;">
            <h3 style="color: var(--primary-color); margin-bottom: 1rem;">Overview</h3>
            <p style="line-height: 1.7; color: var(--text-light);">${escapeHtml(project.overview)}</p>
        </div>
        ${implementedList ? `
        <div style="margin-top: 2rem;">
            <h3 style="color: var(--primary-color); margin-bottom: 1rem;">What I Implemented</h3>
            <ul style="list-style-position: inside; color: var(--text-light); line-height: 1.8;">
                ${implementedList}
            </ul>
        </div>` : ''}
        ${techList ? `
        <div style="margin-top: 2rem;">
            <h3 style="color: var(--primary-color); margin-bottom: 1rem;">Technologies Used</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                ${techList}
            </div>
        </div>` : ''}
        ${project.learning ? `
        <div style="margin-top: 2rem; background: var(--bg-light); padding: 1.5rem; border-radius: 8px; border-left: 4px solid var(--success-color);">
            <h3 style="color: var(--success-color); margin-bottom: 0.5rem;">Key Learning Outcome</h3>
            <p style="color: var(--text-light);">${escapeHtml(project.learning)}</p>
        </div>` : ''}
    `;

    modal.style.display = 'block';
}

// Close Modal
function closeModal() {
    const modal = document.getElementById('projectModal');
    modal.style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('projectModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

// Contact Form Submission (sends via EmailJS)
const contactForm = document.getElementById('contactForm');
if (contactForm) contactForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const form = this;
    const name = form.querySelector('input[type="text"]').value.trim();
    const email = form.querySelector('input[type="email"]').value.trim();
    const message = form.querySelector('textarea').value.trim();

    // Replace with your EmailJS Service ID
    const serviceID = 'service_khydfnh';
    const templateID = 'template_3pss5mb';

    // Template parameters expected by EmailJS template: `from_name`, `email`, `message`
    const templateParams = {
        from_name: name,
        email: email,
        message: message
    };

    emailjs.send(serviceID, templateID, templateParams)
        .then(() => {
            alert('Thank you for your message! I will get back to you soon.');
            form.reset();
        }, (err) => {
            console.error('EmailJS error:', err);
            alert('Sorry — message failed to send. Please try again later.');
        });
});

// Add animation on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all project cards and experience cards
document.querySelectorAll('.project-card, .experience-card, .skill-category').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// Certificates Carousel (horizontal sliding track)
let currentSlide = 0;
const certificateTrack = document.querySelector('.certificate-track');
const slides = document.querySelectorAll('.certificate-slide');
const dots = document.querySelectorAll('.dot');
const totalSlides = slides.length;

function updateTrackPosition() {
    if (!certificateTrack) return;
    certificateTrack.style.transform = `translateX(-${currentSlide * 100}%)`;
}

function updateDots() {
    dots.forEach(dot => dot.classList.remove('active'));
    if (dots[currentSlide]) dots[currentSlide].classList.add('active');
}

function showSlide(index) {
    // Wrap around
    if (index >= totalSlides) {
        currentSlide = 0;
    } else if (index < 0) {
        currentSlide = totalSlides - 1;
    } else {
        currentSlide = index;
    }

    updateTrackPosition();
    updateDots();
}

function nextCertificate() {
    showSlide(currentSlide + 1);
}

function prevCertificate() {
    showSlide(currentSlide - 1);
}

function goToSlide(index) {
    showSlide(index);
}

// Initialize position
showSlide(0);

// Auto-advance carousel every 5 seconds
setInterval(() => {
    nextCertificate();
}, 5000);

// Visit counter: one anonymous ping per page per browser session (no cookies).
try {
    const visitKey = 'visit:' + location.pathname;
    if (!sessionStorage.getItem(visitKey)) {
        sessionStorage.setItem(visitKey, '1');
        fetch('/api/visit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: location.pathname, ref: document.referrer }),
            keepalive: true
        }).catch(() => {});
    }
} catch (e) { /* storage blocked: skip counting */ }

console.log('Portfolio loaded successfully! 🚀');
