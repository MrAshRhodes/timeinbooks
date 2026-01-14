# Page Turn Animation Feature

## Overview
Add a book-like page-turn animation that plays on page load/refresh, originating from the bottom-left corner. Include a toggle to disable the animation.

---

## Implementation

### 1. HTML Changes (`index.html`)

Add a page-turn overlay element before the container:
```html
<div class="page-turn-overlay"></div>
```

Add animation toggle to the settings panel:
```html
<div class="setting-row">
    <label for="animation-toggle">Page animation</label>
    <input type="checkbox" id="animation-toggle" checked>
</div>
```

### 2. CSS Changes (`styles.css`)

Add page-turn overlay and animation:
```css
/* Page Turn Animation */
.page-turn-overlay {
    position: fixed;
    inset: 0;
    background-color: var(--bg-color);
    transform-origin: bottom left;
    z-index: 200;
    pointer-events: none;
}

.page-turn-overlay.animate {
    animation: pageTurn 0.8s ease-out forwards;
}

@keyframes pageTurn {
    0% {
        transform: rotateY(0deg) rotateZ(0deg);
        opacity: 1;
    }
    100% {
        transform: rotateY(-90deg) rotateZ(-15deg);
        opacity: 0;
    }
}

/* Hide overlay when no animation */
.page-turn-overlay.hidden {
    display: none;
}
```

Add checkbox styling for settings:
```css
.setting-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.setting-row input[type="checkbox"] {
    width: 1.25rem;
    height: 1.25rem;
    cursor: pointer;
}
```

### 3. JavaScript Changes (`app.js`)

Add new DOM element reference:
```javascript
const animationToggle = document.getElementById('animation-toggle');
const pageOverlay = document.querySelector('.page-turn-overlay');
```

Add animation preference handling:
```javascript
function initAnimation() {
    const animationEnabled = localStorage.getItem('quote-clock-animation') !== 'false';
    animationToggle.checked = animationEnabled;

    if (animationEnabled) {
        pageOverlay.classList.add('animate');
        // Remove overlay after animation completes
        setTimeout(() => {
            pageOverlay.classList.add('hidden');
        }, 800);
    } else {
        pageOverlay.classList.add('hidden');
    }
}

function setAnimation(enabled) {
    localStorage.setItem('quote-clock-animation', enabled);
}
```

Add event binding:
```javascript
animationToggle.addEventListener('change', (e) => {
    setAnimation(e.target.checked);
});
```

Call `initAnimation()` in `init()` function.

---

## Files to Modify

| File | Changes |
|------|---------|
| `index.html` | Add overlay element, add checkbox toggle in settings |
| `styles.css` | Add page-turn animation, overlay styles, checkbox styles |
| `app.js` | Add animation init, toggle handling, localStorage |

---

## Verification

1. Open the page - animation should play from bottom-left
2. Refresh - animation should play again
3. Open settings, disable animation toggle
4. Refresh - no animation should play
5. Enable animation again, refresh - animation should return
6. Test in both light and dark modes
