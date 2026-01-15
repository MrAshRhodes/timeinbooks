# Page Animation Timing Fix - Smooth Page Turn

## Problem
When the time changes, users see a "flash" where the quote visibly changes, then the page turn animation plays. The animation should be completely smooth - like turning a page in a real book.

## Root Cause
The current implementation uses `display: none` to hide the overlay between animations. When removed, the overlay "pops" into existence abruptly. Combined with timing issues, this creates a jarring flash.

## Solution: Two-Phase Page Turn Animation

Instead of toggling `display`, keep the overlay always rendered but positioned "turned away" at `rotateY(-95deg)`. The animation becomes:

1. **Page swings IN** (rotateY -95deg → 0deg) - covers the old content
2. **Content changes** while covered
3. **Page swings OUT** (rotateY 0deg → -95deg) - reveals new content

This mimics a real book page turn and is perfectly smooth.

---

## Files to Modify

### 1. `styles.css` - Animation Changes

**Remove** the `.hidden` class approach:
```css
/* DELETE THIS */
.page-turn-overlay.hidden {
    display: none;
}
```

**Add** new animation states:
```css
/* Overlay rests in "turned away" position when not animating */
.page-turn-overlay {
    /* ... existing styles ... */
    transform: perspective(2500px) rotateY(-95deg);
}

/* Phase 1: Page swings in to cover content */
.page-turn-overlay.swing-in {
    animation: pageSwingIn 0.8s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
}

/* Phase 2: Page swings out to reveal new content */
.page-turn-overlay.swing-out {
    animation: pageSwingOut 1.0s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
}

@keyframes pageSwingIn {
    0% {
        transform: perspective(2500px) rotateY(-95deg);
        box-shadow: 0 0 0 rgba(0,0,0,0);
    }
    100% {
        transform: perspective(2500px) rotateY(0deg);
        box-shadow: 5px 0 25px rgba(0,0,0,0.3);
    }
}

@keyframes pageSwingOut {
    0% {
        transform: perspective(2500px) rotateY(0deg);
        box-shadow: 5px 0 25px rgba(0,0,0,0.3);
    }
    40% {
        transform: perspective(2500px) rotateY(-25deg);
        box-shadow: 15px 0 35px rgba(0,0,0,0.35);
    }
    70% {
        transform: perspective(2500px) rotateY(-55deg);
        box-shadow: 25px 0 50px rgba(0,0,0,0.4);
    }
    100% {
        transform: perspective(2500px) rotateY(-95deg);
        box-shadow: 0 0 0 rgba(0,0,0,0);
    }
}
```

### 2. `app.js` - Animation Logic

**Replace** `playPageTurn` function:
```javascript
function playPageTurn(onCovered, onComplete) {
    // Phase 1: Page swings in to cover content
    pageOverlay.classList.remove('swing-out');
    pageOverlay.classList.add('swing-in');

    // Wait for swing-in to complete (0.8s)
    setTimeout(() => {
        // Content is now covered - update it
        if (onCovered) onCovered();

        // Small pause while covered, then swing out
        setTimeout(() => {
            // Phase 2: Page swings out to reveal new content
            pageOverlay.classList.remove('swing-in');
            pageOverlay.classList.add('swing-out');

            // Animation complete after swing-out (1.0s)
            setTimeout(() => {
                if (onComplete) onComplete();
            }, 1000);
        }, 100); // Brief pause while covered
    }, 800);
}
```

**Update** `initAnimation` to not use hidden class:
```javascript
function initAnimation() {
    const animationEnabled = localStorage.getItem('quote-clock-animation') !== 'false';
    animationToggle.checked = animationEnabled;
    // Remove: no need to manage hidden class on initial load
    // Overlay starts in "turned away" position via CSS
}
```

---

## Animation Timeline

```
Time 0ms     : Page starts turned away (rotateY -95deg)
Time 0-800ms : Page swings IN (covering old content)
Time 800ms   : Content updates underneath (invisible)
Time 900ms   : Page starts swinging OUT
Time 1900ms  : Page fully turned away, new content visible
```

**Total duration**: ~1.9 seconds for smooth, cinematic page turn

---

## Initial Page Load

On first load, the overlay should start covering (rotateY 0deg), then swing out to reveal the first quote. Add to `initAnimation`:

```javascript
function initAnimation() {
    const animationEnabled = localStorage.getItem('quote-clock-animation') !== 'false';
    animationToggle.checked = animationEnabled;

    if (animationEnabled) {
        // Start covering, will swing out after first quote loads
        pageOverlay.style.transform = 'perspective(2500px) rotateY(0deg)';
    }
}
```

Then in `updateClock` for first load:
```javascript
if (isFirstLoad && isAnimationEnabled()) {
    renderQuote(quote);
    updateDigitalTime();
    // Swing out to reveal first quote
    setTimeout(() => {
        pageOverlay.classList.add('swing-out');
    }, 100);
}
```

---

## Verification

1. Open `index.html` in browser
2. On load: page should swing away to reveal first quote
3. Wait for minute change (or test with shortened interval)
4. Observe: page swings in smoothly, pauses briefly, swings out to reveal new quote
5. No flash, no pop, completely smooth
6. Test both light and dark themes

---

## Summary of Changes

| File | Change |
|------|--------|
| `styles.css` | Remove `.hidden` class, add default rotateY(-95deg), add `swing-in` and `swing-out` animations |
| `app.js` | Rewrite `playPageTurn` for two-phase animation, update `initAnimation` and first-load handling |
