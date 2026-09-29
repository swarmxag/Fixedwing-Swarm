// convert-image.js
const fs = require('fs');
const path = require('path');

// Map file extensions to MIME types (needed for the data URI prefix)
const MIME_TYPES = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.bmp': 'image/bmp',
};

/**
 * Reads an image file and returns it as a base64 string.
 * @param {string} filePath - path to the image
 * @returns {{ base64: string, dataUri: string }}
 */
function imageToBase64(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const mimeType = MIME_TYPES[ext];

  if (!mimeType) {
    throw new Error(`Unsupported image type: ${ext}`);
  }

  // No encoding passed, so this returns a raw Buffer (binary data)
  const buffer = fs.readFileSync(filePath);

  // Convert the binary buffer into a base64 text string
  const base64 = buffer.toString('base64');

  // Data URI = base64 string plus a prefix that tells browsers what it is
  const dataUri = `data:${mimeType};base64,${base64}`;

  return { base64, dataUri };
}

// --- Example usage ---
const { dataUri } = imageToBase64('D:/Kamikaze-Fuze-GUI/GCS-live/assets/img/logo.png');
console.log(dataUri)
const outputPath = 'D:/Kamikaze-Fuze-GUI/GCS-live/assets/img/logo.txt';
fs.writeFileSync(outputPath, dataUri, 'utf8');

console.log(`Saved data URI (${dataUri.length} characters) to ${outputPath}`);