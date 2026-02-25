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

// Project Modal Data
const projectData = {
    osms: {
        title: 'OSMS – Online Shopping Management System',
        overview: 'OSMS is a role-based web application designed to manage online shopping operations for administrators and sellers. The system supports product management, order processing, and user control with structured database integration.',
        implemented: [
            'Role-based authentication (Admin & Seller)',
            'CRUD operations for products and orders',
            'MySQL database schema design',
            'JDBC database connectivity',
            'Dynamic JSP rendering',
            'Backend logic using Servlets'
        ],
        technologies: ['Java', 'JSP & Servlet', 'MySQL', 'JDBC', 'HTML, CSS', 'Bootstrap', 'Apache Tomcat'],
        learning: 'Strengthened understanding of MVC architecture, session management, and database-driven web applications.'
    },
    inventory: {
        title: 'Inventory Management API',
        overview: 'A RESTful backend API built using Django and Django REST Framework to manage inventory operations such as product creation, stock updates, and data tracking.',
        implemented: [
            'REST API endpoints (GET, POST, PUT, DELETE)',
            'Model relationships',
            'Serializer configurations',
            'Authentication mechanisms',
            'Database integration',
            'API testing with Postman'
        ],
        technologies: ['Python', 'Django', 'Django REST Framework', 'SQLite / MySQL', 'Postman'],
        learning: 'Improved API design skills, backend architecture structuring, and scalable application logic.'
    },
    hangart: {
        title: 'HangaArt – Creative Content Platform',
        overview: 'HangaArt is a Django-based web application designed to manage and display artistic or creative content dynamically using database-driven templates.',
        implemented: [
            'Django models and relationships',
            'Admin panel customization',
            'Template inheritance',
            'Dynamic content rendering',
            'Static file management'
        ],
        technologies: ['Python', 'Django', 'HTML & CSS', 'SQLite', 'Django Admin'],
        learning: 'Gained deeper knowledge of Django\'s full-stack capabilities and template rendering engine.'
    },
    kush: {
        title: 'e-Commerce Kush',
        overview: 'A responsive frontend e-commerce website developed to showcase fashion products with a clean and interactive layout.',
        implemented: [
            'Product display interface',
            'Responsive design layout',
            'Interactive UI components',
            'Structured page navigation'
        ],
        technologies: ['HTML', 'CSS', 'JavaScript'],
        learning: 'Strengthened frontend layout structuring and responsive design implementation.'
    },
    phone: {
        title: 'Phone Agreement Management System',
        overview: 'A web-based system prototype developed to manage phone contract agreements and customer records.',
        implemented: [
            'Structured forms for agreement data',
            'Organized layout for contract display',
            'User-friendly interface design'
        ],
        technologies: ['HTML', 'CSS', 'JavaScript'],
        learning: 'Improved user interface structuring and form data organization.'
    },
    housing: {
        title: 'Housing Price Prediction',
        overview: 'Built regression models to predict housing prices using real-world datasets.',
        implemented: [
            'Data cleaning & preprocessing',
            'Exploratory Data Analysis (EDA)',
            'Train-test split',
            'Linear regression modeling',
            'Model evaluation (RMSE, R²)',
            'Hyperparameter tuning'
        ],
        technologies: ['Python', 'Pandas', 'NumPy', 'Matplotlib', 'Scikit-learn', 'Jupyter Notebook'],
        learning: 'Developed practical understanding of regression algorithms and model optimization techniques.'
    },
    airquality: {
        title: 'Air Quality Analysis',
        overview: 'Analyzed environmental pollution data to identify patterns and trends using statistical and visualization techniques.',
        implemented: [
            'Data visualization',
            'Feature correlation analysis',
            'Trend identification',
            'Statistical summaries'
        ],
        technologies: ['Python', 'Pandas', 'Matplotlib', 'Scikit-learn'],
        learning: 'Enhanced data analysis and visualization skills for environmental data interpretation.'
    }
};

// Open Project Modal
function openModal(projectId) {
    const project = projectData[projectId];
    const modal = document.getElementById('projectModal');
    const modalBody = document.getElementById('modalBody');
    
    let implementedList = project.implemented.map(item => `<li>${item}</li>`).join('');
    let techList = project.technologies.map(tech => `<span class="tag">${tech}</span>`).join('');
    
    modalBody.innerHTML = `
        <h2>${project.title}</h2>
        <div style="margin-top: 1.5rem;">
            <h3 style="color: var(--primary-color); margin-bottom: 1rem;">Overview</h3>
            <p style="line-height: 1.7; color: var(--text-light);">${project.overview}</p>
        </div>
        <div style="margin-top: 2rem;">
            <h3 style="color: var(--primary-color); margin-bottom: 1rem;">What I Implemented</h3>
            <ul style="list-style-position: inside; color: var(--text-light); line-height: 1.8;">
                ${implementedList}
            </ul>
        </div>
        <div style="margin-top: 2rem;">
            <h3 style="color: var(--primary-color); margin-bottom: 1rem;">Technologies Used</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                ${techList}
            </div>
        </div>
        <div style="margin-top: 2rem; background: var(--bg-light); padding: 1.5rem; border-radius: 8px; border-left: 4px solid var(--success-color);">
            <h3 style="color: var(--success-color); margin-bottom: 0.5rem;">Key Learning Outcome</h3>
            <p style="color: var(--text-light);">${project.learning}</p>
        </div>
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

// Contact Form Submission
document.getElementById('contactForm').addEventListener('submit', function(e) {
    e.preventDefault();
    alert('Thank you for your message! I will get back to you soon.');
    this.reset();
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

console.log('Portfolio loaded successfully! 🚀');
