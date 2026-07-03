// Chuyển 1 phần tử <svg> đã render trong DOM thành PNG File — dùng chung cho "Vẽ đồ thị" (GĐ3A)
// và "Vẽ bảng biến thiên" (GĐ3B): SVG -> Blob -> Image -> canvas (x2 độ phân giải, nền trắng) -> PNG.
export async function svgSangPngFile(svgEl, tenFile, rong, cao) {
  const xml = new XMLSerializer().serializeToString(svgEl)
  const url = URL.createObjectURL(new Blob([xml], { type: 'image/svg+xml;charset=utf-8' }))
  try {
    const img = new Image()
    await new Promise((resolve, reject) => {
      img.onload = resolve
      img.onerror = () => reject(new Error('Không chuyển được hình sang ảnh'))
      img.src = url
    })
    const canvas = document.createElement('canvas')
    canvas.width = rong * 2
    canvas.height = cao * 2
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'))
    if (!blob) throw new Error('Không tạo được file ảnh')
    return new File([blob], tenFile, { type: 'image/png' })
  } finally {
    URL.revokeObjectURL(url)
  }
}
