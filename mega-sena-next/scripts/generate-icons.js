const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const sizes = [192, 512];
const iconsDir = path.join(__dirname, '../public/icons');

// Ensure icons directory exists
if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

const svgPath = path.join(iconsDir, 'icon.svg');

async function generateIcons() {
  for (const size of sizes) {
    const outputPath = path.join(iconsDir, `icon-${size}x${size}.png`);
    await sharp(svgPath)
      .resize(size, size)
      .png()
      .toFile(outputPath);
    console.log(`Generated: ${outputPath}`);
  }

  // Generate maskable icon (with padding)
  const maskablePath = path.join(iconsDir, 'icon-maskable.png');
  await sharp(svgPath)
    .resize(512, 512)
    .png()
    .toFile(maskablePath);
  console.log(`Generated: ${maskablePath}`);

  console.log('All icons generated successfully!');
}

generateIcons().catch(console.error);
