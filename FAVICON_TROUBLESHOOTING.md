# Favicon Troubleshooting Guide

## Verification Steps

### 1. Verify File Exists

```bash
ls -la frontend/assets/image.png
```

Verify that the file exists.

### 2. Clear Browser Cache

- **Chrome/Edge**: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- **Firefox**: `Cmd+Shift+R` (Mac) or `Ctrl+F5` (Windows)
- **Safari**: `Cmd+Option+R`

### 3. Check Developer Tools

1. Open browser developer tools (F12)
2. Open Network tab
3. Reload the page
4. Filter by `image.png` or `favicon`
5. Verify requests are not returning 404

### 4. Access Direct URL

Access the following URL directly in your browser to verify the image displays:

```
http://localhost:3000/assets/image.png
```

### 5. Verify HTML Path

Verify the favicon path in `frontend/index.html`:

```html
<link rel="icon" type="image/png" href="./assets/image.png">
```

**Note**: Path should start with `./assets/` (relative path)

## Solutions

### Method 1: Rename File

Rename `image.png` to `favicon.png`:

```bash
mv frontend/assets/image.png frontend/assets/favicon.png
```

Update HTML:

```html
<link rel="icon" type="image/png" href="./assets/favicon.png">
```

### Method 2: Create favicon.ico

Create `favicon.ico` using online tools:

1. [Favicon Generator](https://www.favicon-generator.org/)
2. Upload `image.png`
3. Download `favicon.ico`
4. Place in `frontend/assets/`

Add to HTML:

```html
<link rel="icon" href="./assets/favicon.ico">
```

### Method 3: Verify Static File Server Settings

For local development, verify static files are being served correctly:

```bash
# If using Python's http.server
cd frontend
python3 -m http.server 3000
```

### Method 4: Vercel Deployment Verification

When deploying to Vercel, verify `vercel.json` configuration:

```json
{
  "routes": [
    {
      "src": "/assets/(.*)",
      "dest": "/frontend/assets/$1"
    }
  ]
}
```

## Common Issues

### Issue 1: Incorrect Path

❌ Wrong: `href="assets/image.png"`
✅ Correct: `href="./assets/image.png"`

### Issue 2: File Size Too Large

Favicons are typically recommended to be 32x32 or 64x64 pixels.
If using a larger image, resize it.

### Issue 3: Browser Cache

Favicons are heavily cached by browsers.
Try a hard reload.

### Issue 4: Static File Server Configuration

If static files are not being served correctly in local development,
verify server configuration.
