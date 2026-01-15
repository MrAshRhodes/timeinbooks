// Literary Quote Clock - Application Logic

(function() {
    'use strict';

    // DOM Elements
    const quoteFirst = document.getElementById('quote-first');
    const quoteTime = document.getElementById('quote-time');
    const quoteLast = document.getElementById('quote-last');
    const authorEl = document.getElementById('author');
    const titleEl = document.getElementById('title');
    const themeToggle = document.getElementById('theme-toggle');
    const settingsToggle = document.getElementById('settings-toggle');
    const settingsPanel = document.getElementById('settings-panel');
    const timezoneSelect = document.getElementById('timezone-select');
    const digitalTime = document.getElementById('digital-time');
    const container = document.querySelector('.container');
    const animationToggle = document.getElementById('animation-toggle');
    const formatToggle = document.getElementById('format-toggle');
    const loader = document.querySelector('.loader');

    // State
    let currentTimezone = null;
    let lastDisplayedMinute = null;
    let overlay = null;
    let use24Hour = true;

    // Initialize
    function init() {
        initTheme();
        initAnimation();
        initTimeFormat();
        initTimezone();
        initOverlay();
        bindEvents();
        updateClock();
        scheduleNextUpdate();
    }

    // Theme Management
    function initTheme() {
        const savedTheme = localStorage.getItem('quote-clock-theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        }
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        let newTheme;
        if (currentTheme === 'dark') {
            newTheme = 'light';
        } else if (currentTheme === 'light') {
            newTheme = 'dark';
        } else {
            // No explicit theme set, toggle from system preference
            newTheme = prefersDark ? 'light' : 'dark';
        }

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('quote-clock-theme', newTheme);
    }

    // Page Animation using GSAP
    function initAnimation() {
        const animationEnabled = localStorage.getItem('quote-clock-animation') !== 'false';
        animationToggle.checked = animationEnabled;
        // Loader tiles start collapsed (width: 0 via CSS), no setup needed
    }

    function isAnimationEnabled() {
        return localStorage.getItem('quote-clock-animation') !== 'false';
    }

    function playPageTurn(onCovered, onComplete) {
        // Activate loader - tiles expand from left with stagger
        loader.classList.add('loader--active');

        // Wait for tiles to fully cover screen (~2s)
        setTimeout(() => {
            // Content is now covered - update it
            if (onCovered) onCovered();

            // Brief pause while covered, then collapse
            setTimeout(() => {
                // Remove active class - tiles collapse with stagger
                loader.classList.remove('loader--active');

                // Wait for tiles to fully collapse (~2s)
                setTimeout(() => {
                    if (onComplete) onComplete();
                }, 2200);
            }, 300);
        }, 2200);
    }

    function setAnimation(enabled) {
        localStorage.setItem('quote-clock-animation', enabled);
    }

    // Time Format
    function initTimeFormat() {
        const saved = localStorage.getItem('quote-clock-24hour');
        use24Hour = saved !== 'false';
        formatToggle.checked = use24Hour;
    }

    function setTimeFormat(is24Hour) {
        use24Hour = is24Hour;
        localStorage.setItem('quote-clock-24hour', is24Hour);
        lastDisplayedMinute = null; // Force quote refresh
        updateClock();
    }

    // Timezone Management
    function initTimezone() {
        populateTimezones();

        const savedTimezone = localStorage.getItem('quote-clock-timezone');
        const detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

        currentTimezone = savedTimezone || detectedTimezone;
        timezoneSelect.value = currentTimezone;
    }

    function populateTimezones() {
        const timezones = Intl.supportedValuesOf('timeZone');
        const detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

        timezones.forEach(tz => {
            const option = document.createElement('option');
            option.value = tz;
            option.textContent = tz.replace(/_/g, ' ');
            if (tz === detectedTimezone) {
                option.textContent += ' (detected)';
            }
            timezoneSelect.appendChild(option);
        });
    }

    function setTimezone(tz) {
        currentTimezone = tz;
        localStorage.setItem('quote-clock-timezone', tz);
        lastDisplayedMinute = null; // Force update
        updateClock();
    }

    // Settings Panel
    function initOverlay() {
        overlay = document.createElement('div');
        overlay.className = 'overlay';
        document.body.appendChild(overlay);
    }

    function toggleSettings() {
        const isOpen = settingsPanel.classList.contains('open');
        if (isOpen) {
            closeSettings();
        } else {
            openSettings();
        }
    }

    function openSettings() {
        settingsPanel.classList.add('open');
        overlay.classList.add('open');
    }

    function closeSettings() {
        settingsPanel.classList.remove('open');
        overlay.classList.remove('open');
    }

    // Clock Logic
    function getCurrentTime() {
        const now = new Date();
        const formatter = new Intl.DateTimeFormat('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: currentTimezone
        });

        const parts = formatter.formatToParts(now);
        const hour = parseInt(parts.find(p => p.type === 'hour').value, 10);
        const minute = parseInt(parts.find(p => p.type === 'minute').value, 10);

        return { hour, minute };
    }

    function formatTimeKey(hour, minute) {
        const h = hour.toString().padStart(2, '0');
        const m = minute.toString().padStart(2, '0');
        return `${h}:${m}`;
    }

    function is24HourQuote(quote) {
        const timeText = quote.quote_time_case || '';
        // Contains hours 13-23 = definitely 24h
        if (/\b(1[3-9]|2[0-3])\b/.test(timeText)) return true;
        // Contains AM/PM indicators = definitely 12h
        if (/\b(am|pm|a\.m\.|p\.m\.)\b/i.test(timeText)) return false;
        // Contains morning/evening/night/afternoon = 12h style
        if (/\b(morning|evening|night|afternoon)\b/i.test(timeText)) return false;
        // Default: treat as ambiguous (works for both)
        return null;
    }

    function getQuoteForTime(hour, minute) {
        const timeKey = formatTimeKey(hour, minute);
        const quotes = QUOTES[timeKey];

        if (!quotes || quotes.length === 0) {
            return null;
        }

        // Filter by preferred format
        const preferred = quotes.filter(q => {
            const is24h = is24HourQuote(q);
            if (is24h === null) return true; // Ambiguous quotes work for both
            return is24h === use24Hour;
        });

        // Use preferred if available, otherwise fall back to any
        const pool = preferred.length > 0 ? preferred : quotes;
        return pool[Math.floor(Math.random() * pool.length)];
    }

    function cleanHtml(text) {
        // Remove any HTML tags like <br/> and convert to plain text
        if (!text) return '';
        return text.replace(/<br\s*\/?>/gi, ' ').replace(/<[^>]*>/g, '');
    }

    function getFormattedTime() {
        const now = new Date();
        const formatter = new Intl.DateTimeFormat('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: !use24Hour,
            timeZone: currentTimezone
        });
        return formatter.format(now);
    }

    function renderQuote(quote) {
        if (!quote) {
            quoteFirst.textContent = 'No quote available for ';
            quoteTime.textContent = getFormattedTime();
            quoteLast.textContent = '';
            authorEl.textContent = '';
            titleEl.textContent = '';
            return;
        }

        quoteFirst.textContent = cleanHtml(quote.quote_first);
        quoteTime.textContent = cleanHtml(quote.quote_time_case);
        quoteLast.textContent = cleanHtml(quote.quote_last);
        authorEl.textContent = quote.author || 'Unknown';
        titleEl.textContent = quote.title || '';
    }

    function updateDigitalTime() {
        const now = new Date();
        const formatter = new Intl.DateTimeFormat('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: !use24Hour,
            timeZone: currentTimezone
        });
        digitalTime.textContent = formatter.format(now);
    }

    function updateClock() {
        const { hour, minute } = getCurrentTime();
        const currentMinute = hour * 60 + minute;

        // Only update if minute has changed
        if (currentMinute === lastDisplayedMinute) {
            updateDigitalTime();
            return;
        }

        const isFirstLoad = lastDisplayedMinute === null;
        lastDisplayedMinute = currentMinute;

        const quote = getQuoteForTime(hour, minute);

        if (isFirstLoad) {
            // First load: just render content (tiles are already collapsed)
            renderQuote(quote);
            updateDigitalTime();
        } else if (isAnimationEnabled()) {
            // Minute change with animation: full swing-in/swing-out cycle
            playPageTurn(
                // Called when overlay covers the content - update quote here
                () => {
                    renderQuote(quote);
                    updateDigitalTime();
                },
                null
            );
        } else {
            // Animation disabled - just render
            renderQuote(quote);
            updateDigitalTime();
        }
    }

    function scheduleNextUpdate() {
        // Calculate milliseconds until next minute
        const now = new Date();
        const msUntilNextMinute = (60 - now.getSeconds()) * 1000 - now.getMilliseconds();

        setTimeout(() => {
            updateClock();
            // After first alignment, update every minute
            setInterval(updateClock, 60000);
        }, msUntilNextMinute);

        // Also update digital time every second
        setInterval(updateDigitalTime, 1000);
    }

    // Event Bindings
    function bindEvents() {
        themeToggle.addEventListener('click', toggleTheme);
        settingsToggle.addEventListener('click', toggleSettings);
        overlay.addEventListener('click', closeSettings);

        timezoneSelect.addEventListener('change', (e) => {
            setTimezone(e.target.value);
        });

        animationToggle.addEventListener('change', (e) => {
            setAnimation(e.target.checked);
        });

        formatToggle.addEventListener('change', (e) => {
            setTimeFormat(e.target.checked);
        });

        // Close settings on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && settingsPanel.classList.contains('open')) {
                closeSettings();
            }
        });
    }

    // Start the app
    init();
})();
