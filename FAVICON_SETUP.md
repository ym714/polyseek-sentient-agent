# Favicon Setup Guide

This guide explains how to set up the favicon (icon) displayed in browser tabs.

## Current Setup

The following configuration has been added to `frontend/index.html`:

```html
<!-- Favicon -->
<link rel="icon" type="image/png" href="./assets/image.png">
<link rel="apple-touch-icon" href="./assets/image.png">
<link rel="shortcut icon" href="./assets/image.png">
```

## Icon File Preparation

### Method 1: Use Existing Logo

Currently, `frontend/assets/image.png` is being used. Verify that this file exists.

### Method 2: Create Dedicated Favicon

To create a more optimal favicon:

1. **Recommended Sizes**
   - `favicon.ico`: 16x16, 32x32, 48x48 (multi-size)
   - `favicon.png`: 32x32 or 64x64
   - `apple-touch-icon.png`: 180x180 (for iOS)

2. **Online Tools**
   - [Favicon Generator](https://www.favicon-generator.org/)
   - [RealFaviconGenerator](https://realfavicongenerator.net/)
   - [Favicon.io](https://favicon.io/)

3. **Creation Steps**
   ```
   1. Prepare logo image (square recommended)
   2. Generate favicon using online tools
   3. Place generated files in frontend/assets/
   4. Update HTML paths
   ```

## Customization

### Set Multiple Sizes

```html
<link rel="icon" type="image/png" sizes="32x32" href="./assets/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="./assets/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="./assets/apple-touch-icon.png">
```

### Use SVG Favicon (Recommended)

```html
<link rel="icon" type="image/svg+xml" href="./assets/favicon.svg">
```

SVG favicon advantages:
- Scalable (sharp at any size)
- Smaller file size
- Dark mode support possible

## Vercel Deployment Notes

When deploying to Vercel, ensure static file paths are correctly configured:

1. Verify static file routing in `vercel.json`
2. Verify that `frontend/assets/` directory is properly served

## Troubleshooting

### Icon Not Displaying

1. **Clear Browser Cache**
   - Hard reload: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)

2. **Verify File Path**
   - Verify file is in the correct location
   - Verify path starts with `./assets/` (relative path)

3. **Verify File Format**
   - Verify PNG format loads correctly
   - Verify file size is not too large (recommended: under 100KB)

4. **Check Console for Errors**
   - Open browser developer tools (F12) to check for errors
   - Check Network tab to verify favicon requests are not 404

## Reference Links

- [MDN: Favicon](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/link#linking_to_favicons)
- [Favicon Best Practices](https://www.w3.org/2005/10/howto-favicon)
