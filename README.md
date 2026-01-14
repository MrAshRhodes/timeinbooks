# Quote O'Clock

A literary clock that tells time through quotes from books. Each minute displays a quote from literature that mentions that specific time.

## Features

- **Literary Quotes**: Displays quotes from books that mention the current time, with the time portion highlighted in bold
- **Light/Dark Mode**: Toggle between themes, or automatically follow system preference
- **12/24 Hour Format**: Switch between time formats - affects both the digital display and quote filtering (prefers quotes matching your format)
- **Timezone Selection**: Choose any timezone with auto-detection of your local zone
- **Page Turn Animation**: Book-like page turn effect on load (can be disabled)
- **Fallback Display**: Shows the digital time when no quote is available for the current minute

## Usage

Simply open `index.html` in a browser. No build tools or server required.

### Settings

Click the gear icon to access:
- Page animation toggle
- 12/24 hour format toggle
- Timezone selector

Click the sun/moon icon to toggle dark mode.

## Files

| File | Description |
|------|-------------|
| `index.html` | Main HTML structure |
| `styles.css` | Styling with CSS variables for theming |
| `app.js` | Application logic |
| `quotes.js` | Quote database keyed by time (HH:MM) |

## Credits

Quotes sourced from [literature-clock](https://github.com/JohannesNE/literature-clock) by Johannes Enevoldsen.

## License

MIT
