(function () {
    'use strict';

    function updateHeaderState(header) {
        if (!header) return;
        header.classList.toggle('scrolled', window.scrollY > 50);
    }

    function setupMobileMenu(menuButton, navLinks) {
        if (!menuButton || !navLinks) return;

        const iconEl = menuButton.querySelector('[data-lucide]');
        const labelEl = menuButton.querySelector('span');

        const syncMenuState = (isOpen) => {
            if (labelEl) labelEl.textContent = isOpen ? 'Close' : 'Menu';
            if (iconEl) {
                iconEl.setAttribute('data-lucide', isOpen ? 'x' : 'menu');
                if (window.lucide && typeof window.lucide.createIcons === 'function') {
                    window.lucide.createIcons();
                }
            }
        };

        const closeMenu = () => {
            navLinks.classList.remove('active');
            syncMenuState(false);
        };

        menuButton.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            syncMenuState(navLinks.classList.contains('active'));
        });

        document.querySelectorAll('.nav-links a').forEach(link => {
            link.addEventListener('click', closeMenu);
        });
    }

    function copyCitation() {
        const citation = document.getElementById('bibtex');
        const button = document.getElementById('copy-citation-btn');
        if (!citation || !button) return;

        navigator.clipboard.writeText(citation.innerText).then(() => {
            const originalText = button.textContent;
            button.textContent = 'Copied';
            button.classList.add('success');

            setTimeout(() => {
                button.textContent = originalText;
                button.classList.remove('success');
            }, 1800);
        }).catch(error => {
            console.error('Failed to copy citation text:', error);
        });
    }

    function setupCitationCopy() {
        const button = document.getElementById('copy-citation-btn');
        if (!button) return;
        button.addEventListener('click', copyCitation);
    }

    function setupContributeModal() {
        const modal = document.getElementById('contribute-modal');
        if (!modal) return;

        const openers = document.querySelectorAll('[data-open-contribute]');
        const closeButton = document.getElementById('contribute-close-btn');

        const openModal = () => {
            modal.classList.add('is-open');
            modal.setAttribute('aria-hidden', 'false');
            document.body.classList.add('contribute-modal-open');
        };

        const closeModal = () => {
            modal.classList.remove('is-open');
            modal.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('contribute-modal-open');
        };

        openers.forEach(opener => {
            opener.addEventListener('click', openModal);
        });

        if (closeButton) {
            closeButton.addEventListener('click', closeModal);
        }

        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                closeModal();
            }
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && modal.classList.contains('is-open')) {
                closeModal();
            }
        });
    }

    function setupDatasetAccordion() {
        const root = document.getElementById('dataset-accordion-root');
        if (!root) return;

        root.addEventListener('click', (event) => {
            const header = event.target.closest('.accordion-header');
            if (!header || !root.contains(header)) return;

            const item = header.closest('.accordion-item');
            if (!item) return;

            const isActive = item.classList.toggle('active');
            header.setAttribute('aria-expanded', String(isActive));
        });

        // Keep all sections collapsed by default.
    }

    function initPage() {
        setupDatasetAccordion();
        setupCitationCopy();
        setupContributeModal();

        const header = document.querySelector('.site-header');
        updateHeaderState(header);
        window.addEventListener('scroll', () => updateHeaderState(header));

        const mobileMenuButton = document.querySelector('.mobile-menu-btn');
        const navLinks = document.querySelector('.nav-links');
        setupMobileMenu(mobileMenuButton, navLinks);

        if (window.lucide && typeof window.lucide.createIcons === 'function') {
            window.lucide.createIcons();
            document.querySelectorAll('.github-link').forEach(link => {
                if (!link.querySelector('svg')) {
                    const icon = document.createElement('i');
                    icon.className = 'icon';
                    icon.setAttribute('data-lucide', 'github');
                    link.insertAdjacentElement('afterbegin', icon);
                }
            });
            window.lucide.createIcons();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPage);
    } else {
        initPage();
    }
})();
