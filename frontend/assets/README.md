# Icon Files Setup

Place the following icon files in this directory:

## Required Files

1. **favicon.svg** (Recommended)
   - SVG format favicon
   - Size: Any (scalable)
   - Purpose: Main favicon

2. **favicon-32x32.png**
   - PNG format favicon (32x32 pixels)
   - Purpose: Fallback for browsers that don't support SVG

3. **favicon-16x16.png**
   - PNG format favicon (16x16 pixels)
   - Purpose: Small size version

4. **apple-touch-icon.png**
   - PNG format (180x180 pixels)
   - Purpose: For iOS devices

5. **favicon.ico** (Optional)
   - ICO format (multi-size including 16x16, 32x32, 48x48)
   - Purpose: For older browsers

## How to Create Icon Files

### Method 1: Use Online Tools

1. **RealFaviconGenerator** (Recommended)
   - https://realfavicongenerator.net/
   - Upload an image and automatically generate all sizes

2. **Favicon.io**
   - https://favicon.io/
   - Generate favicon from text or image

3. **Favicon Generator**
   - https://www.favicon-generator.org/
   - Upload an image to generate favicon

### Method 2: Create Manually

1. **Create SVG file**
   - Export as SVG from design tools (Figma, Illustrator, etc.)
   - Or generate SVG using online tools

2. **Create PNG files**
   - Export PNGs of each size from SVG
   - Or resize using image editing software

3. **Create ICO file**
   - Convert to ICO using online tools
   - Or use dedicated software

## Verification After File Placement

1. Hard reload browser (Cmd+Shift+R or Ctrl+Shift+R)
2. Verify that the icon appears in the browser tab
3. Check the Network tab in developer tools (F12) to verify favicon requests are successful
