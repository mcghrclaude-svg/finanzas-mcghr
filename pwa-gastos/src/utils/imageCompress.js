import imageCompression from 'browser-image-compression'

export async function compressPhoto(file) {
  if (!file) return null
  return imageCompression(file, {
    maxWidthOrHeight: 1600,
    initialQuality: 0.75,
    fileType: 'image/jpeg',
    useWebWorker: true,
  })
}
